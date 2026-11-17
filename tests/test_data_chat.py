"""Tests for the home-page chat box callbacks and layout (components/data_chat.py)."""

from dash import dcc, html, no_update

from components import data_chat


def _find_all(node, component_type):
    """Return every component of the given type in a layout tree."""
    found = [node] if isinstance(node, component_type) else []
    children = getattr(node, "children", None)
    if children is None:
        return found
    if not isinstance(children, list):
        children = [children]
    for child in children:
        found.extend(_find_all(child, component_type))
    return found


def test_input_has_associated_label():
    """Accessibility: the chat input has a <label for=...> pointing at it."""
    labels = _find_all(data_chat.layout, html.Label)
    assert [
        label
        for label in labels
        if getattr(label, "htmlFor", None) == "data-chat-input"
    ]


def test_log_and_status_are_announced():
    """Accessibility: replies and progress are exposed to screen readers."""
    divs = {
        getattr(div, "id", None): div for div in _find_all(data_chat.layout, html.Div)
    }
    assert getattr(divs["data-chat-log"], "role", None) == "log"
    assert getattr(divs["data-chat-status"], "role", None) == "status"


def test_submit_appends_question_and_clears_input():
    """A typed question is added to history, marked pending, input cleared."""
    history, pending, value = data_chat.submit_question(
        1, None, "  Which genes?  ", [], None
    )
    assert history == [{"role": "user", "content": "Which genes?"}]
    assert pending == "Which genes?"
    assert value == ""


def test_submit_ignores_blank_and_in_flight_questions():
    """Blank input, or a new question while one is pending, does nothing."""
    assert data_chat.submit_question(1, None, "   ", [], None) == (
        no_update,
        no_update,
        no_update,
    )
    assert data_chat.submit_question(1, None, "Next?", [], "First?") == (
        no_update,
        no_update,
        no_update,
    )


def test_answer_pending_passes_earlier_turns_and_appends_reply(monkeypatch):
    """The pending question is answered with only the prior turns as context."""
    seen = {}

    def fake_answer(history, question):
        seen["history"] = history
        seen["question"] = question
        return "Answer."

    monkeypatch.setattr(data_chat, "answer_question", fake_answer)
    history = [
        {"role": "user", "content": "First?"},
        {"role": "assistant", "content": "One."},
        {"role": "user", "content": "Second?"},
    ]

    new_history, pending = data_chat.answer_pending("Second?", history)

    assert seen["question"] == "Second?"
    assert seen["history"] == history[:-1]
    assert new_history[-1] == {"role": "assistant", "content": "Answer."}
    assert pending is None


def test_render_log_hides_empty_log_and_renders_markdown_replies():
    """The log is hidden until used; assistant replies render as Markdown."""
    children, class_name = data_chat.render_log([])
    assert children == []
    assert "data-chat-log-empty" in class_name

    children, class_name = data_chat.render_log(
        [
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "**A**"},
        ]
    )
    assert len(children) == 2
    assert "data-chat-log-empty" not in class_name
    assert _find_all(children[1], dcc.Markdown)


def test_home_page_renders_chat_box(dash_duo):
    """The chat box replaces the gene search box on the home page."""
    from app import app

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#data-chat-input")
    dash_duo.wait_for_element("#data-chat-submit")
    assert not dash_duo.find_elements("#gene-search-input")
