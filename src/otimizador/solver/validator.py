"""Validação pré-solver com diagnóstico descritivo."""

from __future__ import annotations

from dataclasses import dataclass

from otimizador.config import SolverSettings
from otimizador.domain.entities import CD, Cliente, Produto
from otimizador.domain.schemas import ScenarioConfig


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Resultado da validação de uma instância."""

    valido: bool
    mensagens: list[str]

    @property
    def ok(self) -> bool:
        return self.valido and not self.mensagens


class ProblemValidator:
    """Valida pré-condições antes de construir o modelo MIP."""

    def __init__(self, settings: SolverSettings | None = None) -> None:
        self.settings = settings or SolverSettings()

    def validate(
        self,
        cds: list[CD],
        clientes: list[Cliente],
        produtos: list[Produto],
        config: ScenarioConfig,
    ) -> ValidationResult:
        """Executa todas as validações e retorna diagnóstico consolidado."""
        mensagens: list[str] = []

        # V1: listas não vazias
        if not cds:
            mensagens.append("ERRO: Lista de CDs está vazia.")
        if not clientes:
            mensagens.append("ERRO: Lista de clientes está vazia.")
        if not produtos:
            mensagens.append("ERRO: Lista de produtos está vazia.")

        if mensagens:
            return ValidationResult(valido=False, mensagens=mensagens)

        # V2: coordenadas dentro do Brasil (aproximado)
        for entidade in (*cds, *clientes):
            if not (self.settings.lat_min <= entidade.lat <= self.settings.lat_max):
                mensagens.append(
                    f"ERRO: {entidade.nome} lat={entidade.lat} fora dos limites brasileiros."
                )
            if not (self.settings.lon_min <= entidade.lon <= self.settings.lon_max):
                mensagens.append(
                    f"ERRO: {entidade.nome} lon={entidade.lon} fora dos limites brasileiros."
                )

        # V3: capacidades e custos positivos
        for cd in cds:
            if cd.capacidade_total <= 0:
                mensagens.append(f"ERRO: {cd.nome} tem capacidade_total <= 0.")
            if cd.custo_fixo_mensal < 0:
                mensagens.append(f"ERRO: {cd.nome} tem custo_fixo_mensal negativo.")
            for pid, cap in cd.cap_produto.items():
                if cap < 0:
                    mensagens.append(
                        f"ERRO: {cd.nome} tem capacidade negativa para produto {pid}."
                    )

        # V4: demanda não negativa
        for cli in clientes:
            for pid, dem in cli.demanda.items():
                if dem < 0:
                    mensagens.append(
                        f"ERRO: {cli.nome} tem demanda negativa para produto {pid}."
                    )

        # V5: capacidade total >= demanda total (condição necessária de viabilidade)
        demanda_total = sum(c.demanda_total() for c in clientes)

        cds_disponiveis = set(range(len(cds)))
        if config.max_cds is not None and config.max_cds < len(cds):
            # Ordenar CDs por capacidade decrescente e pegar os top max_cds
            ordenados = sorted(
                range(len(cds)), key=lambda i: cds[i].capacidade_total, reverse=True
            )
            cds_disponiveis = set(ordenados[: config.max_cds])

        cap_disponivel = sum(cds[i].capacidade_total for i in cds_disponiveis)
        if cap_disponivel < demanda_total:
            mensagens.append(
                f"ERRO: Capacidade disponível ({cap_disponivel:,}) "
                f"é menor que demanda total ({demanda_total:,}). "
                f"Aumente max_cds ou remova restrições."
            )

        # V6: cada produto tem demanda e pelo menos um CD com capacidade > 0
        for p in produtos:
            dem_p = sum(c.demanda_para(p.id) for c in clientes)
            if dem_p > 0:
                cap_p = sum(cd.capacidade_para(p.id) for cd in cds)
                if cap_p < dem_p:
                    mensagens.append(
                        f"ERRO: Produto {p.nome} tem demanda {dem_p:,} "
                        f"mas capacidade total {cap_p:,}."
                    )

        # V7: max_cds consistente
        if config.max_cds is not None and config.max_cds > len(cds):
            mensagens.append(
                f"AVISO: max_cds ({config.max_cds}) maior que número de CDs ({len(cds)})."
            )

        valido = not any(m.startswith("ERRO:") for m in mensagens)
        return ValidationResult(valido=valido, mensagens=mensagens)
