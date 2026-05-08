"""Helpers de gráficos Plotly reusáveis."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

from otimizador.domain.schemas import SolverOutput


def pie_custos(result: SolverOutput) -> go.Figure:
    """Gráfico de pizza com composição do custo total."""
    df = {
        "Categoria": ["Custo Fixo (CDs)", "Custo de Transporte", "Custo de Estoque"],
        "Valor": [result.custo_fixo, result.custo_transporte, result.custo_estoque],
    }
    fig = px.pie(
        df, values="Valor", names="Categoria",
        hole=0.4, color_discrete_sequence=["#2563EB", "#059669", "#D97706"],
    )
    fig.update_traces(textinfo="label+percent", textfont_size=12)
    _apply_contrast(fig)
    return fig


def bar_custo_por_cd(result: SolverOutput) -> go.Figure:
    """Gráfico de barras com custo total por CD aberto."""
    custo_por_cd: dict[str, float] = {}
    for cd in result.cds_abertos:
        custo_por_cd[cd.nome] = cd.custo_fixo

    for a in result.alocacoes:
        custo_por_cd[a.cd_nome] = custo_por_cd.get(a.cd_nome, 0.0) + a.custo_transporte_total

    for e in result.estoques:
        custo_por_cd[e.cd_nome] = custo_por_cd.get(e.cd_nome, 0.0) + e.custo_estoque_mensal

    df = {
        "CD": list(custo_por_cd.keys()),
        "Custo Total (R$)": list(custo_por_cd.values()),
    }
    fig = px.bar(
        df, x="CD", y="Custo Total (R$)",
        color="Custo Total (R$)", color_continuous_scale="Blues",
        text_auto=".2s",
    )
    fig.update_layout(xaxis_tickangle=-45)
    _apply_contrast(fig)
    return fig


def stacked_comparativo(resultados: list[SolverOutput], nomes: list[str]) -> go.Figure:
    """Gráfico de barras empilhadas comparando cenários."""
    fig = go.Figure()
    for label, attr, color in [
        ("Custo Fixo", "custo_fixo", "#2563EB"),
        ("Transporte", "custo_transporte", "#059669"),
        ("Estoque", "custo_estoque", "#D97706"),
    ]:
        fig.add_trace(go.Bar(
            name=label,
            x=nomes,
            y=[getattr(r, attr) for r in resultados],
            marker_color=color,
        ))
    fig.update_layout(
        barmode="stack",
        xaxis_title="Cenário",
        yaxis_title="Custo (R$)",
        legend_title="Componente",
        height=450,
    )
    _apply_contrast(fig)
    return fig


def _apply_contrast(fig: go.Figure) -> None:
    """Forca texto escuro em todos os elementos do grafico."""
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#111827",
        title_font_color="#111827",
        legend_font_color="#111827",
    )
    fig.update_xaxes(tickfont_color="#111827", title_font_color="#111827")
    fig.update_yaxes(tickfont_color="#111827", title_font_color="#111827")
