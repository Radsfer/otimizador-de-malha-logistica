"""Tab: Análise de Custos e comparativo de cenários."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import bar_custo_por_cd, pie_custos, stacked_comparativo
from otimizador.domain.entities import CD, Cliente, Produto
from otimizador.domain.schemas import ScenarioConfig, SolverInput, SolverOutput
from otimizador.solver import LogisticsSolver


def render(
    cds: list[CD],
    clientes: list[Cliente],
    produtos: list[Produto],
    result: SolverOutput,
) -> None:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### Composição do Custo Total")
        st.plotly_chart(pie_custos(result), use_container_width=True)

    with col_right:
        st.markdown("### Custo por CD Aberto")
        st.plotly_chart(bar_custo_por_cd(result), use_container_width=True)

    st.markdown("### Comparativo de Cenarios")

    cenarios = [
        ("Otimização Livre", ScenarioConfig(tempo_limite_segundos=30)),
        ("Máx 6 CDs", ScenarioConfig(tempo_limite_segundos=30, max_cds=6)),
        ("Máx 3 CDs", ScenarioConfig(tempo_limite_segundos=30, max_cds=3)),
        ("Todos CDs (atual)", ScenarioConfig(tempo_limite_segundos=30, cds_obrigatorios=list(range(len(cds))))),
    ]

    solver = LogisticsSolver()
    resultados: list[SolverOutput] = []
    nomes: list[str] = []
    for nome, cfg in cenarios:
        try:
            inp = SolverInput(cds=cds, clientes=clientes, produtos=produtos, config=cfg)
            r = solver.solve(inp)
            if r.status != "INVIAVEL":
                resultados.append(r)
                nomes.append(nome)
        except Exception:
            pass

    if resultados:
        st.plotly_chart(stacked_comparativo(resultados, nomes), use_container_width=True)

        df_comp = pd.DataFrame([
            {
                "Cenário": n,
                "CDs": len(r.cds_abertos),
                "Custo Total (R$)": r.custo_total,
                "Custo Fixo": r.custo_fixo,
                "Transporte": r.custo_transporte,
                "Estoque": r.custo_estoque,
            }
            for n, r in zip(nomes, resultados)
        ])
        st.dataframe(
            df_comp.style.format({
                "Custo Total (R$)": "R$ {:,.0f}",
                "Custo Fixo": "R$ {:,.0f}",
                "Transporte": "R$ {:,.0f}",
                "Estoque": "R$ {:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
