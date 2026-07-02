"""
tpm_violin_plot.py

Modular plotting utilities for visualizing TPM expression across an
arbitrary number of groups, combining a violin plot, boxplot, and jittered
scatter (strip) overlay on the same axis.

Designed around output from the nf-core/rnaseq pipeline (e.g.
salmon.merged.gene_tpm.tsv / salmon.merged.transcript_tpm.tsv), but the core
plotting function works with any tidy (long-format) TPM table, regardless of
the number of groups being compared.

On headless HPC environments (e.g. Cheaha) with no display, set a
non-interactive backend before importing pyplot in your driver script:

    import matplotlib
    matplotlib.use("Agg")
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------

def melt_nfcore_tpm(
    tpm_wide: pd.DataFrame,
    sample_metadata: pd.DataFrame,
    id_col: str = "gene_name",
    sample_id_col: str = "sample",
    group_col: str = "group",
) -> pd.DataFrame:
    """
    Convert an nf-core/rnaseq merged TPM matrix (genes x samples, wide
    format) into a tidy long-format dataframe annotated with group
    membership.
    """
    sample_cols = [c for c in tpm_wide.columns if c in set(sample_metadata[sample_id_col])]
    if not sample_cols:
        raise ValueError(
            "No overlap between tpm_wide columns and sample_metadata "
            f"'{sample_id_col}' values — check that sample names match."
        )
    long_df = tpm_wide.melt(
        id_vars=[id_col], value_vars=sample_cols, var_name=sample_id_col, value_name="TPM"
    )
    long_df = long_df.merge(
        sample_metadata[[sample_id_col, group_col]], on=sample_id_col, how="left"
    )
    missing = long_df[group_col].isna().sum()
    if missing:
        print(f"Warning: {missing} sample rows had no matching group in metadata.")
    return long_df


# --------------------------------------------------------------------------
# Core plotting function — works for any number of groups
# --------------------------------------------------------------------------

def plot_tpm_violin(
    data: pd.DataFrame,
    group_col: str,
    value_col: str = "TPM",
    group_order: Optional[Sequence[str]] = None,
    palette: Optional[Union[dict, str, Sequence]] = "Set2",
    log_scale: bool = True,
    pseudocount: float = 1.0,
    point_size: float = 4.0,
    point_alpha: float = 0.7,
    jitter: float = 0.12,
    violin_alpha: float = 0.45,
    box_width: float = 0.18,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
    show_n: bool = True,
    stat_test: Optional[str] = None,
) -> plt.Axes:
    data = data.dropna(subset=[group_col, value_col]).copy()

    if group_order is None:
        group_order = sorted(data[group_col].unique())
    n_groups = len(group_order)

    if ax is None:
        fig_width = max(3.5, 1.4 * n_groups)
        fig, ax = plt.subplots(figsize=(fig_width, 4.5))

    plot_col = value_col
    if log_scale:
        plot_col = f"log10_{value_col}"
        data[plot_col] = np.log10(data[value_col] + pseudocount)

    sns.violinplot(
        data=data, x=group_col, y=plot_col, order=group_order,
        hue=group_col, hue_order=group_order, palette=palette, legend=False,
        inner=None, cut=0, linewidth=1.0, ax=ax,
    )
    for collection in ax.collections:
        collection.set_alpha(violin_alpha)

    sns.boxplot(
        data=data, x=group_col, y=plot_col, order=group_order,
        hue=group_col, hue_order=group_order, legend=False,
        width=box_width, showcaps=True, boxprops={"facecolor": "white", "zorder": 3},
        whiskerprops={"zorder": 3}, medianprops={"color": "black", "zorder": 4},
        showfliers=False, ax=ax,
    )

    sns.stripplot(
        data=data, x=group_col, y=plot_col, order=group_order,
        hue=group_col, hue_order=group_order, legend=False,
        palette=["black"] * len(group_order), size=point_size, alpha=point_alpha, jitter=jitter,
        ax=ax, zorder=5,
    )

    ax.set_xlabel(group_col)
    ax.set_ylabel(ylabel or (f"log10({value_col} + {pseudocount})" if log_scale else value_col))

    if n_groups > 4:
        ax.tick_params(axis="x", rotation=30)

    if show_n:
        ymax = data[plot_col].max()
        ypad = (data[plot_col].max() - data[plot_col].min()) * 0.06 + 1e-9
        for i, grp in enumerate(group_order):
            n = (data[group_col] == grp).sum()
            ax.text(i, ymax + ypad, f"n={n}", ha="center", va="bottom", fontsize=8)
        ax.set_ylim(top=ymax + ypad * 3)

    full_title = title or ""
    if stat_test:
        pval = _run_stat_test(data, group_col, plot_col, group_order, stat_test)
        if pval is not None:
            full_title = f"{full_title}  (p={pval:.3g})".strip()
    if full_title:
        ax.set_title(full_title)

    return ax


def _run_stat_test(
    data: pd.DataFrame, group_col: str, value_col: str,
    group_order: Sequence[str], stat_test: str,
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
    raise ValueError(f"Unknown stat_test: {stat_test!r}. Use 'mannwhitney' or 'kruskal'.")


# --------------------------------------------------------------------------
# Multi-gene grid wrapper
# --------------------------------------------------------------------------

def plot_multi_gene_violin(
    data: pd.DataFrame,
    genes: Sequence[str],
    gene_col: str,
    group_col: str,
    value_col: str = "TPM",
    ncols: int = 3,
    panel_size: tuple = (4.0, 3.8),
    **plot_kwargs,
) -> plt.Figure:
    n = len(genes)
    ncols = max(1, min(ncols, n))
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(panel_size[0] * ncols, panel_size[1] * nrows), squeeze=False
    )
    axes_flat = axes.flatten()

    for i, gene in enumerate(genes):
        gene_data = data[data[gene_col] == gene]
        if gene_data.empty:
            print(f"Warning: no rows found for gene '{gene}', skipping panel.")
            axes_flat[i].set_visible(False)
            continue
        plot_tpm_violin(
            gene_data, group_col=group_col, value_col=value_col,
            ax=axes_flat[i], title=gene, **plot_kwargs,
        )

    for j in range(n, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.tight_layout()
    return fig
