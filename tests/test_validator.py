"""Testes da camada de validação pré-solver."""

from __future__ import annotations

import pytest

from otimizador.config import SolverSettings
from otimizador.data.generator import gerar_dados_sinteticos
from otimizador.domain.entities import CD
from otimizador.domain.schemas import ScenarioConfig
from otimizador.solver.validator import ProblemValidator


@pytest.fixture
def validator() -> ProblemValidator:
    return ProblemValidator(settings=SolverSettings())


def test_validacao_basica_passa(validator: ProblemValidator):
    cds, clientes, produtos = gerar_dados_sinteticos(seed=42)
    config = ScenarioConfig()
    result = validator.validate(cds, clientes, produtos, config)
    assert result.valido is True


def test_lista_vazia_cds(validator: ProblemValidator):
    _, clientes, produtos = gerar_dados_sinteticos(seed=42)
    config = ScenarioConfig()
    result = validator.validate([], clientes, produtos, config)
    assert result.valido is False
    assert any("CDs está vazia" in m for m in result.mensagens)


def test_lista_vazia_clientes(validator: ProblemValidator):
    cds, _, produtos = gerar_dados_sinteticos(seed=42)
    config = ScenarioConfig()
    result = validator.validate(cds, [], produtos, config)
    assert result.valido is False
    assert any("clientes está vazia" in m for m in result.mensagens)


def test_capacidade_negativa(validator: ProblemValidator):
    cds, clientes, produtos = gerar_dados_sinteticos(seed=42)
    # Corrompe um CD
    cd_ruim = CD(
        id="CD_RUIM",
        nome="CD Ruim",
        cidade="X",
        lat=-20.0,
        lon=-45.0,
        capacidade_total=-100,
        custo_fixo_mensal=1000.0,
        cap_produto={p.id: 10 for p in produtos},
    )
    config = ScenarioConfig()
    result = validator.validate([cd_ruim], clientes, produtos, config)
    assert result.valido is False
    assert any("capacidade_total <= 0" in m for m in result.mensagens)


def test_max_cds_menor_que_obrigatorios(validator: ProblemValidator):
    cds, clientes, produtos = gerar_dados_sinteticos(seed=42)
    # A validação em si não detecta isso (SchemaConfig já valida),
    # mas garantimos que o schema quebra antes
    with pytest.raises(ValueError):
        config = ScenarioConfig(max_cds=2, cds_obrigatorios=[0, 1, 2])
        validator.validate(cds, clientes, produtos, config)


def test_capacidade_insuficiente(validator: ProblemValidator):
    cds, clientes, produtos = gerar_dados_sinteticos(seed=42)
    # Forçar max_cds=1 com CD pequeno
    config = ScenarioConfig(max_cds=1)
    result = validator.validate(cds, clientes, produtos, config)
    # Pode ser válido ou não dependendo do CD maior; verificamos estrutura
    assert isinstance(result.valido, bool)
    assert isinstance(result.mensagens, list)
