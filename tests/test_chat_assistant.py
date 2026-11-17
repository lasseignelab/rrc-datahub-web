"""Tests for components/chat_assistant.py with the Gemini client mocked."""

from types import SimpleNamespace

from google.genai import errors, types

from components import chat_assistant
from db import chat_tools


def _response(
    text: str | None = "", finish_reason=types.FinishReason.STOP, block_reason=None
):
    """Build a minimal Gemini response with one candidate."""
    return SimpleNamespace(
        text=text,
        candidates=[SimpleNamespace(finish_reason=finish_reason)],
        prompt_feedback=(
            SimpleNamespace(block_reason=block_reason) if block_reason else None
        ),
    )


def _install_fake_client(monkeypatch, response=None, error=None):
    """Patch the assistant's client; return the dict of captured kwargs."""
    monkeypatch.setenv(chat_assistant.API_KEY_ENV, "test-key")
    captured = {}

    def generate_content(**kwargs):
        captured.update(kwargs)
        if error:
            raise error
        return response

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    monkeypatch.setattr(chat_assistant, "_get_client", lambda: client)
    return captured


def test_returns_reply_text_and_sends_question_last(monkeypatch):
    """The new question follows the earlier turns, mapped to Gemini roles."""
    captured = _install_fake_client(monkeypatch, _response("Two datasets."))
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]

    reply = chat_assistant.answer_question(history, "Which datasets have females?")

    assert reply == "Two datasets."
    assert captured["model"] == chat_assistant.MODEL
    contents = captured["contents"]
    assert [content.role for content in contents] == ["user", "model", "user"]
    assert contents[-1].parts[0].text == "Which datasets have females?"
    config = captured["config"]
    assert config.tools == chat_assistant.TOOLS
    assert config.system_instruction == chat_assistant.SYSTEM_PROMPT


def test_history_is_trimmed_and_starts_with_user(monkeypatch):
    """Old turns are dropped and a leading assistant turn is removed."""
    captured = _install_fake_client(monkeypatch, _response("ok"))
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"}
        for i in range(chat_assistant.MAX_HISTORY_MESSAGES + 5)
    ]

    chat_assistant.answer_question(history, "next")

    contents = captured["contents"]
    assert contents[0].role == "user"
    assert len(contents) <= chat_assistant.MAX_HISTORY_MESSAGES + 1


def test_blocked_reply_returns_polite_message(monkeypatch):
    """A safety-blocked reply is not shown as an empty answer."""
    _install_fake_client(
        monkeypatch, _response("", finish_reason=types.FinishReason.SAFETY)
    )
    assert (
        chat_assistant.answer_question([], "off-topic")
        == chat_assistant.BLOCKED_MESSAGE
    )


def test_empty_reply_asks_for_narrower_question(monkeypatch):
    """Running out of tool calls without an answer gives a helpful message."""
    _install_fake_client(monkeypatch, _response(None))
    assert (
        chat_assistant.answer_question([], "everything?")
        == chat_assistant.INCOMPLETE_MESSAGE
    )


def test_quota_error_reports_busy(monkeypatch):
    """A free-tier quota (429) error tells the user to try again later."""
    error = errors.ClientError(
        429, {"error": {"code": 429, "message": "Quota exceeded"}}
    )
    _install_fake_client(monkeypatch, error=error)
    assert chat_assistant.answer_question([], "Which?") == chat_assistant.BUSY_MESSAGE


def test_invalid_key_reports_not_configured(monkeypatch):
    """A rejected API key gives a configuration message, not a crash."""
    error = errors.ClientError(
        400, {"error": {"code": 400, "message": "API key not valid."}}
    )
    _install_fake_client(monkeypatch, error=error)
    assert (
        chat_assistant.answer_question([], "Which?")
        == chat_assistant.NOT_CONFIGURED_MESSAGE
    )


def test_network_error_reports_generic_error(monkeypatch):
    """Unexpected failures become a short message instead of a stack trace."""
    _install_fake_client(monkeypatch, error=ConnectionError("down"))
    assert chat_assistant.answer_question([], "Which?") == chat_assistant.ERROR_MESSAGE


def test_missing_key_reports_not_configured_without_calling_api(monkeypatch):
    """With no API key the assistant answers politely instead of crashing."""
    monkeypatch.delenv(chat_assistant.API_KEY_ENV, raising=False)

    def fail():
        raise AssertionError("client should not be created without a key")

    monkeypatch.setattr(chat_assistant, "_get_client", fail)

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.NOT_CONFIGURED_MESSAGE


def test_tools_accept_gemini_style_arguments(monkeypatch):
    """Filter and age models are unpacked into plain values for the DB layer."""
    seen = {}

    def fake_find(filters, min_days, max_days):
        seen["args"] = (filters, min_days, max_days)
        return {"datasets": []}

    monkeypatch.setattr(chat_tools, "find_datasets", fake_find)
    chat_assistant.find_datasets(
        filters=chat_assistant.SampleFilters(sex="female", tissue=""),
        age=chat_assistant.AgeRange(min_days=30),
    )
    assert seen["args"] == ({"sex": "female"}, 30, None)


def test_field_names_match_db_whitelist():
    """The documented field names are exactly the ones the DB layer accepts."""
    assert set(chat_assistant.SAMPLE_FIELD_NAMES) == set(chat_tools.SAMPLE_FIELDS)
    assert set(chat_assistant.SampleFilters.model_fields) == set(
        chat_tools.SAMPLE_FIELDS
    )


def test_build_chart_link_encodes_filters():
    """Chart links are URL-encoded so Markdown links cannot break."""
    url = chat_assistant.build_chart_link(
        [" prjna1 ", "PRJNA2", "prjna1"],
        gene="Pkd1",
        sample_type=["kidney (whole)"],
        min_age_days=30.0,
    )
    assert url == (
        "/charts?gene=Pkd1&datasets=PRJNA1%2CPRJNA2"
        "&sample_type=kidney+%28whole%29&min_age_days=30"
    )
    assert " " not in url and "(" not in url
    assert chat_assistant.build_chart_link([]) == "/charts"


def test_chart_link_tool_uses_age_bounds():
    """The chart_link tool passes its age model through to the URL."""
    result = chat_assistant.chart_link(
        ["PRJNA1"], age=chat_assistant.AgeRange(max_days=60)
    )
    assert result == {"url": "/charts?datasets=PRJNA1&max_age_days=60"}
    assert chat_assistant.chart_link in chat_assistant.TOOLS
