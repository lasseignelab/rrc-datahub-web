"""Tests for components/tpm_violin_plot_plotly.py: automatic stats tests."""

import pandas as pd
import pytest

from components.tpm_violin_plot_plotly import (
    plot_tpm_violin_plotly,
    select_stat_test,
)


def _title(fig):
    """Return the figure's title text."""
    return fig.to_dict()["layout"]["title"]["text"]


def _make_data(groups):
    """Build a TPM table with five distinct values per group."""
    rows = []
    for offset, group in enumerate(groups):
        for i in range(5):
            rows.append({"genotype": group, "TPM": float(offset * 10 + i)})
    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    "n_groups, expected",
    [(0, None), (1, None), (2, "mannwhitney"), (3, "kruskal"), (5, "kruskal")],
)
def test_select_stat_test_by_group_count(n_groups, expected):
    """Two groups use Mann-Whitney U, three or more Kruskal-Wallis."""
    assert select_stat_test(n_groups) == expected


def test_two_groups_title_names_mann_whitney():
    """Two groups add the Mann-Whitney U name and p-value to the title."""
    fig = plot_tpm_violin_plotly(
        _make_data(["WT", "KO"]), group_col="genotype", title="Pkd2", show_stats=True
    )
    assert _title(fig).startswith("Pkd2  (Mann-Whitney U, p=")


def test_three_groups_title_names_kruskal_wallis():
    """Three groups add the Kruskal-Wallis name and p-value to the title."""
    fig = plot_tpm_violin_plotly(
        _make_data(["WT", "HET", "KO"]),
        group_col="genotype",
        title="Pkd2",
        show_stats=True,
    )
    assert _title(fig).startswith("Pkd2  (Kruskal-Wallis, p=")


def test_one_group_title_explains_no_test():
    """A single group gets a note instead of a test."""
    fig = plot_tpm_violin_plotly(
        _make_data(["WT"]), group_col="genotype", title="Pkd2", show_stats=True
    )
    assert _title(fig) == "Pkd2  (statistics need 2 or more groups)"


def test_identical_values_do_not_crash():
    """All-identical values (e.g. all TPM 0) report a non-computable p-value."""
    data = pd.DataFrame({"genotype": ["WT", "HET", "KO"] * 3, "TPM": [0.0] * 9})
    fig = plot_tpm_violin_plotly(
        data, group_col="genotype", title="Pkd2", show_stats=True
    )
    assert "Kruskal-Wallis: p-value not computable" in _title(fig)


def test_stats_off_leaves_title_unchanged():
    """With show_stats False the title is just the gene."""
    fig = plot_tpm_violin_plotly(
        _make_data(["WT", "KO"]), group_col="genotype", title="Pkd2"
    )
    assert _title(fig) == "Pkd2"
