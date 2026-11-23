"""Tests for the charts page's chat-link handling (pages/charts.py)."""

from dash import no_update

from app import app  # noqa: F401  # registers pages before pages.charts is imported
from components.chat_assistant import build_chart_link
from pages import charts


def test_parse_url_filters_round_trips_chat_links():
    """A link built by the chat assistant parses back to the same settings."""
    url = build_chart_link(
        ["prjna2", "PRJNA1", "PRJNA2"],
        gene="Pkd1",
        scientific_name=["Mus musculus"],
        sex=["female"],
        sample_type=["kidney (whole)"],
        min_age_days=30,
        max_age_days=182.5,
    )
    parsed = charts._parse_url_filters(url.split("?", 1)[1])
    assert parsed["datasets"] == ["PRJNA2", "PRJNA1"]
    assert parsed["scientific_name"] == ["Mus musculus"]
    assert parsed["sex"] == ["female"]
    assert parsed["underlying_variant"] == []
    assert parsed["sample_type"] == ["kidney (whole)"]
    assert parsed["min_age_days"] == 30
    assert parsed["max_age_days"] == 182.5


def test_parse_url_filters_ignores_missing_and_malformed_values():
    """Absent or non-numeric parameters come back empty, never raise."""
    parsed = charts._parse_url_filters("?gene=Pkd1&min_age_days=abc&max_age_days=inf")
    assert parsed["datasets"] == []
    assert parsed["sex"] == []
    assert parsed["min_age_days"] is None
    assert parsed["max_age_days"] is None
    assert charts._parse_url_filters(None)["datasets"] == []


def test_match_options_is_case_insensitive_and_keeps_db_spelling():
    """Requested values match dropdown options ignoring case."""
    matched = charts._match_options(["FEMALE", "other"], ["female", "male"])
    assert matched == ["female"]


def test_limit_rows_keeps_only_answer_datasets():
    """With a limit, only the answer's datasets stay in the table."""
    rows = [{"bioproject": "PRJNA1"}, {"bioproject": "PRJNA2"}]
    assert charts._limit_rows(rows, ["PRJNA2"]) == [{"bioproject": "PRJNA2"}]
    assert charts._limit_rows(rows, None) == rows


def test_choose_selected_prefers_first_answer_dataset_when_limit_set():
    """A new chat link selects the answer's first dataset that is listed."""
    listed = ["PRJNA1", "PRJNA2", "PRJNA3"]
    limit = ["PRJNA9", "PRJNA3", "PRJNA1"]
    assert charts._choose_selected(listed, "PRJNA1", limit, True) == "PRJNA3"
    # Later filter changes keep the user's choice while it is still listed.
    assert charts._choose_selected(listed, "PRJNA1", limit, False) == "PRJNA1"
    assert charts._choose_selected(listed, "PRJNA2", None, False) == "PRJNA2"
    assert charts._choose_selected(listed, "PRJNA7", None, False) == "PRJNA1"
    assert charts._choose_selected([], "PRJNA1", limit, True) is None


def test_apply_url_filters_sets_only_named_filters(monkeypatch):
    """Named filters are set (and their 'not provided' box unticked);
    unnamed or unmatched ones are left alone."""
    monkeypatch.setattr(charts, "_all_sexes", ["female", "male"])
    monkeypatch.setattr(charts, "_all_scientific_names", ["Mus musculus"])
    result = charts.apply_url_filters(
        "?datasets=PRJNA1&sex=Female&scientific_name=Danio+rerio&max_age_days=60"
    )
    (
        names,
        sexes,
        unknown_sex,
        variants,
        unknown_variant,
        sample_types,
        age_min,
        age_max,
        unknown_age,
        limit,
    ) = result
    assert sexes == ["female"]
    assert unknown_sex == []
    # No species matched, so that filter keeps its default.
    assert names is no_update
    assert variants is no_update and unknown_variant is no_update
    assert sample_types is no_update
    assert age_min is no_update
    assert age_max == 60
    assert unknown_age == []
    assert limit == ["PRJNA1"]


def test_apply_url_filters_without_params_changes_nothing():
    """A plain /charts visit leaves every filter at its default."""
    result = charts.apply_url_filters("")
    assert all(value is no_update for value in result[:-1])
    assert result[-1] is None


def _caption_data():
    """Two groups with clearly different TPM values."""
    import pandas as pd  # pylint: disable=import-outside-toplevel

    return pd.DataFrame(
        {
            "genotype": ["WT"] * 5 + ["KO"] * 5,
            "TPM": [1, 2, 3, 4, 5, 20, 21, 22, 23, 24],
        }
    )


def test_plot_caption_describes_plot_without_stats():
    """Caption names the gene, group count and groups."""
    caption = charts._plot_caption("Pkd2", ["KO", "WT"], _caption_data(), False)
    assert caption == (
        "Violin plot of log₁₀(TPM + 1) for Pkd2 across 2 groups: KO, WT."
    )


def test_plot_caption_includes_stats_result():
    """With stats on, the caption carries the same test and p-value as the title."""
    caption = charts._plot_caption("Pkd2", ["KO", "WT"], _caption_data(), True)
    assert caption.endswith("KO, WT. Mann-Whitney U, p=0.00794.")


def test_plot_caption_single_group_wording():
    """One group uses the singular and explains why no test ran."""
    data = _caption_data().query("genotype == 'WT'")
    caption = charts._plot_caption("Pkd2", ["WT"], data, True)
    assert "across 1 group: WT." in caption
    assert caption.endswith("WT. Statistics need 2 or more groups.")
