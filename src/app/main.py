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
from app.pages import alocacoes, cds, custos, mapa, modelo  # noqa: E402
from otimizador.data.generator import gerar_dados_sinteticos  # noqa: E402
from otimizador.domain.schemas import SolverInput  # noqa: E402
from otimizador.solver import LogisticsSolver  # noqa: E402

st.set_page_config(
    page_title="Otimizador de Malha Logística",
    page_icon=":package:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado minimal
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #1F2937;
        margin-bottom: 2rem;
    }
    /* fundo branco no conteudo principal */
    .stApp {
        background-color: #FFFFFF;
    }
    .main .block-container {
        background-color: #FFFFFF;
    }
    /* texto escuro no conteudo, sem !important para nao quebrar controles */
    .main h1, .main h2, .main h3, .main h4, .main p,
    .main .stMarkdown, .stMetric, .stTabs [data-baseweb="tab-list"] {
        color: #111827;
    }
    /* sidebar branca com texto escuro */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSlider {
        color: #111827;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Otimizador de Malha Logística</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Ferramenta de otimização de rede de distribuição usando Programação Linear Inteira (MIP)'
    '</div>',
    unsafe_allow_html=True,
)

# Dados (cacheados)
@st.cache_data
def _carregar_dados():
    return gerar_dados_sinteticos(seed=42)

cds_data, clientes_data, produtos_data = _carregar_dados()

# Sidebar
config, rodar = render_sidebar(total_cds=len(cds_data))

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
