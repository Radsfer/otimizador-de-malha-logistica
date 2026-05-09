"""Tab: Alocações otimizadas com filtros."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from otimizador.domain.schemas import SolverOutput


def render(result: SolverOutput) -> None:
    st.markdown(
        "<style>.stMultiSelect [data-baseweb='tag'] { background-color: #1e40af !important; }</style>",
        unsafe_allow_html=True,
    )
    st.markdown("### Alocações Otimizadas (CD → Cliente → Produto)")

    if not result.alocacoes:
        st.info("Nenhuma alocação encontrada.")
        return

    df_aloc = pd.DataFrame([a.model_dump() for a in result.alocacoes])

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        cds_disp = sorted(df_aloc["cd_nome"].unique())
        cd_sel = st.multiselect("Filtrar por CD", cds_disp, default=cds_disp)
    with col_f2:
        prods_disp = sorted(df_aloc["produto_nome"].unique())
        prod_sel = st.multiselect("Filtrar por Produto", prods_disp, default=prods_disp)
    with col_f3:
        min_qtd = st.number_input("Quantidade mínima", min_value=0, value=50)

    df_filt = df_aloc[
        (df_aloc["cd_nome"].isin(cd_sel)) &
        (df_aloc["produto_nome"].isin(prod_sel)) &
        (df_aloc["quantidade"] >= min_qtd)
    ]

    st.dataframe(
        df_filt[[
            "cd_nome", "cliente_nome", "produto_nome", "quantidade", "custo_transporte_total"
        ]].rename(columns={
            "cd_nome": "CD",
            "cliente_nome": "Cliente",
            "produto_nome": "Produto",
            "quantidade": "Qtd (un)",
            "custo_transporte_total": "Custo Transp. (R$)",
        }).style.format({
            "Qtd (un)": "{:,.0f}",
            "Custo Transp. (R$)": "R$ {:,.2f}",
        }),
        use_container_width=True,
        height=500,
    )

    st.markdown(
        f"**Total de registros:** {len(df_filt):,} | "
        f"**Volume filtrado:** {df_filt['quantidade'].sum():,.0f} unidades"
    )
