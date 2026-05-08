"""Entrypoint CLI: roda cenários comparativos via linha de comando."""

from __future__ import annotations

import argparse
import logging
import sys

from otimizador.data.generator import gerar_dados_sinteticos
from otimizador.domain.schemas import ScenarioConfig, SolverInput
from otimizador.solver import LogisticsSolver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("otimizador.cli")


def run_scenario(
    solver: LogisticsSolver,
    cds,
    clientes,
    produtos,
    config: ScenarioConfig,
    nome: str,
) -> dict:
    """Executa um cenário e retorna resumo."""
    logger.info(
        "\n%s %s %s",
        "=" * 20,
        nome,
        "=" * 20,
    )
    inp = SolverInput(cds=cds, clientes=clientes, produtos=produtos, config=config)
    try:
        r = solver.solve(inp)
    except ValueError as exc:
        logger.error("Cenário %s inviável: %s", nome, exc)
        return {
            "cenário": nome,
            "status": "INVIÁVEL",
            "cds": "—",
            "custo_total": "—",
            "custo_fixo": "—",
            "transporte": "—",
            "estoque": "—",
            "tempo_ms": "—",
        }

    logger.info("Status: %s", r.status)
    logger.info("Custo total: R$ %,.2f", r.custo_total)
    logger.info("  → Fixo:      R$ %,.2f", r.custo_fixo)
    logger.info("  → Transporte: R$ %,.2f", r.custo_transporte)
    logger.info("  → Estoque:    R$ %,.2f", r.custo_estoque)
    logger.info("CDs abertos: %d", len(r.cds_abertos))
    for cd in r.cds_abertos:
        logger.info(
            "  [OK] %s — utilizacao %.1f%% — volume %,.0f un",
            cd.nome,
            cd.utilizacao_pct,
            cd.volume_total,
        )

    return {
        "cenário": nome,
        "status": r.status,
        "cds": len(r.cds_abertos),
        "custo_total": r.custo_total,
        "custo_fixo": r.custo_fixo,
        "transporte": r.custo_transporte,
        "estoque": r.custo_estoque,
        "tempo_ms": r.tempo_solucao_ms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Otimizador de Malha Logística — CLI",
    )
    parser.add_argument(
        "--tempo",
        type=int,
        default=120,
        help="Tempo limite do solver em segundos (default: 120)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente para geração de dados sintéticos (default: 42)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Aumenta verbosidade do logging",
    )
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cds, clientes, produtos = gerar_dados_sinteticos(seed=args.seed)
    solver = LogisticsSolver()

    cenários = [
        (
            "Otimização Livre",
            ScenarioConfig(tempo_limite_segundos=args.tempo),
        ),
        (
            "Máx 6 CDs",
            ScenarioConfig(tempo_limite_segundos=args.tempo, max_cds=6),
        ),
        (
            "Máx 3 CDs",
            ScenarioConfig(tempo_limite_segundos=args.tempo, max_cds=3),
        ),
        (
            "Todos CDs (atual)",
            ScenarioConfig(
                tempo_limite_segundos=args.tempo,
                cds_obrigatorios=list(range(len(cds))),
            ),
        ),
    ]

    resultados = []
    for nome, config in cenários:
        res = run_scenario(solver, cds, clientes, produtos, config, nome)
        resultados.append(res)

    # Comparativo final
    logger.info("\n%s COMPARATIVO %s", "=" * 25, "=" * 25)
    livre = next((r for r in resultados if r["cenário"] == "Otimização Livre"), None)
    atual = next(
        (r for r in resultados if r["cenário"] == "Todos CDs (atual)"), None
    )
    if (
        livre
        and atual
        and livre["status"] != "INVIÁVEL"
        and atual["status"] != "INVIÁVEL"
    ):
        economia = atual["custo_total"] - livre["custo_total"]  # type: ignore[operator]
        pct = economia / atual["custo_total"] * 100  # type: ignore[operator]
        logger.info("Economia mensal:  R$ %,.2f (%.1f%%)", economia, pct)
        logger.info("Economia anual:   R$ %,.2f", economia * 12)
        logger.info(
            "Redução de CDs:   %d → %d",
            atual["cds"],
            livre["cds"],
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
