"""Tests for db/chat_tools.py helpers that need no database connection."""

import pytest

from db import chat_tools


def test_field_whitelist_rejects_unknown_columns():
    """Only whitelisted sample fields can be filtered or grouped on."""
    with pytest.raises(ValueError, match="Unknown field 'fastq_ftp'"):
        chat_tools._field("fastq_ftp")


def test_field_whitelist_maps_age_to_raw_text():
    """The model-facing 'age' field is the human-readable age_raw column."""
    assert chat_tools._field("age") is chat_tools.Sample.age_raw


def test_filter_conditions_skip_blank_values():
    """Empty or None filter values add no condition."""
    conditions = chat_tools._filter_conditions(
        {"sex": "female", "tissue": "", "strain": None}
    )
    assert len(conditions) == 1


def test_filter_conditions_reject_unknown_field():
    """A filter on a non-whitelisted field raises instead of being ignored."""
    with pytest.raises(ValueError):
        chat_tools._filter_conditions({"run_hash": "abc"})


def test_age_conditions_only_for_given_bounds():
    """Each supplied age bound adds one overlap condition."""
    assert len(chat_tools._age_conditions(None, None)) == 0
    assert len(chat_tools._age_conditions(10, None)) == 1
    assert len(chat_tools._age_conditions(10, 60)) == 2
