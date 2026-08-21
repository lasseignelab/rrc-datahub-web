"""
tpm_violin_plot_plotly.py

Plotly equivalent of plot_tpm_violin() from tpm_violin_plot.py.
Returns a go.Figure, making it directly usable in a Dash app via dcc.Graph.

Data preparation (melt_nfcore_tpm) is shared with the original module —
import it from tpm_violin_plot.py as usual.
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

_DEFAULT_COLORS = [
    "#66c2a5",
    "#fc8d62",
    "#8da0cb",
    "#e78ac3",
    "#a6d854",
]


def plot_tpm_violin_plotly(
    data: pd.DataFrame,
    group_col: str,
    value_col: str = "TPM",
    group_order: Optional[Sequence[str]] = None,
    palette: Optional[Union[dict, list]] = None,
    log_scale: bool = True,
    pseudocount: float = 1.0,
    point_size: float = 5.0,
    point_opacity: float = 0.7,
    jitter: float = 0.3,
    title: Optional[str] = None,
    show_n: bool = True,
    stat_test: Optional[str] = None,
    group_label: Optional[str] = None,
) -> go.Figure:
    data = data.dropna(subset=[group_col, value_col]).copy()

    if group_order is None:
        group_order = sorted(data[group_col].unique())
    group_order = list(group_order)

    colors = _resolve_palette(palette, group_order)

    plot_col = value_col
    ylabel = value_col
    if log_scale:
        plot_col = f"_log10_{value_col}"
        data[plot_col] = np.log10(data[value_col] + pseudocount)
        ylabel = f"log10({value_col} + {pseudocount})"

    fig = go.Figure()

    for i, group in enumerate(group_order):
        grp_data = data.loc[data[group_col] == group, plot_col].values
        color = colors[i]
        n = len(grp_data)
        name = f"{group} (n={n})" if show_n else group

        fig.add_trace(
            go.Violin(
                x=np.full(n, i),
                y=grp_data,
                name=name,
                side="both",
                line_color=color,
                fillcolor=color,
                opacity=0.45,
                points=False,
                box_visible=False,
                meanline_visible=False,
                spanmode="hard",
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Box(
                x=np.full(n, i),
                y=grp_data,
                name=name,
                marker_color=color,
                line_color="black",
                fillcolor="white",
                width=0.12,
                boxpoints=False,
                showlegend=False,
            )
        )

        x_jittered = i + np.random.default_rng(42 + i).uniform(
            -jitter,
            jitter,
            n,
        )
        fig.add_trace(
            go.Scatter(
                x=x_jittered,
                y=grp_data,
                mode="markers",
                marker=dict(color="black", size=point_size, opacity=point_opacity),
                name=name,
                showlegend=False,
            )
        )

    full_title = title or ""
    if stat_test:
        pval = _run_stat_test(data, group_col, plot_col, group_order, stat_test)
        if pval is not None:
            full_title = f"{full_title}  (p={pval:.3g})".strip()

    axis_label = group_label if group_label is not None else group_col
    fig.update_layout(
        title=full_title,
        xaxis_title=axis_label,
        yaxis_title=ylabel,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(group_order))),
            ticktext=list(group_order),
        ),
        violingap=0.3,
        violinmode="overlay",
        boxmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            title_text=axis_label,
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="left",
            x=0,
        ),
        font=dict(family="Arial", size=13),
        autosize=True,
        margin=dict(b=160),
    )
    fig.update_xaxes(showgrid=False, linecolor="black", ticks="outside")
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#eeeeee",
        linecolor="black",
        ticks="outside",
    )

    return fig


def _resolve_palette(palette: Optional[Union[dict, list]], group_order: list) -> list:
    if palette is None:
        return [
            _DEFAULT_COLORS[i % len(_DEFAULT_COLORS)] for i in range(len(group_order))
        ]
    if isinstance(palette, dict):
        return [
            palette.get(g, _DEFAULT_COLORS[i % len(_DEFAULT_COLORS)])
            for i, g in enumerate(group_order)
        ]
    return list(palette)


def _run_stat_test(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    group_order: list,
    stat_test: str,
) -> Optional[float]:
    groups = [data.loc[data[group_col] == g, value_col].values for g in group_order]
    if stat_test == "mannwhitney":
        if len(groups) != 2:
            print("Warning: mannwhitney requires exactly 2 groups; skipping stat test.")
            return None
        _, p = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
        return p
    if stat_test == "kruskal":
        _, p = stats.kruskal(*groups)
        return p
    raise ValueError(
        f"Unknown stat_test: {stat_test!r}. " "Use 'mannwhitney' or 'kruskal'."
    )
