"""Runner manual de testes sem pytest (workaround para Abort trap 6 no macOS)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from otimizador.config import SolverSettings
from otimizador.data.generator import gerar_dados_sinteticos
from otimizador.domain.entities import CD
from otimizador.domain.schemas import ScenarioConfig, SolverInput
from otimizador.solver import LogisticsSolver
from otimizador.solver.validator import ProblemValidator


def _ok(name: str):
    print(f"  [OK] {name}")


def _fail(name: str, exc: Exception):
    print(f"  [FALHA] {name}: {exc}")
    return 1


def run():
    failures = 0
    print("=" * 50)
    print("TESTES DE VALIDAÇÃO")
    print("=" * 50)

    validator = ProblemValidator(settings=SolverSettings())
    cds, clientes, produtos = gerar_dados_sinteticos(seed=42)
    config = ScenarioConfig()

    # test_validacao_basica_passa
    try:
        result = validator.validate(cds, clientes, produtos, config)
        assert result.valido is True
        _ok("validacao_basica_passa")
    except Exception as exc:
        failures += _fail("validacao_basica_passa", exc)

    # test_lista_vazia_cds
    try:
        result = validator.validate([], clientes, produtos, config)
        assert result.valido is False
        assert any("CDs está vazia" in m for m in result.mensagens)
        _ok("lista_vazia_cds")
    except Exception as exc:
        failures += _fail("lista_vazia_cds", exc)

    # test_capacidade_negativa
    try:
        cd_ruim = CD(
            id="CD_RUIM", nome="CD Ruim", cidade="X", lat=-20.0, lon=-45.0,
            capacidade_total=-100, custo_fixo_mensal=1000.0,
            cap_produto={p.id: 10 for p in produtos},
        )
        result = validator.validate([cd_ruim], clientes, produtos, config)
        assert result.valido is False
        assert any("capacidade_total <= 0" in m for m in result.mensagens)
        _ok("capacidade_negativa")
    except Exception as exc:
        failures += _fail("capacidade_negativa", exc)

    print("\n" + "=" * 50)
    print("TESTES DO SOLVER")
    print("=" * 50)

    solver = LogisticsSolver(settings=SolverSettings())
    inp_free = SolverInput(cds=cds, clientes=clientes, produtos=produtos, config=config)

    # test_solve_livre
    try:
        result = solver.solve(inp_free)
        assert result.status in ("OPTIMO", "VIAVEL")
        assert result.custo_total >= 0
        assert len(result.cds_abertos) >= 1
        _ok("solve_livre_retorna_otimo_ou_viavel")
    except Exception as exc:
        failures += _fail("solve_livre_retorna_otimo_ou_viavel", exc)

    # test_custo_consistencia
    try:
        result = solver.solve(inp_free)
        soma = result.custo_fixo + result.custo_transporte + result.custo_estoque
        assert abs(result.custo_total - soma) <= 1.0
        _ok("custo_consistencia")
    except Exception as exc:
        failures += _fail("custo_consistencia", exc)

    # test_demanda_total_atendida
    try:
        result = solver.solve(inp_free)
        demanda_atendida = sum(a.quantidade for a in result.alocacoes)
        assert abs(demanda_atendida - result.demanda_total) <= 1.0
        _ok("demanda_total_atendida")
    except Exception as exc:
        failures += _fail("demanda_total_atendida", exc)

    # test_cds_fechados_nao_alocam
    try:
        result = solver.solve(inp_free)
        abertos_ids = {cd.cd_id for cd in result.cds_abertos}
        for alloc in result.alocacoes:
            assert alloc.cd_id in abertos_ids
        _ok("cds_fechados_nao_alocam")
    except Exception as exc:
        failures += _fail("cds_fechados_nao_alocam", exc)

    # test_comparativo_economia
    try:
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
        _ok("comparativo_economia")
    except Exception as exc:
        failures += _fail("comparativo_economia", exc)

    print("\n" + "=" * 50)
    if failures == 0:
        print("TODOS OS TESTES PASSARAM")
    else:
        print(f"FALHAS: {failures}")
    print("=" * 50)
    return failures


if __name__ == "__main__":
    sys.exit(run())
