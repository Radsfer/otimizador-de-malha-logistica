"""Valida um dataset CSV sem executar o solver.

Útil para verificar se os dados estão no formato correto antes de rodar a otimização.
Não depende do OR-Tools — pode rodar em qualquer ambiente.
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd


def validate_csv_structure(df_cds: pd.DataFrame, df_clientes: pd.DataFrame, df_produtos: pd.DataFrame) -> list[str]:
    """Valida estrutura dos CSVs independentemente do conteúdo."""
    erros = []

    required_cd = {"id", "nome", "cidade", "lat", "lon", "capacidade_total", "custo_fixo_mensal"}
    required_cli = {"id", "nome", "cidade", "lat", "lon"}
    required_prod = {"id", "nome", "peso_kg", "valor_unitario", "prazo_validade_dias", "giro_classificacao"}

    missing_cd = required_cd - set(df_cds.columns)
    missing_cli = required_cli - set(df_clientes.columns)
    missing_prod = required_prod - set(df_produtos.columns)

    if missing_cd:
        erros.append(f"CDs: colunas obrigatórias faltando: {missing_cd}")
    if missing_cli:
        erros.append(f"Clientes: colunas obrigatórias faltando: {missing_cli}")
    if missing_prod:
        erros.append(f"Produtos: colunas obrigatórias faltando: {missing_prod}")

    prod_ids = set(df_produtos["id"])
    cap_cols = {c.replace("cap_", "") for c in df_cds.columns if c.startswith("cap_")}
    dem_cols = {c.replace("demanda_", "") for c in df_clientes.columns if c.startswith("demanda_")}

    missing_cap = prod_ids - cap_cols
    missing_dem = prod_ids - dem_cols

    if missing_cap:
        erros.append(f"CDs: faltam colunas cap_* para produtos: {missing_cap}")
    if missing_dem:
        erros.append(f"Clientes: faltam colunas demanda_* para produtos: {missing_dem}")

    return erros


def validate_content(df_cds: pd.DataFrame, df_clientes: pd.DataFrame, df_produtos: pd.DataFrame) -> tuple[bool, list[str]]:
    """Valida conteúdo dos dados."""
    mensagens = []

    # Coordenadas
    for _, row in df_cds.iterrows():
        if not (-34 <= row["lat"] <= 5.5):
            mensagens.append(f"ERRO: CD {row['id']} lat={row['lat']} fora do Brasil")
        if not (-74 <= row["lon"] <= -34):
            mensagens.append(f"ERRO: CD {row['id']} lon={row['lon']} fora do Brasil")
    for _, row in df_clientes.iterrows():
        if not (-34 <= row["lat"] <= 5.5):
            mensagens.append(f"ERRO: Cliente {row['id']} lat={row['lat']} fora do Brasil")
        if not (-74 <= row["lon"] <= -34):
            mensagens.append(f"ERRO: Cliente {row['id']} lon={row['lon']} fora do Brasil")

    # Valores negativos
    for _, row in df_cds.iterrows():
        if row["capacidade_total"] <= 0:
            mensagens.append(f"ERRO: CD {row['id']} capacidade_total <= 0")
        if row["custo_fixo_mensal"] < 0:
            mensagens.append(f"ERRO: CD {row['id']} custo_fixo_mensal negativo")

    # Demanda total vs capacidade total
    dem_cols = [c for c in df_clientes.columns if c.startswith("demanda_")]
    demanda_total = df_clientes[dem_cols].sum().sum()
    capacidade_total = df_cds["capacidade_total"].sum()

    if capacidade_total < demanda_total:
        mensagens.append(
            f"ERRO: Capacidade total ({capacidade_total:,.0f}) menor que demanda total ({demanda_total:,.0f})"
        )

    valido = not any(m.startswith("ERRO:") for m in mensagens)
    return valido, mensagens


def main():
    parser = argparse.ArgumentParser(description="Valida dataset CSV para o otimizador")
    parser.add_argument("--cds", required=True, help="CSV de CDs")
    parser.add_argument("--clientes", required=True, help="CSV de clientes")
    parser.add_argument("--produtos", required=True, help="CSV de produtos")
    args = parser.parse_args()

    print("=" * 60)
    print("VALIDAÇÃO DE DATASET (sem OR-Tools)")
    print("=" * 60)

    print("\n[1/3] Verificando estrutura dos CSVs...")
    df_cds = pd.read_csv(args.cds)
    df_clientes = pd.read_csv(args.clientes)
    df_produtos = pd.read_csv(args.produtos)

    erros_estrutura = validate_csv_structure(df_cds, df_clientes, df_produtos)
    if erros_estrutura:
        for e in erros_estrutura:
            print(f"  [ERRO] {e}")
        return 1
    print("  [OK] Estrutura valida")

    print("\n[2/3] Analisando conteúdo...")
    valido, mensagens = validate_content(df_cds, df_clientes, df_produtos)
    for msg in mensagens:
        prefix = "[ERRO]" if msg.startswith("ERRO") else "[AVISO]"
        print(f"  {prefix} {msg}")

    print("\n[3/3] Resumo da instancia...")
    dem_cols = [c for c in df_clientes.columns if c.startswith("demanda_")]
    demanda_total = df_clientes[dem_cols].sum().sum()
    print(f"  CDs:      {len(df_cds)}")
    print(f"  Clientes: {len(df_clientes)}")
    print(f"  Produtos: {len(df_produtos)}")
    print(f"  Demanda total:    {demanda_total:,.0f} un/mes")
    print(f"  Capacidade total: {df_cds['capacidade_total'].sum():,.0f} un/mes")

    if valido:
        print("\n[OK] Instancia VALIDA para otimizacao")
        print("\nPara otimizar, execute em um ambiente com OR-Tools funcional:")
        print("  python scripts/run_with_real_data.py \\")
        print(f"    --cds {args.cds} \\")
        print(f"    --clientes {args.clientes} \\")
        print(f"    --produtos {args.produtos}")
    else:
        print("\n[ERRO] Instancia INVALIDA — corrija os erros antes de rodar o solver")
        return 1
        print(f"  {prefix} {msg}")

    print("\n[3/3] Resumo da instância...")
    dem_cols = [c for c in df_clientes.columns if c.startswith("demanda_")]
    demanda_total = df_clientes[dem_cols].sum().sum()
    print(f"  CDs:      {len(df_cds)}")
    print(f"  Clientes: {len(df_clientes)}")
    print(f"  Produtos: {len(df_produtos)}")
    print(f"  Demanda total:    {demanda_total:,.0f} un/mês")
    print(f"  Capacidade total: {df_cds['capacidade_total'].sum():,.0f} un/mês")

    if valido:
        print("\n[OK] Instancia VALIDA para otimizacao")
        print("\nPara otimizar, execute em um ambiente com OR-Tools funcional:")
        print("  python scripts/run_with_real_data.py \\")
        print(f"    --cds {args.cds} \\")
        print(f"    --clientes {args.clientes} \\")
        print(f"    --produtos {args.produtos}")
    else:
        print("\n[ERRO] Instancia INVALIDA — corrija os erros antes de rodar o solver")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
