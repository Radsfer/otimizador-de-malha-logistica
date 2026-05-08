"""Gera dataset no padrão Olist (e-commerce brasileiro) para o otimizador.

O dataset original Olist (disponível em https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
contém ~100k pedidos de e-commerce com:
- sellers em diferentes cidades brasileiras
- customers em todo o Brasil
- produtos com categorias e pesos

Este script gera dados sintéticos *estatisticamente consistentes* com o padrão Olist,
mas prontos para consumo pelo otimizador.

Para usar o dataset real:
1. Baixe de https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Extraia lat/lon dos zip codes usando geopy + coordenadas do IBGE
3. Agregue pedidos por seller-customer-product_category
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# Cidades com maior concentração de sellers no Olist (Sudeste dominante)
SELLER_CITIES = [
    ("São Paulo", -23.5505, -46.6333, 0.35),
    ("Curitiba", -25.4290, -49.2671, 0.12),
    ("Rio de Janeiro", -22.9068, -43.1729, 0.10),
    ("Belo Horizonte", -19.9167, -43.9345, 0.08),
    ("Porto Alegre", -30.0346, -51.2177, 0.07),
    ("Campinas", -22.9053, -47.0659, 0.06),
    ("Santos", -23.9608, -46.3331, 0.05),
    ("São José dos Campos", -23.2237, -45.9009, 0.04),
    ("Florianópolis", -27.5954, -48.5480, 0.04),
    ("Vitória", -20.3155, -40.3128, 0.03),
    ("Salvador", -12.9714, -38.5014, 0.03),
    ("Brasília", -15.7975, -47.8919, 0.02),
    ("Goiânia", -16.6869, -49.2648, 0.01),
]

# Cidades de customers (mais espalhadas, proporção aproximada ao PIB/População)
CUSTOMER_CITIES = [
    # Sudeste (55%)
    ("São Paulo", -23.5505, -46.6333, 0.22),
    ("Rio de Janeiro", -22.9068, -43.1729, 0.12),
    ("Belo Horizonte", -19.9167, -43.9345, 0.08),
    ("Campinas", -22.9053, -47.0659, 0.04),
    ("Santos", -23.9608, -46.3331, 0.03),
    ("Sorocaba", -23.5015, -47.4526, 0.02),
    ("Niterói", -22.8833, -43.1034, 0.02),
    ("São José dos Campos", -23.2237, -45.9009, 0.02),
    # Sul (18%)
    ("Curitiba", -25.4290, -49.2671, 0.07),
    ("Porto Alegre", -30.0346, -51.2177, 0.05),
    ("Florianópolis", -27.5954, -48.5480, 0.03),
    ("Londrina", -23.3045, -51.1696, 0.02),
    ("Caxias do Sul", -29.1678, -51.1794, 0.01),
    # Nordeste (15%)
    ("Salvador", -12.9714, -38.5014, 0.05),
    ("Fortaleza", -3.7172, -38.5433, 0.04),
    ("Recife", -8.0476, -34.8770, 0.03),
    ("Feira de Santana", -12.2664, -38.9663, 0.02),
    ("Caucaia", -3.7333, -38.6533, 0.01),
    # Centro-Oeste (10%)
    ("Brasília", -15.7975, -47.8919, 0.05),
    ("Goiânia", -16.6869, -49.2648,0.03),
    ("Anápolis", -16.3267, -48.9525, 0.02),
    # Norte (2%)
    ("Manaus", -3.1190, -60.0217, 0.02),
]

# Categorias de produto (padrão Olist)
CATEGORIES = [
    ("P01", "eletronicos", 1.5, 250.0, 365, "A"),
    ("P02", "moveis_decoracao", 8.0, 180.0, 730, "B"),
    ("P03", "beleza_saude", 0.8, 45.0, 1095, "A"),
    ("P04", "esporte_lazer", 2.5, 120.0, 730, "B"),
    ("P05", "utilidades_domesticas", 3.0, 65.0, 1095, "A"),
    ("P06", "brinquedos", 1.2, 80.0, 730, "B"),
    ("P07", "ferramentas", 4.0, 150.0, 1095, "C"),
    ("P08", "papelaria", 0.5, 25.0, 730, "C"),
]


def _escolher_cidade(cidades, rng):
    nomes = [c[0] for c in cidades]
    probs = np.array([c[3] for c in cidades])
    probs = probs / probs.sum()
    idx = rng.choice(len(cidades), p=probs)
    return nomes[idx], cidades[idx][1], cidades[idx][2]


def generate_olist_synthetic(
    n_sellers: int = 15,
    n_customers: int = 40,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Gera 3 DataFrames no formato do otimizador, inspirados no Olist.

    Args:
        n_sellers: Número de sellers (CDs candidatos).
        n_customers: Número de customers.
        seed: Semente para reprodutibilidade.

    Returns:
        (df_cds, df_clientes, df_produtos) prontos para DataLoader.from_csvs.
    """
    rng = np.random.default_rng(seed)

    # ---- Produtos ----
    produtos_data = []
    for cat_id, cat_nome, peso_base, valor_base, validade, giro in CATEGORIES:
        produtos_data.append({
            "id": cat_id,
            "nome": cat_nome.replace("_", " ").title(),
            "peso_kg": round(peso_base * rng.uniform(0.8, 1.2), 2),
            "valor_unitario": round(valor_base * rng.uniform(0.85, 1.15), 2),
            "prazo_validade_dias": validade,
            "giro_classificacao": giro,
        })
    df_produtos = pd.DataFrame(produtos_data)
    prod_ids = df_produtos["id"].tolist()

    # ---- Sellers (CDs) ----
    seller_data = []
    for i in range(n_sellers):
        cidade, lat, lon = _escolher_cidade(SELLER_CITIES, rng)
        # Capacidade baseada no "tamanho" da cidade (proxy pelo peso na lista)
        city_weight = next(c[3] for c in SELLER_CITIES if c[0] == cidade)
        cap_total = int(rng.integers(8000, 25000) * (0.5 + city_weight))
        custo_fixo = int(cap_total * rng.uniform(3.5, 5.5))

        row = {
            "id": f"CD_{i+1:03d}",
            "nome": f"CD {cidade} {i+1}",
            "cidade": cidade,
            "lat": round(lat + rng.normal(0, 0.05), 4),
            "lon": round(lon + rng.normal(0, 0.05), 4),
            "capacidade_total": cap_total,
            "custo_fixo_mensal": custo_fixo,
        }
        for pid in prod_ids:
            row[f"cap_{pid}"] = int(cap_total * rng.uniform(0.08, 0.18))
        seller_data.append(row)
    df_cds = pd.DataFrame(seller_data)

    # ---- Customers ----
    customer_data = []
    for i in range(n_customers):
        cidade, lat, lon = _escolher_cidade(CUSTOMER_CITIES, rng)
        # Demanda base proporcional ao "tamanho" da cidade
        city_weight = next(c[3] for c in CUSTOMER_CITIES if c[0] == cidade)
        demanda_base = int(rng.integers(300, 1200) * (0.3 + city_weight * 2))

        row = {
            "id": f"CLI_{i+1:03d}",
            "nome": f"Cliente {cidade} {i+1}",
            "cidade": cidade,
            "lat": round(lat + rng.normal(0, 0.03), 4),
            "lon": round(lon + rng.normal(0, 0.03), 4),
        }
        for pid, _, _, _, _, giro in CATEGORIES:
            if giro == "A":
                fator = rng.uniform(0.8, 1.5)
            elif giro == "B":
                fator = rng.uniform(0.4, 0.9)
            else:
                fator = rng.uniform(0.15, 0.4)
            row[f"demanda_{pid}"] = max(5, int(demanda_base * fator * rng.uniform(0.7, 1.3)))
        customer_data.append(row)
    df_clientes = pd.DataFrame(customer_data)

    return df_cds, df_clientes, df_produtos


def main():
    parser = argparse.ArgumentParser(description="Gera dataset Olist-like para o otimizador")
    parser.add_argument("--sellers", type=int, default=15, help="Número de sellers/CDs")
    parser.add_argument("--customers", type=int, default=40, help="Número de customers")
    parser.add_argument("--seed", type=int, default=42, help="Semente aleatória")
    parser.add_argument("--output-dir", type=str, default="data_olist", help="Diretório de saída")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df_cds, df_clientes, df_produtos = generate_olist_synthetic(
        n_sellers=args.sellers,
        n_customers=args.customers,
        seed=args.seed,
    )

    df_cds.to_csv(out_dir / "cds.csv", index=False)
    df_clientes.to_csv(out_dir / "clientes.csv", index=False)
    df_produtos.to_csv(out_dir / "produtos.csv", index=False)

    print(f"Dataset gerado em: {out_dir.resolve()}")
    print(f"  CDs:      {len(df_cds)}")
    print(f"  Clientes: {len(df_clientes)}")
    print(f"  Produtos: {len(df_produtos)}")
    print()
    print("Para usar no otimizador:")
    print(f'  python scripts/run_with_real_data.py --cds {out_dir}/cds.csv --clientes {out_dir}/clientes.csv --produtos {out_dir}/produtos.csv')


if __name__ == "__main__":
    main()
