"""Tab: Mapa da rede otimizada."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from otimizador.domain.entities import CD, Cliente
from otimizador.domain.schemas import SolverOutput


def render(cds: list[CD], clientes: list[Cliente], result: SolverOutput) -> None:
    st.markdown("### Visualização Geográfica da Rede Otimizada")

    abertos_ids = {cd.cd_id for cd in result.cds_abertos}

    df_cds = pd.DataFrame([
        {
            "tipo": "CD Aberto",
            "nome": cd.nome,
            "cidade": cd.cidade,
            "lat": cd.lat,
            "lon": cd.lon,
            "tamanho": cd.volume_total / 100,
        }
        for cd in result.cds_abertos
    ])

    df_fechados = pd.DataFrame([
        {
            "tipo": "CD Fechado",
            "nome": cd.nome,
            "cidade": cd.cidade,
            "lat": cd.lat,
            "lon": cd.lon,
            "tamanho": 15,
        }
        for cd in cds if cd.id not in abertos_ids
    ])

    df_clientes = pd.DataFrame([
        {
            "tipo": "Cliente",
            "nome": cli.nome,
            "cidade": cli.cidade,
            "lat": cli.lat,
            "lon": cli.lon,
            "tamanho": 8,
        }
        for cli in clientes
    ])

    df_mapa = pd.concat([df_cds, df_fechados, df_clientes], ignore_index=True)

    fig = px.scatter_mapbox(
        df_mapa,
        lat="lat",
        lon="lon",
        color="tipo",
        size="tamanho",
        hover_name="nome",
        hover_data=["cidade"],
        color_discrete_map={
            "CD Aberto": "#2563EB",
            "CD Fechado": "#9CA3AF",
            "Cliente": "#059669",
        },
        zoom=3,
        height=600,
        title="Malha Logistica Otimizada — Brasil",
    )

    # Linhas de alocação (agrupadas por cliente para não poluir)
    aloc_por_cd: dict[str, list] = {}
    for a in result.alocacoes:
        aloc_por_cd.setdefault(a.cd_id, []).append(a)

    cd_info_map = {cd.cd_id: cd for cd in result.cds_abertos}

    for cd_id, alocs in aloc_por_cd.items():
        cd_info = cd_info_map.get(cd_id)
        if cd_info is None:
            continue
        clientes_agg: dict[str, dict] = {}
        for a in alocs:
            cid = a.cliente_id
            if cid not in clientes_agg:
                clientes_agg[cid] = {"lat": a.cliente_lat, "lon": a.cliente_lon, "qtd": 0}
            clientes_agg[cid]["qtd"] += a.quantidade
        for cinfo in clientes_agg.values():
            fig.add_trace(go.Scattermapbox(
                mode="lines",
                lon=[cd_info.lon, cinfo["lon"]],
                lat=[cd_info.lat, cinfo["lat"]],
                line=dict(width=0.5, color="#93C5FD"),
                hoverinfo="skip",
                showlegend=False,
                opacity=0.3,
            ))

    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div style="background:#F9FAFB;border-left:4px solid #2563EB;padding:1rem;border-radius:0 8px 8px 0;margin:1rem 0;">
    <b>Como ler este mapa:</b><br>
    <b>CDs Abertos</b> atendem clientes (linhas vermelhas).<br>
    <b>CDs Fechados</b> representam economia de custo fixo.<br>
    <b>Clientes</b> consomem produtos da rede.
    </div>
    """, unsafe_allow_html=True)
