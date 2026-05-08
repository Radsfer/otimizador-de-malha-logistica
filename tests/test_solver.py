"""Testes de integração do solver MIP."""

from __future__ import annotations

from otimizador.domain.schemas import ScenarioConfig, SolverInput
from otimizador.solver import LogisticsSolver


def test_solve_livre_retorna_otimo_ou_viavel(
    solver: LogisticsSolver,
    input_free: SolverInput,
):
    result = solver.solve(input_free)
    assert result.status in ("OPTIMO", "VIAVEL")
    assert result.custo_total >= 0
    assert len(result.cds_abertos) >= 1


def test_solve_todos_abertos(
    solver: LogisticsSolver,
    input_all_open: SolverInput,
):
    result = solver.solve(input_all_open)
    assert result.status in ("OPTIMO", "VIAVEL")
    cds_total = len(input_all_open.cds)
    assert len(result.cds_abertos) == cds_total


def test_custo_consistencia(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    soma = result.custo_fixo + result.custo_transporte + result.custo_estoque
    assert abs(result.custo_total - soma) <= 1.0


def test_comparativo_economia(solver: LogisticsSolver, instance_tiny):
    cds, clientes, produtos = instance_tiny

    inp_free = SolverInput(
        cds=cds, clientes=clientes, produtos=produtos,
        config=ScenarioConfig(tempo_limite_segundos=60),
    )
    inp_all = SolverInput(
        cds=cds, clientes=clientes, produtos=produtos,
        config=ScenarioConfig(
            tempo_limite_segundos=60,
            cds_obrigatorios=list(range(len(cds))),
        ),
    )

    r_free = solver.solve(inp_free)
    r_all = solver.solve(inp_all)

    assert r_free.custo_total <= r_all.custo_total
