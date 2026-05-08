"""Cálculo de custos de transporte e estoque com parâmetros injetáveis."""

from __future__ import annotations

import numpy as np

from otimizador.config import SolverSettings
from otimizador.domain.entities import CD, Cliente, Produto


def calcular_distancia_haversine(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Distância em km entre dois pontos geográficos."""
    raio_terra = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(np.radians(lat1))
        * np.cos(np.radians(lat2))
        * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return float(raio_terra * c)


def calcular_custo_transporte(
    cd: CD,
    cliente: Cliente,
    produto: Produto,
    settings: SolverSettings,
) -> float:
    """Custo unitário de transporte (R$ por unidade).

    Inclui custo proporcional à distância + custo fixo de manuseio
    para evitar frete zero quando CD e cliente estão na mesma cidade.
    """
    dist = calcular_distancia_haversine(
        cd.lat, cd.lon, cliente.lat, cliente.lon
    )
    custo_variavel = (
        dist * (produto.peso_kg / 1000.0) * settings.custo_por_km_ton
    )
    return round(custo_variavel + settings.custo_manuseio_fixo_por_unidade, 4)


def calcular_custo_estoque(
    produto: Produto,
    settings: SolverSettings,
) -> float:
    """Custo mensal de estocar uma unidade do produto.

    Composto por:
    - armazenagem proporcional ao peso
    - custo de capital empatado
    - risco de perda por validade
    """
    custo_armazenagem = settings.custo_armazenagem_por_kg * produto.peso_kg

    taxa_mensal = settings.taxa_juros_anual / 12.0
    custo_capital = produto.valor_unitario * taxa_mensal

    if produto.prazo_validade_dias <= 30:
        fator = settings.fator_validade_curta
    elif produto.prazo_validade_dias <= 60:
        fator = settings.fator_validade_media
    else:
        fator = settings.fator_validade_longa
    custo_validade = produto.valor_unitario * fator

    return round(custo_armazenagem + custo_capital + custo_validade, 4)
