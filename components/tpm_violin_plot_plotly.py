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

DEFAULT_COLORS = [
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
    show_stats: bool = False,
    group_label: Optional[str] = None,
    dataset_accession: Optional[str] = None,
) -> go.Figure:
    """Build a violin + box + jittered-points figure of TPM by group.

    The title is the main line (``title``) with a smaller subtitle line
    beneath it holding the dataset accession and, when ``show_stats`` is
    True, the test name and p-value. The test is picked from the number of
    groups plotted (see ``select_stat_test``).
    """
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

    stat_label = (
        stat_summary(data, group_col, value_col, group_order) if show_stats else None
    )
    full_title = build_title(title, dataset_accession, stat_label)

    axis_label = group_label if group_label is not None else group_col
    fig.update_layout(
        title=dict(text=full_title, x=0.05, xanchor="left"),
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


# Middle dot between the pieces of the subtitle line.
SUBTITLE_SEPARATOR = " \u00b7 "


def build_title(
    title: Optional[str],
    dataset_accession: Optional[str] = None,
    stat_label: Optional[str] = None,
) -> str:
    """Return the plot title: a main line plus an optional subtitle line.

    The subtitle joins the dataset accession and the statistics summary with
    a middle dot, e.g. ``Dataset PRJNA123456 · Mann-Whitney U, p=0.012``.
    Plotly renders the ``<sup>`` text smaller, which keeps the p-value out of
    the main heading. With neither extra, the title is returned unchanged.
    """
    main = title or ""
    parts = []
    if dataset_accession:
        parts.append(f"Dataset {dataset_accession}")
    if stat_label:
        parts.append(stat_label)
    if not parts:
        return main
    subtitle = "<sup>" + SUBTITLE_SEPARATOR.join(parts) + "</sup>"
    return f"{main}<br>{subtitle}" if main else subtitle


def _resolve_palette(palette: Optional[Union[dict, list]], group_order: list) -> list:
    if palette is None:
        return [
            DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i in range(len(group_order))
        ]
    if isinstance(palette, dict):
        return [
            palette.get(g, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
            for i, g in enumerate(group_order)
        ]
    return list(palette)


STAT_TEST_NAMES = {
    "mannwhitney": "Mann-Whitney U",
    "kruskal": "Kruskal-Wallis",
}


def select_stat_test(n_groups: int) -> Optional[str]:
    """Return the test key for ``n_groups`` groups, or None if fewer than 2.

    2 groups -> Mann-Whitney U; 3 or more -> Kruskal-Wallis.
    """
    if n_groups < 2:
        return None
    if n_groups == 2:
        return "mannwhitney"
    return "kruskal"


def stat_summary(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    group_order: Sequence[str],
) -> str:
    """Pick and run the test for the plotted groups; return a short summary.

    Used for both the plot title and the Charts page caption. Both tests are
    rank-based, so raw and log-transformed values give the same p-value.
    """
    group_order = list(group_order)
    stat_test = select_stat_test(len(group_order))
    if stat_test is None:
        return "statistics need 2 or more groups"
    test_name = STAT_TEST_NAMES[stat_test]
    pval = _run_stat_test(data, group_col, value_col, group_order, stat_test)
    if pval is None or np.isnan(pval):
        return f"{test_name}: p-value not computable"
    return f"{test_name}, p={pval:.3g}"


def _run_stat_test(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    group_order: list,
    stat_test: str,
) -> Optional[float]:
    """Run ``stat_test`` across the groups; None if scipy cannot compute it."""
    groups = [data.loc[data[group_col] == g, value_col].values for g in group_order]
    try:
        if stat_test == "mannwhitney":
            _, p = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
            return float(p)
        if stat_test == "kruskal":
            # Raises ValueError when every value is identical (e.g. all TPM 0).
            _, p = stats.kruskal(*groups)
            return float(p)
    except ValueError:
        return None
    raise ValueError(
        f"Unknown stat_test: {stat_test!r}. Use 'mannwhitney' or 'kruskal'."
    )
