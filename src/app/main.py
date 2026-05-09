"""Entrypoint do dashboard Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote src/ está no path sem gambiarras
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.components.metrics import render_metrics  # noqa: E402
from app.components.sidebar import render_sidebar  # noqa: E402
from app.views import alocacoes, cds, custos, mapa, modelo  # noqa: E402
from otimizador.data.generator import gerar_dados_sinteticos  # noqa: E402
from otimizador.data.loader import DataLoader  # noqa: E402
from otimizador.domain.schemas import SolverInput  # noqa: E402
from otimizador.solver import LogisticsSolver  # noqa: E402

DATA_DIR = PROJECT_ROOT.parent / "data_olist"


@st.cache_data
def _carregar_dados(fonte: str):
    if fonte == "Olist (e-commerce)":
        return DataLoader.from_csvs(
            DATA_DIR / "cds.csv",
            DATA_DIR / "clientes.csv",
            DATA_DIR / "produtos.csv",
        )
    return gerar_dados_sinteticos(seed=42)

st.set_page_config(
    page_title="Otimizador de Malha Logística",
    page_icon=":package:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { min-width: 260px !important; max-width: 300px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("Otimizador de Malha Logística")
st.subheader(
    "Ferramenta de otimização de rede de distribuição usando Programação Linear Inteira (MIP)"
)

if "fonte_dados" not in st.session_state:
    st.session_state["fonte_dados"] = "Sintético (lácteos)"

cds_data, clientes_data, produtos_data = _carregar_dados(st.session_state["fonte_dados"])

# Sidebar
config, rodar, fonte_dados = render_sidebar(cd_nomes=[cd.nome for cd in cds_data])

# Se mudou a fonte, limpa resultado e recarrega
if fonte_dados != st.session_state.get("fonte_dados"):
    st.session_state["fonte_dados"] = fonte_dados
    for key in ["resultado", "otimizador"]:
        st.session_state.pop(key, None)
    st.rerun()

# Recarrega se a fonte mudou e deu rerun acima — se não, já tá carregado
cds_data, clientes_data, produtos_data = _carregar_dados(st.session_state["fonte_dados"])

# Estado inicial
if "resultado" not in st.session_state:
    with st.spinner("Executando otimização inicial..."):
        solver = LogisticsSolver()
        inp = SolverInput(
            cds=cds_data, clientes=clientes_data, produtos=produtos_data,
            config=config,
        )
        st.session_state["resultado"] = solver.solve(inp)
        st.session_state["otimizador"] = solver

if rodar:
    with st.spinner("Otimizando rede..."):
        solver = LogisticsSolver()
        inp = SolverInput(
            cds=cds_data, clientes=clientes_data, produtos=produtos_data,
            config=config,
        )
        st.session_state["resultado"] = solver.solve(inp)
        st.session_state["otimizador"] = solver

# Título contextual
if fonte_dados == "Olist (e-commerce)":
    st.info(f"Dataset Olist: {len(cds_data)} sellers como CDs, {len(clientes_data)} customers, {len(produtos_data)} categorias de produto.")

result = st.session_state["resultado"]

# Métricas
render_metrics(result, total_cds=len(cds_data))

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Mapa da Rede", "Análise de Custos", "Alocações", "CDs Otimizados", "Modelo Matemático"
])

with tab1:
    mapa.render(cds_data, clientes_data, result)

with tab2:
    custos.render(cds_data, clientes_data, produtos_data, result)

with tab3:
    alocacoes.render(result)

with tab4:
    cds.render(result)

with tab5:
    modelo.render()

st.markdown("---")
st.markdown(
    "<center><small>"
    "Projeto de modelagem matemática e otimização em supply chain"
    "</small></center>",
    unsafe_allow_html=True,
)
