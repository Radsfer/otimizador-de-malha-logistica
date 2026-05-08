"""Interface para carregar instâncias de dados de diferentes fontes."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from otimizador.domain.entities import CD, Cliente, Produto


class DataSource(Protocol):
    """Protocolo para fontes de dados do otimizador."""

    def load(
        self,
    ) -> tuple[list[CD], list[Cliente], list[Produto]]:
        """Carrega e retorna a instância completa."""
        ...


class DataLoader:
    """Carrega instâncias a partir de arquivos CSV ou DataFrames."""

    @staticmethod
    def from_csvs(
        path_cds: str | Path,
        path_clientes: str | Path,
        path_produtos: str | Path,
    ) -> tuple[list[CD], list[Cliente], list[Produto]]:
        """Carrega instância a partir de arquivos CSV.

        Args:
            path_cds: CSV com colunas obrigatórias:
                id, nome, cidade, lat, lon, capacidade_total, custo_fixo_mensal.
                Colunas adicionais cap_<produto_id> definem capacidade por produto.
            path_clientes: CSV com colunas obrigatórias:
                id, nome, cidade, lat, lon.
                Colunas adicionais demanda_<produto_id> definem demanda por produto.
            path_produtos: CSV com colunas:
                id, nome, peso_kg, valor_unitario, prazo_validade_dias, giro_classificacao.
        """
        df_produtos = pd.read_csv(path_produtos)
        produtos = [
            Produto(
                id=str(row["id"]),
                nome=str(row["nome"]),
                peso_kg=float(row["peso_kg"]),
                valor_unitario=float(row["valor_unitario"]),
                prazo_validade_dias=int(row["prazo_validade_dias"]),
                giro_classificacao=str(row["giro_classificacao"]),
            )
            for _, row in df_produtos.iterrows()
        ]
        produto_ids = {p.id for p in produtos}

        df_cds = pd.read_csv(path_cds)
        cds: list[CD] = []
        for _, row in df_cds.iterrows():
            cap_produto = {
                col.replace("cap_", ""): int(row[col])
                for col in df_cds.columns
                if col.startswith("cap_") and col.replace("cap_", "") in produto_ids
            }
            cds.append(
                CD(
                    id=str(row["id"]),
                    nome=str(row["nome"]),
                    cidade=str(row["cidade"]),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    capacidade_total=int(row["capacidade_total"]),
                    custo_fixo_mensal=float(row["custo_fixo_mensal"]),
                    cap_produto=cap_produto,
                )
            )

        df_clientes = pd.read_csv(path_clientes)
        clientes: list[Cliente] = []
        for _, row in df_clientes.iterrows():
            demanda = {
                col.replace("demanda_", ""): int(row[col])
                for col in df_clientes.columns
                if col.startswith("demanda_")
                and col.replace("demanda_", "") in produto_ids
            }
            clientes.append(
                Cliente(
                    id=str(row["id"]),
                    nome=str(row["nome"]),
                    cidade=str(row["cidade"]),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    demanda=demanda,
                )
            )

        return cds, clientes, produtos
