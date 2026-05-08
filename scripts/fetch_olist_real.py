"""Baixa o dataset real do Olist via Kaggle API e processa para o formato do otimizador.

Requer:
    1. pip install kaggle python-dotenv
    2. Arquivo .env na raiz do projeto com:
       KAGGLE_USERNAME=seu_username
       KAGGLE_KEY=sua_chave

Uso:
    python scripts/fetch_olist_real.py --output-dir data_kaggle
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Adiciona src/ ao path para usar o DataLoader de validacao
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

# Dicionario de lat/lon das principais cidades do dataset Olist
# Fonte: coordenadas aproximadas dos centros urbanos
CITY_COORDS: dict[str, tuple[float, float]] = {
    "sao paulo": (-23.5505, -46.6333),
    "rio de janeiro": (-22.9068, -43.1729),
    "belo horizonte": (-19.9167, -43.9345),
    "curitiba": (-25.4290, -49.2671),
    "porto alegre": (-30.0346, -51.2177),
    "campinas": (-22.9053, -47.0659),
    "santos": (-23.9608, -46.3331),
    "sao jose dos campos": (-23.2237, -45.9009),
    "florianopolis": (-27.5954, -48.5480),
    "vitoria": (-20.3155, -40.3128),
    "salvador": (-12.9714, -38.5014),
    "fortaleza": (-3.7172, -38.5433),
    "recife": (-8.0476, -34.8770),
    "feira de santana": (-12.2664, -38.9663),
    "caucaia": (-3.7333, -38.6533),
    "brasilia": (-15.7975, -47.8919),
    "goiania": (-16.6869, -49.2648),
    "anapolis": (-16.3267, -48.9525),
    "manaus": (-3.1190, -60.0217),
    "sorocaba": (-23.5015, -47.4526),
    "niteroi": (-22.8833, -43.1034),
    "contagem": (-19.9317, -44.0538),
    "londrina": (-23.3045, -51.1696),
    "caxias do sul": (-29.1678, -51.1794),
    "taguatinga": (-15.8100, -48.0615),
    "jaboatao dos guararapes": (-8.1803, -35.0014),
    "vitoria da conquista": (-14.8615, -40.8443),
    "maringa": (-23.4273, -51.9375),
    "piracicaba": (-22.7343, -47.6481),
    "jundiai": (-23.1857, -46.8978),
    "sao jose do rio preto": (-20.8113, -49.3758),
    "franca": (-20.5390, -47.4010),
    "maua": (-23.6677, -46.4603),
    "diadema": (-23.6858, -46.6225),
    "carapicuiba": (-23.5276, -46.8359),
    "osasco": (-23.5320, -46.7917),
    "guarulhos": (-23.4543, -46.5337),
    "santo andre": (-23.6639, -46.5383),
    "sao bernardo do campo": (-23.6939, -46.5650),
    "sao caetano do sul": (-23.6232, -46.5515),
    "barueri": (-23.5057, -46.8760),
    "taboao da serra": (-23.6261, -46.7917),
    "cotia": (-23.6052, -46.9191),
    "aracaju": (-10.9472, -37.0731),
    "maceio": (-9.6659, -35.7350),
    "joao pessoa": (-7.1150, -34.8641),
    "natal": (-5.7945, -35.2110),
    "teresina": (-5.0892, -42.8016),
    "sao luis": (-2.5297, -44.3028),
    "belem": (-1.4558, -48.4902),
    "macapa": (0.0355, -51.0706),
    "boa vista": (2.8235, -60.6758),
    "palmas": (-10.2491, -48.3243),
    "rio branco": (-9.9754, -67.8243),
    "porto velho": (-8.7608, -63.8999),
    "cuiaba": (-15.6014, -56.0979),
    "campo grande": (-20.4697, -54.6201),
    "foz do iguacu": (-25.5163, -54.5854),
    "joinville": (-26.3044, -48.8464),
    "blumenau": (-26.9196, -49.0663),
    "sao jose": (-27.6142, -48.6372),
    "chapeco": (-27.1004, -52.6152),
    "itajai": (-26.9102, -48.6702),
    "pelotas": (-31.7719, -52.3425),
    "novo hamburgo": (-29.6820, -51.1306),
    "canoas": (-29.9170, -51.1838),
    "santa maria": (-29.6868, -53.8149),
    "passo fundo": (-28.2577, -52.4095),
    "uberlandia": (-18.9186, -48.2772),
    "uberaba": (-19.7472, -47.9311),
    "juiz de fora": (-21.7595, -43.3495),
    "montes claros": (-16.7286, -43.8578),
    "divinopolis": (-20.1389, -44.8838),
    "ribeirao preto": (-21.1699, -47.8099),
    "sao carlos": (-22.0087, -47.8908),
    " presidente prudente": (-22.1256, -51.3889),
    "araraquara": (-21.7845, -48.1780),
    "itu": (-23.2642, -47.2992),
    "indaiatuba": (-23.0904, -47.2181),
    "americana": (-22.7395, -47.3314),
    "limeira": (-22.5649, -47.4017),
    "sumare": (-22.8219, -47.2668),
    "hortolandia": (-22.8583, -47.2200),
    "valinhos": (-22.9705, -46.9953),
    "vinhedo": (-23.0294, -46.9753),
    "louveira": (-23.0863, -46.9506),
    "jundiapeba": (-23.5428, -46.1887),
    "suzano": (-23.5422, -46.3108),
    "mogi das cruzes": (-23.5228, -46.1850),
    "jacarei": (-23.3053, -45.9658),
    "taubate": (-23.0264, -45.5553),
    "pindamonhangaba": (-22.9244, -45.4613),
    "resende": (-22.4685, -44.4467),
    "volta redonda": (-22.5232, -44.1042),
    "barra mansa": (-22.5449, -44.1713),
    "sao goncalo": (-22.8267, -43.0534),
    "duque de caxias": (-22.7856, -43.3112),
    "nova iguacu": (-22.7592, -43.4511),
    "nilopolis": (-22.8075, -43.4139),
    "mesquita": (-22.7827, -43.4277),
    " Belford roxo": (-22.7640, -43.3992),
    "sao joao de meriti": (-22.8030, -43.3721),
    "itaborai": (-22.7445, -42.8581),
    "tangua": (-22.7303, -42.7140),
    "cachoeiras de macacu": (-22.4641, -42.6532),
    "casimiro de abreu": (-22.4806, -42.2044),
    "arroio do sal": (-29.5439, -49.8890),
    "capao da canoa": (-29.7456, -50.0097),
    "torres": (-29.3354, -49.7262),
    "osorio": (-29.8869, -50.2707),
    "tramandai": (-29.9844, -50.1327),
    "imbe": (-29.9754, -50.1270),
    "xangri-la": (-29.8058, -50.0440),
    "cidreira": (-30.1603, -50.1987),
    "balneario pinhal": (-30.2464, -50.2339),
    "terra de areia": (-30.0808, -50.3719),
    "mostardas": (-31.1070, -50.9211),
    "tavares": (-31.2846, -51.0885),
    "sao jose do norte": (-32.0153, -52.0333),
    "rio grande": (-32.0354, -52.0984),
    "capao do leao": (-31.7658, -52.4834),
    "cangucu": (-31.3950, -52.6756),
    "jaguarao": (-32.5608, -53.3758),
    "bage": (-31.3314, -54.1069),
    "dom pedrito": (-30.9828, -54.5057),
    "hulha negra": (-31.4056, -53.3944),
    "candiota": (-31.5527, -53.6737),
    "santana do livramento": (-30.8776, -55.5322),
    "uruguaiana": (-29.7551, -57.0883),
    "alegrete": (-29.7869, -55.7948),
    "quarai": (-30.3879, -56.4521),
    "rosario do sul": (-30.2586, -54.9145),
    "santiago": (-29.1917, -54.8672),
    "jaguari": (-29.4962, -54.6890),
    "sao borja": (-28.6577, -56.0043),
    "itaqui": (-29.1253, -56.5531),
    "sao gabriel": (-30.3363, -54.3199),
    "livramento": (-30.8776, -55.5322),
    "cacapava do sul": (-30.5146, -53.4852),
    "sao sepe": (-30.1607, -53.5647),
    "santa cruz do sul": (-29.7176, -52.4268),
    "lajeado": (-29.4591, -51.9644),
    "estrela": (-29.5003, -51.9660),
    "teutonia": (-29.4483, -51.8064),
    "feliz": (-29.4485, -51.3067),
    "porto feliz": (-29.4485, -51.3067),
    "itupeva": (-23.1531, -47.0578),
    "jarinu": (-23.1014, -46.7286),
    "cabreuva": (-23.3075, -47.1328),
    "salto": (-23.2008, -47.2869),
}


def _normalize_city(city_state: str) -> str:
    """Normaliza nome da cidade do formato Olist 'cidade_estado'."""
    city = city_state.split("_")[0].strip().lower()
    return city


def _get_coords(city_state: str) -> tuple[float, float]:
    """Retorna lat/lon da cidade. Se nao encontrar, usa fallback por estado."""
    city = _normalize_city(city_state)
    if city in CITY_COORDS:
        return CITY_COORDS[city]
    # Fallback: retorna coordenadas de brasilia com perturbacao para evitar colisao
    return (-15.7975 + np.random.normal(0, 0.5), -47.8919 + np.random.normal(0, 0.5))


def download_olist_dataset(output_dir: Path) -> Path:
    """Baixa o dataset Olist via Kaggle API."""
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    dataset_dir = output_dir / "raw"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print("Baixando dataset olistbr/brazilian-ecommerce...")
    api.dataset_download_files(
        "olistbr/brazilian-ecommerce",
        path=str(dataset_dir),
        unzip=True,
    )
    print(f"Dataset extraido em: {dataset_dir}")
    return dataset_dir


def process_olist_to_optimizer_format(
    raw_dir: Path,
    output_dir: Path,
    min_orders_per_seller: int = 10,
    top_seller_cities: int = 15,
    top_customer_cities: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Processa CSVs brutos do Olist para o formato do otimizador.

    Estrategia:
    1. Agrupa sellers por cidade -> CDs candidatos
    2. Agrupa customers por cidade -> mercados de demanda
    3. Usa categorias de produto como SKUs (8 categorias principais)
    4. Demanda = soma de order_items por customer_city x seller_city x categoria
    """
    print("\n[1/6] Carregando CSVs brutos...")

    sellers = pd.read_csv(raw_dir / "olist_sellers_dataset.csv")
    customers = pd.read_csv(raw_dir / "olist_customers_dataset.csv")
    orders = pd.read_csv(raw_dir / "olist_orders_dataset.csv")
    items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
    products = pd.read_csv(raw_dir / "olist_products_dataset.csv")

    print(f"  Sellers: {len(sellers)}")
    print(f"  Customers: {len(customers)}")
    print(f"  Orders: {len(orders)}")
    print(f"  Items: {len(items)}")
    print(f"  Products: {len(products)}")

    # --- Merge para enriquecer items ---
    print("\n[2/6] Enriquecendo dados...")
    items_products = items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    orders_items = orders.merge(items_products, on="order_id", how="inner")
    orders_items = orders_items.merge(
        customers[["customer_id", "customer_city"]],
        on="customer_id",
        how="left",
    )
    orders_items = orders_items.merge(
        sellers[["seller_id", "seller_city"]],
        on="seller_id",
        how="left",
    )

    # Filtrar pedidos entregues
    orders_items = orders_items[orders_items["order_status"] == "delivered"]

    # --- Mapear categorias para SKU padrao ---
    print("\n[3/6] Mapeando categorias para SKUs...")

    # Top 8 categorias por volume
    top_cats = (
        orders_items["product_category_name"]
        .value_counts()
        .head(8)
        .index.tolist()
    )
    print(f"  Top categorias: {top_cats}")

    cat_mapping = {cat: f"P{i+1:02d}" for i, cat in enumerate(top_cats)}
    orders_items["sku"] = orders_items["product_category_name"].map(cat_mapping)
    orders_items = orders_items.dropna(subset=["sku"])

    # --- Definir CDs (sellers agrupados por cidade) ---
    print("\n[4/6] Definindo CDs...")
    seller_city_counts = orders_items["seller_city"].value_counts()
    top_seller_cities_list = seller_city_counts.head(top_seller_cities).index.tolist()
    print(f"  Top {top_seller_cities} cidades de seller: {top_seller_cities_list}")

    # --- Definir clientes (customers agrupados por cidade) ---
    print("\n[5/6] Definindo clientes...")
    customer_city_counts = orders_items["customer_city"].value_counts()
    top_customer_cities_list = customer_city_counts.head(top_customer_cities).index.tolist()
    print(f"  Top {top_customer_cities} cidades de customer: {top_customer_cities_list}")

    # --- Agregar demanda ---
    print("\n[6/6] Agregando demanda...")
    demand_agg = (
        orders_items.groupby(["customer_city", "seller_city", "sku"])["order_item_id"]
        .count()
        .reset_index(name="demanda")
    )

    # Filtrar apenas cidades selecionadas
    demand_agg = demand_agg[
        demand_agg["seller_city"].isin(top_seller_cities_list) &
        demand_agg["customer_city"].isin(top_customer_cities_list)
    ]

    # --- Construir DataFrames do otimizador ---

    # Produtos
    sku_info = {
        "P01": ("eletronicos", 1.5, 250.0, 365, "A"),
        "P02": ("moveis_decoracao", 8.0, 180.0, 730, "B"),
        "P03": ("beleza_saude", 0.8, 45.0, 1095, "A"),
        "P04": ("esporte_lazer", 2.5, 120.0, 730, "B"),
        "P05": ("utilidades_domesticas", 3.0, 65.0, 1095, "A"),
        "P06": ("brinquedos", 1.2, 80.0, 730, "B"),
        "P07": ("ferramentas", 4.0, 150.0, 1095, "C"),
        "P08": ("papelaria", 0.5, 25.0, 730, "C"),
    }

    df_produtos = pd.DataFrame([
        {
            "id": sku,
            "nome": info[0].replace("_", " ").title(),
            "peso_kg": info[1],
            "valor_unitario": info[2],
            "prazo_validade_dias": info[3],
            "giro_classificacao": info[4],
        }
        for sku, info in sku_info.items()
        if sku in demand_agg["sku"].unique()
    ])

    # CDs
    cd_data = []
    for i, city in enumerate(top_seller_cities_list):
        lat, lon = _get_coords(city)
        total_demand_from_city = demand_agg[demand_agg["seller_city"] == city]["demanda"].sum()
        # Capacidade proporcional a demanda historica + folga
        cap_total = max(int(total_demand_from_city * 1.5), 5000)
        custo_fixo = int(cap_total * np.random.uniform(3.5, 5.5))

        row = {
            "id": f"CD_{i+1:03d}",
            "nome": f"CD {city.title()}",
            "cidade": city.title(),
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "capacidade_total": cap_total,
            "custo_fixo_mensal": custo_fixo,
        }
        for sku in df_produtos["id"]:
            cap = int(cap_total * np.random.uniform(0.08, 0.18))
            row[f"cap_{sku}"] = cap
        cd_data.append(row)
    df_cds = pd.DataFrame(cd_data)

    # Clientes
    cliente_data = []
    for i, city in enumerate(top_customer_cities_list):
        lat, lon = _get_coords(city)
        row = {
            "id": f"CLI_{i+1:03d}",
            "nome": f"Cliente {city.title()}",
            "cidade": city.title(),
            "lat": round(lat, 4),
            "lon": round(lon, 4),
        }
        for sku in df_produtos["id"]:
            dem = demand_agg[
                (demand_agg["customer_city"] == city) &
                (demand_agg["sku"] == sku)
            ]["demanda"].sum()
            row[f"demanda_{sku}"] = int(dem) if dem > 0 else 0
        cliente_data.append(row)
    df_clientes = pd.DataFrame(cliente_data)

    return df_cds, df_clientes, df_produtos


def main():
    parser = argparse.ArgumentParser(description="Baixa e processa dataset Olist real")
    parser.add_argument("--output-dir", type=str, default="data_kaggle", help="Diretorio de saida")
    parser.add_argument("--skip-download", action="store_true", help="Pula download se ja existir")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Verificar credenciais
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if not username or not key:
        print("ERRO: KAGGLE_USERNAME e KAGGLE_KEY nao encontrados.")
        print("Crie um arquivo .env na raiz do projeto com:")
        print("  KAGGLE_USERNAME=seu_username")
        print("  KAGGLE_KEY=sua_chave")
        return 1

    # Download
    raw_dir = output_dir / "raw"
    if not args.skip_download or not raw_dir.exists():
        try:
            raw_dir = download_olist_dataset(output_dir)
        except Exception as exc:
            print(f"ERRO ao baixar dataset: {exc}")
            print("Possiveis causas:")
            print("  - Credenciais invalidas")
            print("  - Sem conexao com internet")
            print("  - API do Kaggle indisponivel")
            return 1
    else:
        print(f"Usando dados existentes em: {raw_dir}")

    # Processamento
    print("\n" + "=" * 60)
    print("PROCESSANDO DADOS")
    print("=" * 60)
    df_cds, df_clientes, df_produtos = process_olist_to_optimizer_format(
        raw_dir=raw_dir,
        output_dir=output_dir,
    )

    # Salvar
    df_cds.to_csv(output_dir / "cds.csv", index=False)
    df_clientes.to_csv(output_dir / "clientes.csv", index=False)
    df_produtos.to_csv(output_dir / "produtos.csv", index=False)

    print("\n" + "=" * 60)
    print("DATASET PROCESSADO")
    print("=" * 60)
    print(f"  CDs:      {len(df_cds)}")
    print(f"  Clientes: {len(df_clientes)}")
    print(f"  Produtos: {len(df_produtos)}")
    print(f"\nArquivos salvos em: {output_dir}")
    print("\nPara validar:")
    print("  python scripts/validate_dataset.py \\")
    print(f"    --cds {output_dir}/cds.csv \\")
    print(f"    --clientes {output_dir}/clientes.csv \\")
    print(f"    --produtos {output_dir}/produtos.csv")
    print("\nPara otimizar:")
    print("  python scripts/run_with_real_data.py \\")
    print(f"    --cds {output_dir}/cds.csv \\")
    print(f"    --clientes {output_dir}/clientes.csv \\")
    print(f"    --produtos {output_dir}/produtos.csv")

    return 0


if __name__ == "__main__":
    sys.exit(main())
