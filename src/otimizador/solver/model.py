"""Construção do modelo MIP com separação clara entre builder e solver."""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.linear_solver import pywraplp

from otimizador.config import SolverSettings
from otimizador.domain.entities import CD, Cliente, Produto
from otimizador.domain.schemas import ScenarioConfig
from otimizador.solver.costs import calcular_custo_estoque, calcular_custo_transporte


@dataclass(frozen=True, slots=True)
class BigMCalculator:
    """Calcula constantes Big-M apertadas por produto."""

    demanda: dict[tuple[int, int], int]  # (j, k) -> demanda
    clientes: list[Cliente]
    produtos: list[Produto]

    def m_para_produto(self, k: int) -> int:
        """Retorna M_ik = demanda total do produto k across all clientes.

        Isso é suficientemente grande para ativar z[i,k] quando há fluxo,
        mas muito mais apertado que um M global.
        """
        return sum(self.demanda[(j, k)] for j in range(len(self.clientes)))


@dataclass
class MIPModel:
    """Container com o solver OR-Tools e todas as variáveis de decisão."""

    solver: pywraplp.Solver
    y: dict[int, pywraplp.Variable] = field(default_factory=dict)          # CD aberto
    z: dict[tuple[int, int], pywraplp.Variable] = field(default_factory=dict)  # CD estoca produto
    x: dict[tuple[int, int, int], pywraplp.Variable] = field(default_factory=dict)  # fluxo
    s: dict[tuple[int, int], pywraplp.Variable] = field(default_factory=dict)  # estoque


class MIPModelBuilder:
    """Constrói o modelo MIP de Facility Location com Estoque Integrado."""

    def __init__(
        self,
        cds: list[CD],
        clientes: list[Cliente],
        produtos: list[Produto],
        settings: SolverSettings | None = None,
    ) -> None:
        self.cds = cds
        self.clientes = clientes
        self.produtos = produtos
        self.settings = settings or SolverSettings()
        self.I = range(len(cds))
        self.J = range(len(clientes))
        self.K = range(len(produtos))

        # Pré-computar parâmetros
        self._custo_transporte: dict[tuple[int, int, int], float] = {}
        self._custo_estoque: dict[tuple[int, int], float] = {}
        self._demanda: dict[tuple[int, int], int] = {}
        self._capacidade_cd: dict[int, int] = {}
        self._capacidade_produto_cd: dict[tuple[int, int], int] = {}
        self._custo_fixo: dict[int, float] = {}

        for i, cd in enumerate(cds):
            self._custo_fixo[i] = cd.custo_fixo_mensal
            self._capacidade_cd[i] = cd.capacidade_total
            for k, p in enumerate(produtos):
                self._capacidade_produto_cd[(i, k)] = cd.capacidade_para(p.id)
                self._custo_estoque[(i, k)] = calcular_custo_estoque(p, self.settings)
            for j, cli in enumerate(clientes):
                for k, p in enumerate(produtos):
                    self._custo_transporte[(i, j, k)] = calcular_custo_transporte(
                        cd, cli, p, self.settings
                    )
                    self._demanda[(j, k)] = cli.demanda_para(p.id)

        self._big_m = BigMCalculator(
            demanda=self._demanda,
            clientes=clientes,
            produtos=produtos,
        )

    def build(
        self,
        config: ScenarioConfig,
        engine: str = "CBC",
    ) -> MIPModel:
        """Constrói e retorna o modelo MIP pronto para resolver."""
        solver = pywraplp.Solver.CreateSolver(engine)
        if not solver:
            raise RuntimeError(f"Não foi possível criar o solver {engine}")

        solver.SetTimeLimit(config.tempo_limite_segundos * 1000)

        model = MIPModel(solver=solver)

        # Variáveis de decisão
        for i in self.I:
            model.y[i] = solver.BoolVar(f"y_{i}")

        for i in self.I:
            for k in self.K:
                model.z[(i, k)] = solver.BoolVar(f"z_{i}_{k}")

        for i in self.I:
            for j in self.J:
                for k in self.K:
                    model.x[(i, j, k)] = solver.NumVar(
                        0, solver.infinity(), f"x_{i}_{j}_{k}"
                    )

        for i in self.I:
            for k in self.K:
                model.s[(i, k)] = solver.NumVar(
                    0, solver.infinity(), f"s_{i}_{k}"
                )

        # Função objetivo
        objective = solver.Objective()
        for i in self.I:
            objective.SetCoefficient(model.y[i], self._custo_fixo[i])

        for key, coef in self._custo_transporte.items():
            i, j, k = key
            objective.SetCoefficient(model.x[key], coef)

        for key, coef in self._custo_estoque.items():
            i, k = key
            objective.SetCoefficient(model.s[key], coef)

        objective.SetMinimization()

        # Restrições
        self._add_demand_constraints(model)
        self._add_capacity_constraints(model)
        self._add_stock_logic_constraints(model)
        self._add_safety_stock_constraints(model)
        self._add_stock_limit_constraints(model)
        self._add_mandatory_cd_constraints(model, config)
        self._add_max_cd_constraints(model, config)

        return model

    def _add_demand_constraints(self, model: MIPModel) -> None:
        """R1: Toda demanda de todo cliente deve ser atendida."""
        for j in self.J:
            for k in self.K:
                ct = model.solver.Constraint(
                    self._demanda[(j, k)],
                    self._demanda[(j, k)],
                    f"demanda_{j}_{k}",
                )
                for i in self.I:
                    ct.SetCoefficient(model.x[(i, j, k)], 1)

    def _add_capacity_constraints(self, model: MIPModel) -> None:
        """R2: Capacidade total do CD (big-M lógico)."""
        for i in self.I:
            ct = model.solver.Constraint(
                -model.solver.infinity(), 0, f"cap_{i}"
            )
            for j in self.J:
                for k in self.K:
                    ct.SetCoefficient(model.x[(i, j, k)], 1)
            ct.SetCoefficient(model.y[i], -self._capacidade_cd[i])

    def _add_stock_logic_constraints(self, model: MIPModel) -> None:
        """R3: z_ik <= y_i (só estoca se CD aberto).

        R4: Se envia produto, deve estar ativado em z (big-M por produto).
        """
        for i in self.I:
            for k in self.K:
                # z <= y
                ct = model.solver.Constraint(
                    -model.solver.infinity(), 0, f"z_le_y_{i}_{k}"
                )
                ct.SetCoefficient(model.z[(i, k)], 1)
                ct.SetCoefficient(model.y[i], -1)

                # sum(x) <= M_ik * z
                big_m = self._big_m.m_para_produto(k)
                ct2 = model.solver.Constraint(
                    -model.solver.infinity(), 0, f"x_le_z_{i}_{k}"
                )
                for j in self.J:
                    ct2.SetCoefficient(model.x[(i, j, k)], 1)
                ct2.SetCoefficient(model.z[(i, k)], -big_m)

    def _add_safety_stock_constraints(self, model: MIPModel) -> None:
        """R5: Estoque de segurança proporcional ao fluxo."""
        pct = self.settings.estoque_seguranca_pct
        for i in self.I:
            for k in self.K:
                ct = model.solver.Constraint(
                    0, model.solver.infinity(), f"est_min_{i}_{k}"
                )
                ct.SetCoefficient(model.s[(i, k)], 1)
                for j in self.J:
                    ct.SetCoefficient(model.x[(i, j, k)], -pct)

    def _add_stock_limit_constraints(self, model: MIPModel) -> None:
        """R6: Limite de estoque por produto (capacidade de armazenagem)."""
        for i in self.I:
            for k in self.K:
                ct = model.solver.Constraint(
                    -model.solver.infinity(), 0, f"est_max_{i}_{k}"
                )
                ct.SetCoefficient(model.s[(i, k)], 1)
                ct.SetCoefficient(
                    model.z[(i, k)], -self._capacidade_produto_cd[(i, k)]
                )

    def _add_mandatory_cd_constraints(
        self, model: MIPModel, config: ScenarioConfig
    ) -> None:
        """R7: CDs obrigatórios devem estar abertos."""
        if config.cds_obrigatorios:
            for i in config.cds_obrigatorios:
                ct = model.solver.Constraint(1, 1, f"obrigatorio_{i}")
                ct.SetCoefficient(model.y[i], 1)

    def _add_max_cd_constraints(
        self, model: MIPModel, config: ScenarioConfig
    ) -> None:
        """R8: Limite máximo de CDs abertos."""
        if config.max_cds is not None:
            ct = model.solver.Constraint(0, config.max_cds, "max_cds")
            for i in self.I:
                ct.SetCoefficient(model.y[i], 1)
