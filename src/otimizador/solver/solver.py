"""Engine de resolução MIP com logging e controle de execução."""

from __future__ import annotations

import logging

from ortools.linear_solver import pywraplp

from otimizador.config import SolverSettings
from otimizador.domain.schemas import SolverInput, SolverOutput
from otimizador.solver.extract import ResultExtractor
from otimizador.solver.model import MIPModelBuilder
from otimizador.solver.validator import ProblemValidator

logger = logging.getLogger(__name__)


class LogisticsSolver:
    """Fachada que orquestra validação, construção e resolução do MIP."""

    def __init__(self, settings: SolverSettings | None = None) -> None:
        self.settings = settings or SolverSettings()
        self._validator = ProblemValidator(settings=self.settings)

    def solve(
        self,
        input_data: SolverInput,
    ) -> SolverOutput:
        """Resolve a instância e retorna resultado tipado.

        Args:
            input_data: Instância tipada com CDs, clientes, produtos e config.

        Returns:
            SolverOutput com métricas, alocações e estoques.
        """
        cds = input_data.cds
        clientes = input_data.clientes
        produtos = input_data.produtos
        config = input_data.config

        # 1. Validação
        val = self._validator.validate(cds, clientes, produtos, config)
        if not val.valido:
            for msg in val.mensagens:
                logger.error(msg)
            raise ValueError(f"Instância inválida: {'; '.join(val.mensagens)}")
        for msg in val.mensagens:
            logger.warning(msg)

        logger.info(
            "Instância: %d CDs, %d clientes, %d produtos",
            len(cds),
            len(clientes),
            len(produtos),
        )

        # 2. Construção do modelo
        builder = MIPModelBuilder(
            cds=cds,
            clientes=clientes,
            produtos=produtos,
            settings=self.settings,
        )
        model = builder.build(config=config, engine=self.settings.solver_engine)

        logger.info(
            "Modelo construído: %d variáveis, %d restrições",
            model.solver.NumVariables(),
            model.solver.NumConstraints(),
        )

        # 3. Resolução
        status = model.solver.Solve()

        status_map = {
            pywraplp.Solver.OPTIMAL: ("OPTIMO", True),
            pywraplp.Solver.FEASIBLE: ("VIAVEL", True),
        }
        status_name, has_solution = status_map.get(
            status, (f"STATUS_{status}", False)
        )

        logger.info(
            "Solver finalizado: %s | tempo=%dms iter=%d nodes=%d",
            status_name,
            model.solver.wall_time(),
            model.solver.iterations(),
            model.solver.nodes(),
        )

        if not has_solution:
            return SolverOutput(
                status="INVIAVEL",
                status_code=status,
                custo_total=0.0,
                custo_fixo=0.0,
                custo_transporte=0.0,
                custo_estoque=0.0,
                cds_abertos=[],
                alocacoes=[],
                estoques=[],
                utilizacao_cds={},
                demanda_total=sum(c.demanda_total() for c in clientes),
                tempo_solucao_ms=model.solver.wall_time(),
                iteracoes=model.solver.iterations(),
                nos=model.solver.nodes(),
            )

        # 4. Extração tipada
        extractor = ResultExtractor(
            cds=cds,
            clientes=clientes,
            produtos=produtos,
            builder=builder,
        )
        return extractor.extract(model, status_name, status)
