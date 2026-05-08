"""Exemplo completo: carrega dados CSV (reais ou Olist-like) e resolve com o otimizador.

Uso:
    python scripts/run_with_real_data.py \
        --cds data_olist/cds.csv \
        --clientes data_olist/clientes.csv \
        --produtos data_olist/produtos.csv \
        --tempo 120 \
        --output resultados_olist.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from otimizador.data.loader import DataLoader
from otimizador.domain.schemas import ScenarioConfig, SolverInput
from otimizador.solver import LogisticsSolver


def main():
    parser = argparse.ArgumentParser(
        description="Roda o otimizador com dados CSV reais"
    )
    parser.add_argument("--cds", required=True, help="CSV de CDs")
    parser.add_argument("--clientes", required=True, help="CSV de clientes")
    parser.add_argument("--produtos", required=True, help="CSV de produtos")
    parser.add_argument("--tempo", type=int, default=120, help="Tempo limite do solver (s)")
    parser.add_argument("--max-cds", type=int, default=None, help="Máximo de CDs abertos")
    parser.add_argument("--output", type=str, default=None, help="Arquivo JSON para exportar resultados")
    parser.add_argument("--verbose", action="store_true", help="Logging detalhado")
    args = parser.parse_args()

    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 60)
    print("OTIMIZADOR COM DADOS REAIS")
    print("=" * 60)

    # 1. Carregar dados
    print("\n[1/4] Carregando dados...")
    cds, clientes, produtos = DataLoader.from_csvs(
        path_cds=args.cds,
        path_clientes=args.clientes,
        path_produtos=args.produtos,
    )
    print(f"  CDs:      {len(cds)}")
    print(f"  Clientes: {len(clientes)}")
    print(f"  Produtos: {len(produtos)}")
    print(f"  Demanda total: {sum(c.demanda_total() for c in clientes):,} un/mês")

    # 2. Configurar cenário
    print("\n[2/4] Configurando cenário...")
    config = ScenarioConfig(
        tempo_limite_segundos=args.tempo,
        max_cds=args.max_cds,
    )
    print(f"  Tempo limite: {config.tempo_limite_segundos}s")
    if config.max_cds:
        print(f"  Máx CDs: {config.max_cds}")

    # 3. Resolver
    print("\n[3/4] Resolvendo modelo MIP...")
    inp = SolverInput(cds=cds, clientes=clientes, produtos=produtos, config=config)
    solver = LogisticsSolver()
    result = solver.solve(inp)

    print(f"\n{'=' * 60}")
    print("RESULTADO")
    print(f"{'=' * 60}")
    print(f"Status:        {result.status}")
    print(f"CDs abertos:   {len(result.cds_abertos)} / {len(cds)}")
    print(f"Custo total:   R$ {result.custo_total:,.2f}")
    print(f"  → Fixo:      R$ {result.custo_fixo:,.2f}")
    print(f"  → Transporte: R$ {result.custo_transporte:,.2f}")
    print(f"  → Estoque:    R$ {result.custo_estoque:,.2f}")
    print(f"Tempo solver:  {result.tempo_solucao_ms}ms")
    print(f"Iterações:     {result.iteracoes}")
    print(f"Nós:           {result.nos}")

    print("\nCDs na solução ótima:")
    for cd in sorted(result.cds_abertos, key=lambda x: -x.utilizacao_pct):
        print(
            f"  [OK] {cd.nome:28s} | Util: {cd.utilizacao_pct:5.1f}% | "
            f"Vol: {cd.volume_total:8,.0f} un | Custo fixo: R$ {cd.custo_fixo:,.0f}"
        )

    # 4. Exportar
    if args.output:
        print(f"\n[4/4] Exportando resultados para {args.output}...")
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "status": result.status,
            "custo_total": result.custo_total,
            "custo_fixo": result.custo_fixo,
            "custo_transporte": result.custo_transporte,
            "custo_estoque": result.custo_estoque,
            "cds_abertos": [cd.model_dump() for cd in result.cds_abertos],
            "alocacoes_top20": [
                a.model_dump()
                for a in sorted(
                    result.alocacoes, key=lambda x: -x.quantidade
                )[:20]
            ],
            "estoques": [e.model_dump() for e in result.estoques],
            "metricas_solver": {
                "tempo_ms": result.tempo_solucao_ms,
                "iteracoes": result.iteracoes,
                "nos": result.nos,
            },
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print("  [OK] Exportado com sucesso")

    print(f"\n{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
