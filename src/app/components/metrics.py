"""KPIs principais do dashboard."""

from __future__ import annotations

import streamlit as st

from otimizador.domain.schemas import SolverOutput


def render_metrics(result: SolverOutput, total_cds: int) -> None:
    """Renderiza as métricas principais em colunas."""
    if result.status == "INVIAVEL":
        st.error(
            "O cenario configurado e inviavel. "
            "Tente relaxar restricoes (aumentar max CDs ou remover obrigatorios)."
        )
        st.stop()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Custo Total Mensal", f"R$ {result.custo_total:,.0f}")
    with col2:
        st.metric("CDs Abertos", f"{len(result.cds_abertos)}/{total_cds}")
    with col3:
        st.metric("Custo Transporte", f"R$ {result.custo_transporte:,.0f}")
    with col4:
        st.metric("Custo Estoque", f"R$ {result.custo_estoque:,.0f}")
    with col5:
        st.metric("Demanda Atendida", f"{result.demanda_total:,} un")
