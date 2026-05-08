"""Tab: Detalhamento dos CDs na solução ótima."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from otimizador.domain.schemas import SolverOutput


def render(result: SolverOutput) -> None:
    st.markdown("### Detalhamento dos CDs na Solução Ótima")

    if not result.cds_abertos:
        st.info("Nenhum CD aberto na solução.")
        return

    for cd in result.cds_abertos:
        with st.expander(f"CD {cd.nome} — Utilizacao {cd.utilizacao_pct}%"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Capacidade", f"{cd.capacidade:,} un")
                st.metric("Volume", f"{cd.volume_total:,.0f} un")
            with col_b:
                st.metric("Custo Fixo", f"R$ {cd.custo_fixo:,.0f}")
                st.metric("Utilização", f"{cd.utilizacao_pct:.1f}%")
            with col_c:
                prods_cd = {
                    a.produto_nome
                    for a in result.alocacoes
                    if a.cd_id == cd.cd_id
                }
                clientes_cd = {
                    a.cliente_id
                    for a in result.alocacoes
                    if a.cd_id == cd.cd_id
                }
                st.metric("Produtos", f"{len(prods_cd)}")
                st.metric("Clientes", f"{len(clientes_cd)}")

            prod_qtd: dict[str, float] = {}
            for a in result.alocacoes:
                if a.cd_id == cd.cd_id:
                    prod_qtd[a.produto_nome] = prod_qtd.get(a.produto_nome, 0.0) + a.quantidade

            df = pd.DataFrame([
                {"Produto": p, "Quantidade": q}
                for p, q in sorted(prod_qtd.items(), key=lambda x: -x[1])
            ])
            fig = px.bar(
                df, x="Produto", y="Quantidade", color="Quantidade",
                color_continuous_scale="Blues", text_auto=".2s",
            )
            fig.update_layout(
                height=250, xaxis_tickangle=-30,
                paper_bgcolor="white", plot_bgcolor="white",
                font_color="#111827", title_font_color="#111827",
            )
            fig.update_xaxes(tickfont_color="#111827", title_font_color="#111827")
            fig.update_yaxes(tickfont_color="#111827", title_font_color="#111827")
            st.plotly_chart(fig, use_container_width=True)
