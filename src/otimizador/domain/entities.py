"""Entidades de domínio do problema de otimização logística."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Produto:
    """Produto / SKU distribuído pela rede."""

    id: str
    nome: str
    peso_kg: float
    valor_unitario: float
    prazo_validade_dias: int
    giro_classificacao: str  # 'A', 'B', 'C'


@dataclass(frozen=True, slots=True)
class CD:
    """Centro de Distribuição candidato."""

    id: str
    nome: str
    cidade: str
    lat: float
    lon: float
    capacidade_total: int          # unidades/mês
    custo_fixo_mensal: float       # R$
    cap_produto: dict[str, int]    # capacidade por produto_id

    def capacidade_para(self, produto_id: str) -> int:
        """Retorna capacidade de armazenamento para um produto específico."""
        return self.cap_produto.get(produto_id, 0)


@dataclass(frozen=True, slots=True)
class Cliente:
    """Cliente / mercado consumidor."""

    id: str
    nome: str
    cidade: str
    lat: float
    lon: float
    demanda: dict[str, int]        # produto_id -> unidades/mês

    def demanda_para(self, produto_id: str) -> int:
        """Retorna demanda por um produto específico."""
        return self.demanda.get(produto_id, 0)

    def demanda_total(self) -> int:
        """Soma da demanda across all produtos."""
        return sum(self.demanda.values())
