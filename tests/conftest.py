"""Fixtures compartilhadas entre os testes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from otimizador.config import SolverSettings
from otimizador.data.generator import gerar_dados_sinteticos
from otimizador.domain.schemas import ScenarioConfig, SolverInput
from otimizador.solver import LogisticsSolver


@pytest.fixture(scope="session")
def settings() -> SolverSettings:
    return SolverSettings()


@pytest.fixture(scope="session")
def instance_tiny(settings: SolverSettings):
    """Instância mínima e conhecida para testes de integração rápidos."""
    # Usamos a geradora padrão; seed fixo garante reprodutibilidade
    cds, clientes, produtos = gerar_dados_sinteticos(settings=settings, seed=42)
    return cds, clientes, produtos


@pytest.fixture
def solver(settings: SolverSettings) -> LogisticsSolver:
    return LogisticsSolver(settings=settings)


@pytest.fixture
def scenario_free() -> ScenarioConfig:
    return ScenarioConfig(tempo_limite_segundos=60)


@pytest.fixture
def scenario_all_open(instance_tiny) -> ScenarioConfig:
    cds, _, _ = instance_tiny
    return ScenarioConfig(
        tempo_limite_segundos=60,
        cds_obrigatorios=list(range(len(cds))),
    )


@pytest.fixture
def input_free(instance_tiny, scenario_free) -> SolverInput:
    cds, clientes, produtos = instance_tiny
    return SolverInput(cds=cds, clientes=clientes, produtos=produtos, config=scenario_free)


@pytest.fixture
def input_all_open(instance_tiny, scenario_all_open) -> SolverInput:
    cds, clientes, produtos = instance_tiny
    return SolverInput(
        cds=cds, clientes=clientes, produtos=produtos, config=scenario_all_open
    )
