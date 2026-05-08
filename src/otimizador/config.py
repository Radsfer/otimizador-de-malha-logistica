"""Configurações centralizadas e injetáveis do otimizador."""

from pydantic import Field
from pydantic_settings import BaseSettings


class SolverSettings(BaseSettings):
    """Parâmetros configuráveis do modelo e solver.

    Todos os valores podem ser sobrescritos via variáveis de ambiente
    (prefixo OTIMIZADOR_) ou passados diretamente no construtor.
    """

    # Solver
    tempo_limite_padrao_segundos: int = Field(default=120, ge=1, le=3600)
    solver_engine: str = Field(default="CBC")
    tolerancia_inteira: float = Field(default=0.5, ge=0.0, le=1.0)

    # Transporte
    custo_por_km_ton: float = Field(default=0.85, gt=0.0)
    custo_manuseio_fixo_por_unidade: float = Field(
        default=0.10,
        ge=0.0,
        description="Custo mínimo de manuseio por unidade enviada, evita frete zero quando distância ≈ 0",
    )

    # Estoque
    taxa_juros_anual: float = Field(default=0.12, gt=0.0)
    custo_armazenagem_por_kg: float = Field(default=0.15, ge=0.0)
    estoque_seguranca_pct: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Percentual do fluxo movimentado mantido como estoque de segurança",
    )

    # Perda por validade
    fator_validade_curta: float = Field(default=0.08, ge=0.0)   # ≤ 30 dias
    fator_validade_media: float = Field(default=0.04, ge=0.0)   # ≤ 60 dias
    fator_validade_longa: float = Field(default=0.01, ge=0.0)   # > 60 dias

    # Limites geográficos (Brasil aproximado)
    lat_min: float = Field(default=-34.0)
    lat_max: float = Field(default=5.5)
    lon_min: float = Field(default=-74.0)
    lon_max: float = Field(default=-34.0)

    class Config:
        env_prefix = "OTIMIZADOR_"
        extra = "ignore"
