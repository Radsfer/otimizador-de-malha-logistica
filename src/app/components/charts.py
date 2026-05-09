"""Helpers de gráficos Plotly reusáveis."""

from __future__ import annotations

import plotly.graph_objects as go

from otimizador.domain.schemas import SolverOutput


def pie_custos(result: SolverOutput) -> go.Figure:
    """Gráfico de pizza com composição do custo total."""
    labels = ["Custo Fixo (CDs)", "Custo de Transporte", "Custo de Estoque"]
    values = [result.custo_fixo, result.custo_transporte, result.custo_estoque]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=["#2563eb", "#16a34a", "#dc2626"],
                textinfo="label+percent",
                textfont_size=12,
                name="Custo",
                hovertemplate="%{label}<br>R$ %{value:,.0f}<extra>Custo</extra>",
            )
        ]
    )
    fig.update_layout(title_text="")
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

    cds = list(custo_por_cd.keys())
    valores = list(custo_por_cd.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=cds,
                y=valores,
                marker_color="#2563eb",
                text=[f"R$ {v:,.0f}" for v in valores],
                textposition="outside",
                name="Custo Total",
                hovertemplate="%{x}<br>R$ %{y:,.0f}<extra>Custo Total</extra>",
            )
        ]
    )
    fig.update_layout(xaxis_tickangle=-45, title_text="")
    _apply_contrast(fig)
    return fig


def stacked_comparativo(resultados: list[SolverOutput], nomes: list[str]) -> go.Figure:
    """Gráfico de barras empilhadas comparando cenários."""
    fig = go.Figure()
    for label, attr, color in [
        ("Custo Fixo", "custo_fixo", "#2563eb"),
        ("Transporte", "custo_transporte", "#16a34a"),
        ("Estoque", "custo_estoque", "#dc2626"),
    ]:
        fig.add_trace(
            go.Bar(
                name=label,
                x=nomes,
                y=[getattr(r, attr) for r in resultados],
                marker_color=color,
                hovertemplate="%{x}<br>R$ %{y:,.0f}<extra>" + label + "</extra>",
            )
        )
    fig.update_layout(
        title_text="",
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
