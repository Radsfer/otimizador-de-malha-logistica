"""Barra lateral de configuração do cenário."""

from __future__ import annotations

import streamlit as st

from otimizador.domain.schemas import ScenarioConfig

def render_sidebar(cd_nomes: list[str]) -> tuple[ScenarioConfig, bool, str]:
    """Renderiza a sidebar e retorna (config, rodar_otimizacao, fonte_dados)."""
    total_cds = len(cd_nomes)
    with st.sidebar:
        st.markdown("### Configuracoes do Cenario")
        st.markdown("---")

        fonte_dados = st.radio(
            "Fonte de dados",
            ["Sintético (lácteos)", "Olist (e-commerce)"],
            help="Escolha o dataset para análise",
        )
        if fonte_dados == "Olist (e-commerce)":
            st.caption("Sellers como CDs, customers como mercados de demanda.")

        st.markdown("---")

        max_cds = st.slider(
            "Máximo de CDs permitidos",
            min_value=1,
            max_value=total_cds,
            value=total_cds,
            help="Limite o número máximo de CDs que podem ficar abertos",
        )

        st.markdown("---")
        st.markdown("#### CDs Obrigatórios")
        st.markdown("*Marque CDs que devem permanecer abertos por critério estratégico*")

        obrigatorios = []
        for i, nome in enumerate(cd_nomes):
            default = nome == "São Paulo" or "São Paulo" in nome
            if st.checkbox(nome, key=f"cd_{i}", value=default):
                obrigatorios.append(i)

        st.markdown("---")
        tempo_limite = st.slider(
            "Tempo limite de otimização (segundos)",
            min_value=10,
            max_value=300,
            value=60,
            step=10,
            help="Quanto tempo o solver tem para encontrar a melhor solução",
        )

        st.markdown("---")
        rodar = st.button("Executar Otimizacao", type="primary", use_container_width=True)

        if st.button("Resetar Dados", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith("cd_"):
                    continue
                del st.session_state[key]
            st.rerun()

    config = ScenarioConfig(
        tempo_limite_segundos=tempo_limite,
        cds_obrigatorios=obrigatorios if obrigatorios else None,
        max_cds=max_cds if max_cds < total_cds else None,
    )
    return config, rodar, fonte_dados
