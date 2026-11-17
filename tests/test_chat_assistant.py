"""Tests for components/chat_assistant.py with the Anthropic client mocked."""

from types import SimpleNamespace

import anthropic
import httpx2

from components import chat_assistant


class FakeRunner:
    """Stand-in for the SDK tool runner that returns a canned message."""

    def __init__(self, message=None, error=None):
        """Store the message to return or the error to raise."""
        self.message = message
        self.error = error

    def until_done(self):
        """Return the canned final message, or raise the canned error."""
        if self.error:
            raise self.error
        return self.message


def _install_fake_client(monkeypatch, runner):
    """Patch the assistant's client; return the dict of captured kwargs."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = {}

    def tool_runner(**kwargs):
        captured.update(kwargs)
        return runner

    client = SimpleNamespace(
        beta=SimpleNamespace(messages=SimpleNamespace(tool_runner=tool_runner))
    )
    monkeypatch.setattr(chat_assistant, "_get_client", lambda: client)
    return captured


def _message(text, stop_reason="end_turn"):
    """Build a minimal response object with one text block."""
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
    )


def test_returns_reply_text_and_sends_question_last(monkeypatch):
    """The new question is appended after the earlier turns."""
    captured = _install_fake_client(monkeypatch, FakeRunner(_message("Two datasets.")))
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]

    reply = chat_assistant.answer_question(history, "Which datasets have females?")

    assert reply == "Two datasets."
    assert captured["model"] == "claude-opus-5-5"
    assert captured["messages"][-1] == {
        "role": "user",
        "content": "Which datasets have females?",
    }
    assert len(captured["messages"]) == 3


def test_history_is_trimmed_and_starts_with_user(monkeypatch):
    """Old turns are dropped and a leading assistant turn is removed."""
    captured = _install_fake_client(monkeypatch, FakeRunner(_message("ok")))
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"}
        for i in range(chat_assistant.MAX_HISTORY_MESSAGES + 5)
    ]

    chat_assistant.answer_question(history, "next")

    messages = captured["messages"]
    assert messages[0]["role"] == "user"
    assert len(messages) <= chat_assistant.MAX_HISTORY_MESSAGES + 1


def test_refusal_returns_polite_message(monkeypatch):
    """A refusal stop reason is not shown as an empty answer."""
    _install_fake_client(monkeypatch, FakeRunner(_message("", "refusal")))

    reply = chat_assistant.answer_question([], "something off-topic")

    assert reply == "Sorry, I can't help with that question."


def test_authentication_error_reports_missing_key(monkeypatch):
    """A bad or missing API key gives a configuration message, not a crash."""
    response = httpx2.Response(
        401, request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    error = anthropic.AuthenticationError("bad key", response=response, body=None)
    _install_fake_client(monkeypatch, FakeRunner(error=error))

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert "isn't configured" in reply


def test_missing_key_reports_not_configured_without_calling_api(monkeypatch):
    """With no credentials the assistant answers politely instead of crashing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    def fail():
        raise AssertionError("client should not be created without a key")

    monkeypatch.setattr(chat_assistant, "_get_client", fail)

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.NOT_CONFIGURED_MESSAGE


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


def test_chart_link_tool_is_offered():
    """The model is given the chart_link tool to build its links."""
    assert chat_assistant.chart_link in chat_assistant.TOOLS
