"""Testes de invariantes da solução MIP.

Garantem que o modelo matemático respeita as restrições programadas.
"""

from __future__ import annotations

from otimizador.domain.schemas import SolverInput
from otimizador.solver import LogisticsSolver


def test_demanda_total_atendida(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    demanda_atendida = sum(a.quantidade for a in result.alocacoes)
    assert abs(demanda_atendida - result.demanda_total) <= 1.0


def test_nenhum_cd_excede_capacidade(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    for cd in result.cds_abertos:
        assert cd.utilizacao_pct <= 100.0 + 1e-6


def test_cds_fechados_nao_alocam(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    abertos_ids = {cd.cd_id for cd in result.cds_abertos}
    for alloc in result.alocacoes:
        assert alloc.cd_id in abertos_ids


def test_estoque_nao_negativo(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    for est in result.estoques:
        assert est.estoque >= 0


def test_alocacoes_nao_negativas(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    for alloc in result.alocacoes:
        assert alloc.quantidade >= 0
        assert alloc.custo_transporte_total >= 0


def test_custo_estoque_consistente(solver: LogisticsSolver, input_free: SolverInput):
    result = solver.solve(input_free)
    # O custo total de estoque deve ser a soma dos custos individuais
    soma_individual = sum(e.custo_estoque_mensal for e in result.estoques)
    assert abs(result.custo_estoque - soma_individual) <= 1.0
