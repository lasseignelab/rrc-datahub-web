"""Tests for components/chat_assistant.py with the OpenAI client mocked."""

import json
from types import SimpleNamespace

import httpx2
import openai

from components import chat_assistant
from db import chat_tools


def _choice(content=None, tool_calls=None, finish_reason="stop", refusal=None):
    """Build a minimal Chat Completions choice."""
    return SimpleNamespace(
        finish_reason=finish_reason,
        message=SimpleNamespace(
            content=content, tool_calls=tool_calls, refusal=refusal
        ),
    )


def _tool_call(call_id, name, arguments):
    """Build a minimal function tool call with JSON-encoded arguments."""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _install_fake_client(monkeypatch, replies):
    """Patch the client to return `replies` in order (or raise one).

    Returns the list of kwargs each request was made with; messages are
    copied because the assistant keeps appending to the same list.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    requests = []
    remaining = list(replies)

    def create(**kwargs):
        requests.append({**kwargs, "messages": list(kwargs["messages"])})
        reply = remaining.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(choices=[reply])

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(chat_assistant, "_get_client", lambda: client)
    return requests


def _status_error(error_class, status):
    """Build an OpenAI status error as the SDK would raise it."""
    request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx2.Response(status, request=request)
    return error_class("error", response=response, body=None)


def test_returns_reply_text_and_sends_question_last(monkeypatch):
    """The system prompt comes first and the new question last."""
    requests = _install_fake_client(monkeypatch, [_choice("Two datasets.")])
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]

    reply = chat_assistant.answer_question(history, "Which datasets have females?")

    assert reply == "Two datasets."
    sent = requests[0]
    assert sent["model"] == chat_assistant.DEFAULT_MODEL
    assert sent["messages"][0]["role"] == "system"
    assert sent["messages"][-1] == {
        "role": "user",
        "content": "Which datasets have females?",
    }
    assert len(sent["messages"]) == 4


def test_model_can_be_overridden(monkeypatch):
    """OPENAI_MODEL picks a different model without a code change."""
    requests = _install_fake_client(monkeypatch, [_choice("ok")])
    monkeypatch.setenv("OPENAI_MODEL", "some-other-model")

    chat_assistant.answer_question([], "Which datasets?")

    assert requests[0]["model"] == "some-other-model"


def test_history_is_trimmed_and_starts_with_user(monkeypatch):
    """Old turns are dropped and a leading assistant turn is removed."""
    requests = _install_fake_client(monkeypatch, [_choice("ok")])
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"}
        for i in range(chat_assistant.MAX_HISTORY_MESSAGES + 5)
    ]

    chat_assistant.answer_question(history, "next")

    messages = requests[0]["messages"]
    assert messages[1]["role"] == "user"
    assert len(messages) <= chat_assistant.MAX_HISTORY_MESSAGES + 2


def test_tool_calls_are_run_and_results_sent_back(monkeypatch):
    """A tool call is dispatched and its result returned to the model."""
    call = _tool_call("call_1", "chart_link", {"datasets": ["prjna1"], "gene": None})
    requests = _install_fake_client(
        monkeypatch,
        [_choice(tool_calls=[call], finish_reason="tool_calls"), _choice("Done.")],
    )

    reply = chat_assistant.answer_question([], "Plot Pkd1")

    assert reply == "Done."
    follow_up = requests[1]["messages"]
    assert follow_up[-2]["tool_calls"][0]["id"] == "call_1"
    assert follow_up[-1]["role"] == "tool"
    assert follow_up[-1]["tool_call_id"] == "call_1"
    assert json.loads(follow_up[-1]["content"]) == {"url": "/charts?datasets=PRJNA1"}


def test_tool_loop_ends_with_tools_switched_off(monkeypatch):
    """After the last allowed round the model must answer without tools."""
    call = _tool_call("call_1", "chart_link", {"datasets": []})
    looping = [
        _choice(tool_calls=[call], finish_reason="tool_calls")
        for _ in range(chat_assistant.MAX_TOOL_ITERATIONS)
    ]
    requests = _install_fake_client(monkeypatch, looping + [_choice("Final.")])

    reply = chat_assistant.answer_question([], "Search forever")

    assert reply == "Final."
    assert requests[-1]["tool_choice"] == "none"
    assert all(request["tool_choice"] == "auto" for request in requests[:-1])


def test_run_tool_reports_bad_arguments_to_the_model():
    """Bad JSON, unknown tools and unknown arguments become error results."""
    assert "error" in json.loads(chat_assistant.run_tool("chart_link", "{not json"))
    assert "error" in json.loads(chat_assistant.run_tool("drop_tables", "{}"))
    unexpected = chat_assistant.run_tool("chart_link", '{"datasets": [], "x": 1}')
    assert "error" in json.loads(unexpected)


def test_refusal_returns_polite_message(monkeypatch):
    """A refusal is not shown as an empty answer."""
    _install_fake_client(monkeypatch, [_choice(refusal="I can't help with that.")])

    reply = chat_assistant.answer_question([], "something off-topic")

    assert reply == chat_assistant.REFUSAL_MESSAGE


def test_empty_reply_returns_incomplete_message(monkeypatch):
    """An answer with no text tells the user to narrow the question."""
    _install_fake_client(monkeypatch, [_choice("", finish_reason="length")])

    reply = chat_assistant.answer_question([], "Everything about everything")

    assert reply == chat_assistant.INCOMPLETE_MESSAGE


def test_authentication_error_reports_missing_key(monkeypatch):
    """A rejected API key gives a configuration message, not a crash."""
    error = _status_error(openai.AuthenticationError, 401)
    _install_fake_client(monkeypatch, [error])

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.NOT_CONFIGURED_MESSAGE


def test_rate_limit_reports_busy(monkeypatch):
    """Rate limits and exhausted quota ask the user to try again."""
    _install_fake_client(monkeypatch, [_status_error(openai.RateLimitError, 429)])

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.BUSY_MESSAGE


def test_connection_error_reports_unreachable(monkeypatch):
    """A network failure gives a friendly message."""
    request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
    error = openai.APIConnectionError(request=request)
    _install_fake_client(monkeypatch, [error])

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.UNREACHABLE_MESSAGE


def test_missing_key_reports_not_configured_without_calling_api(monkeypatch):
    """With no credentials the assistant answers politely instead of crashing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fail():
        raise AssertionError("client should not be created without a key")

    monkeypatch.setattr(chat_assistant, "_get_client", fail)

    reply = chat_assistant.answer_question([], "Which datasets?")

    assert reply == chat_assistant.NOT_CONFIGURED_MESSAGE


def test_field_names_match_database_whitelist():
    """Tool schemas offer exactly the fields the database layer accepts."""
    assert set(chat_assistant.SAMPLE_FIELD_NAMES) == set(chat_tools.SAMPLE_FIELDS)


def test_every_tool_has_a_function():
    """Each tool offered to the model can be dispatched."""
    names = {tool["function"]["name"] for tool in chat_assistant.TOOLS}
    assert names == set(chat_assistant.TOOL_FUNCTIONS)
    assert "chart_link" in names


def test_build_chart_link_encodes_filters():
    """Chart links are URL-encoded so Markdown links cannot break."""
    url = chat_assistant.build_chart_link(
        [" prjna1 ", "PRJNA2", "prjna1"],
        gene="Pkd1",
        sample_type=["kidney (whole)"],
        min_age_days=30,
    )
    assert url == (
        "/charts?gene=Pkd1&datasets=PRJNA1%2CPRJNA2"
        "&sample_type=kidney+%28whole%29&min_age_days=30"
    )
    assert " " not in url and "(" not in url
    assert chat_assistant.build_chart_link([]) == "/charts"
