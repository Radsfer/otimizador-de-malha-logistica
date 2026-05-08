"""Extração de resultados do solver OR-Tools para contratos tipados."""

from __future__ import annotations

from otimizador.domain.entities import CD, Cliente, Produto
from otimizador.domain.schemas import (
    Allocation,
    CDResult,
    SolverOutput,
    StockLevel,
)
from otimizador.solver.model import MIPModel, MIPModelBuilder


class ResultExtractor:
    """Converte variáveis de decisão do OR-Tools em objetos de domínio tipados."""

    def __init__(
        self,
        cds: list[CD],
        clientes: list[Cliente],
        produtos: list[Produto],
        builder: MIPModelBuilder,
    ) -> None:
        self.cds = cds
        self.clientes = clientes
        self.produtos = produtos
        self.builder = builder
        self.I = range(len(cds))
        self.J = range(len(clientes))
        self.K = range(len(produtos))

    def extract(
        self,
        model: MIPModel,
        status_name: str,
        status_code: int,
    ) -> SolverOutput:
        """Extrai a solução completa do modelo resolvido."""
        y = model.y
        x = model.x
        s = model.s

        # Custos por categoria — extraídos dos coeficientes * valor da variável
        custo_fixo = sum(
            self.builder._custo_fixo[i]
            for i in self.I
            if y[i].solution_value() > 0.5
        )

        custo_transporte = 0.0
        for i in self.I:
            for j in self.J:
                for k in self.K:
                    val = x[(i, j, k)].solution_value()
                    if val > 0.001:
                        custo_transporte += (
                            self.builder._custo_transporte[(i, j, k)] * val
                        )

        custo_estoque = 0.0
        for i in self.I:
            for k in self.K:
                val = s[(i, k)].solution_value()
                if val > 0.001:
                    custo_estoque += (
                        self.builder._custo_estoque[(i, k)] * val
                    )

        custo_total = model.solver.Objective().Value()
        demanda_total = sum(c.demanda_total() for c in self.clientes)

        # CDs abertos
        cds_abertos: list[CDResult] = []
        utilizacao_cds: dict[str, float] = {}
        for i in self.I:
            if y[i].solution_value() > 0.5:
                cd = self.cds[i]
                total_enviado = sum(
                    x[(i, j, k)].solution_value()
                    for j in self.J
                    for k in self.K
                )
                utilizacao = (
                    total_enviado / cd.capacidade_total * 100
                    if cd.capacidade_total > 0
                    else 0.0
                )
                utilizacao_cds[cd.id] = round(utilizacao, 2)
                cds_abertos.append(
                    CDResult(
                        cd_id=cd.id,
                        nome=cd.nome,
                        cidade=cd.cidade,
                        lat=cd.lat,
                        lon=cd.lon,
                        custo_fixo=cd.custo_fixo_mensal,
                        utilizacao_pct=round(utilizacao, 2),
                        volume_total=round(total_enviado, 0),
                        capacidade=cd.capacidade_total,
                    )
                )

        # Alocações
        alocacoes: list[Allocation] = []
        for i in self.I:
            for j in self.J:
                for k in self.K:
                    val = x[(i, j, k)].solution_value()
                    if val > 0.001:
                        cd = self.cds[i]
                        cli = self.clientes[j]
                        prod = self.produtos[k]
                        alocacoes.append(
                            Allocation(
                                cd_id=cd.id,
                                cd_nome=cd.nome,
                                cd_cidade=cd.cidade,
                                cd_lat=cd.lat,
                                cd_lon=cd.lon,
                                cliente_id=cli.id,
                                cliente_nome=cli.nome,
                                cliente_cidade=cli.cidade,
                                cliente_lat=cli.lat,
                                cliente_lon=cli.lon,
                                produto_id=prod.id,
                                produto_nome=prod.nome,
                                quantidade=round(val, 2),
                                custo_transporte_total=round(
                                    self.builder._custo_transporte[(i, j, k)] * val, 2
                                ),
                            )
                        )

        # Estoques
        estoques: list[StockLevel] = []
        for i in self.I:
            for k in self.K:
                val = s[(i, k)].solution_value()
                if val > 0.001:
                    cd = self.cds[i]
                    prod = self.produtos[k]
                    estoques.append(
                        StockLevel(
                            cd_id=cd.id,
                            cd_nome=cd.nome,
                            produto_id=prod.id,
                            produto_nome=prod.nome,
                            estoque=round(val, 2),
                            custo_estoque_mensal=round(
                                self.builder._custo_estoque[(i, k)] * val, 2
                            ),
                        )
                    )

        return SolverOutput(
            status=status_name,
            status_code=status_code,
            custo_total=custo_total,
            custo_fixo=custo_fixo,
            custo_transporte=custo_transporte,
            custo_estoque=custo_estoque,
            cds_abertos=cds_abertos,
            alocacoes=alocacoes,
            estoques=estoques,
            utilizacao_cds=utilizacao_cds,
            demanda_total=demanda_total,
            tempo_solucao_ms=model.solver.wall_time(),
            iteracoes=model.solver.iterations(),
            nos=model.solver.nodes(),
        )
