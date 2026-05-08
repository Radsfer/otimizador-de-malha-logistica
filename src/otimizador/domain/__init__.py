"""Camada de domínio: entidades e contratos tipados."""

from .entities import CD, Cliente, Produto
from .schemas import (
    Allocation,
    CDResult,
    ScenarioConfig,
    SolverInput,
    SolverOutput,
    StockLevel,
)

__all__ = [
    "CD",
    "Cliente",
    "Produto",
    "Allocation",
    "CDResult",
    "ScenarioConfig",
    "SolverInput",
    "SolverOutput",
    "StockLevel",
]
