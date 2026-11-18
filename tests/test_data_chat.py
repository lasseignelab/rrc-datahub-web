"""Tests for the home-page chat box callbacks and layout (components/data_chat.py)."""

import time

from dash import dcc, html, no_update
from dash.testing.wait import until
from selenium.webdriver.common.keys import Keys

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
    history, pending, value, queue = data_chat.submit_question(
        1, None, "  Which genes?  ", [], None, []
    )
    assert history == [{"role": "user", "content": "Which genes?"}]
    assert pending == "Which genes?"
    assert value == ""
    assert queue is no_update


def test_submit_ignores_blank_input():
    """Pressing Enter or Ask with nothing typed does nothing."""
    assert data_chat.submit_question(1, None, "   ", [], None, []) == (
        no_update,
        no_update,
        no_update,
        no_update,
    )


def test_submit_queues_a_question_asked_during_an_answer():
    """Enter while an answer is on its way queues the question and clears it."""
    history, pending, value, queue = data_chat.submit_question(
        None, 2, "Next?", [{"role": "user", "content": "First?"}], "First?", ["A?"]
    )
    assert history is no_update and pending is no_update
    assert value == ""
    assert queue == ["A?", "Next?"]


def test_ask_next_queued_sends_the_oldest_question_after_an_answer():
    """When the answer arrives, the first queued question becomes pending."""
    earlier = [
        {"role": "user", "content": "First?"},
        {"role": "assistant", "content": "One."},
    ]
    history, pending, queue = data_chat.ask_next_queued(
        1, earlier, None, ["Second?", "Third?"]
    )
    assert history == earlier + [{"role": "user", "content": "Second?"}]
    assert pending == "Second?"
    assert queue == ["Third?"]


def test_ask_next_queued_waits_while_an_answer_is_on_its_way():
    """Nothing is sent while a question is still pending or the queue is empty."""
    nothing = (no_update, no_update, no_update)
    assert data_chat.ask_next_queued(1, [], "First?", ["Second?"]) == nothing
    assert data_chat.ask_next_queued(1, [], None, []) == nothing


def test_render_queue_shows_waiting_questions():
    """Queued questions are listed; line and timer are off when there are none."""
    assert data_chat.render_queue([]) == ("", True, True)
    text, hidden, timer_disabled = data_chat.render_queue(["Second?", "Third?"])
    assert hidden is False and timer_disabled is False
    assert "Second?" in text and "Third?" in text


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


def test_answer_pending_always_finishes_the_question(monkeypatch):
    """An unexpected error still clears pending, so the queue keeps moving."""

    def broken_answer(_history, _question):
        raise RuntimeError("database went away")

    monkeypatch.setattr(data_chat, "answer_question", broken_answer)
    history = [{"role": "user", "content": "First?"}]

    new_history, pending = data_chat.answer_pending("First?", history)

    assert new_history[-1] == {"role": "assistant", "content": data_chat.ERROR_REPLY}
    assert pending is None


def test_render_log_hides_empty_log_and_renders_markdown_replies():
    """The log and disclaimer are hidden until used; replies are Markdown."""
    children, class_name, disclaimer_hidden = data_chat.render_log([])
    assert children == []
    assert "data-chat-log-empty" in class_name
    assert disclaimer_hidden is True

    children, class_name, disclaimer_hidden = data_chat.render_log(
        [
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "**A**"},
        ]
    )
    assert len(children) == 2
    assert "data-chat-log-empty" not in class_name
    assert disclaimer_hidden is False
    assert _find_all(children[1], dcc.Markdown)


def test_home_page_renders_chat_box(dash_duo):
    """The chat box replaces the gene search box on the home page."""
    from app import app

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#data-chat-input")
    dash_duo.wait_for_element("#data-chat-submit")
    assert not dash_duo.find_elements("#gene-search-input")


def test_history_is_kept_for_the_tab_but_pending_is_not():
    """The conversation persists per tab; the in-flight flag never does."""
    stores = {
        getattr(store, "id", None): store
        for store in _find_all(data_chat.layout, dcc.Store)
    }
    assert stores["data-chat-history"].storage_type == "session"
    assert getattr(stores["data-chat-pending"], "storage_type", "memory") == "memory"


def test_conversation_survives_a_page_reload(dash_duo, monkeypatch):
    """A reload in the same tab shows the earlier conversation again."""
    from app import app

    monkeypatch.setattr(
        data_chat, "answer_question", lambda history, question: "Saved answer."
    )
    dash_duo.start_server(app)
    # Enter submits the question (n_submit); a click on the button can be
    # intercepted while the page is still laying out.
    dash_duo.wait_for_element("#data-chat-input").send_keys(
        "Which datasets?", Keys.ENTER
    )
    dash_duo.wait_for_contains_text("#data-chat-log", "Saved answer.")

    dash_duo.driver.refresh()

    dash_duo.wait_for_contains_text("#data-chat-log", "Which datasets?")
    dash_duo.wait_for_contains_text("#data-chat-log", "Saved answer.")


# Distance (px) from the top of the log's visible area to the top of the last
# element matching a selector; 0 means it sits at the top of the box.
_OFFSET_IN_LOG_JS = """
var log = document.getElementById("data-chat-log");
var items = log.querySelectorAll(arguments[0]);
var item = items[items.length - 1];
return item.getBoundingClientRect().top - log.getBoundingClientRect().top;
"""


def _ask(dash_duo, question, expected_count):
    """Type a question, press Enter and wait for its answer to be drawn."""
    dash_duo.wait_for_element("#data-chat-input").send_keys(question, Keys.ENTER)
    until(
        lambda: len(dash_duo.find_elements(".data-chat-message")) == expected_count,
        timeout=10,
    )


def _offset_in_log(dash_duo, selector):
    """Return how far below the top of the log box the element sits."""
    return dash_duo.driver.execute_script(_OFFSET_IN_LOG_JS, selector)


def test_long_answer_is_scrolled_to_its_start(dash_duo, monkeypatch):
    """A long new answer is shown from its first line, not its end."""
    from app import app

    long_answer = "\n\n".join(f"Line {number}" for number in range(40))
    monkeypatch.setattr(data_chat, "answer_question", lambda h, q: long_answer)
    dash_duo.start_server(app)

    _ask(dash_duo, "First?", 2)
    _ask(dash_duo, "Second?", 4)

    until(
        lambda: 0 <= _offset_in_log(dash_duo, ".data-chat-assistant") <= 20,
        timeout=5,
    )


def test_newest_question_and_short_answer_are_in_view(dash_duo, monkeypatch):
    """After many short exchanges the newest question and answer are visible."""
    from app import app

    monkeypatch.setattr(data_chat, "answer_question", lambda h, q: f"Answer to {q}")
    dash_duo.start_server(app)

    for number in range(1, 9):
        _ask(dash_duo, f"Question {number}?", number * 2)

    def newest_exchange_visible():
        """True when the last question and answer are both inside the box."""
        return dash_duo.driver.execute_script("""
            var log = document.getElementById("data-chat-log");
            var box = log.getBoundingClientRect();
            var q = log.querySelectorAll(".data-chat-user");
            var a = log.querySelectorAll(".data-chat-assistant");
            var top = q[q.length - 1].getBoundingClientRect().top;
            var bottom = a[a.length - 1].getBoundingClientRect().bottom;
            return log.scrollTop > 0 && top >= box.top && bottom <= box.bottom;
            """)

    until(newest_exchange_visible, timeout=5)


def test_first_answer_scrolls_on_a_slow_browser(dash_duo, monkeypatch):
    """A slow first answer with a Markdown table is still scrolled into view.

    The Markdown component loads on demand and a slow machine draws it late;
    scrolling must wait for the drawn answer, not the Dash update.
    """
    from app import app

    rows = "\n".join(f"| PRJNA{number} | {number} |" for number in range(25))
    answer = f"Several datasets match.\n\n| Dataset | Samples |\n|---|---|\n{rows}"

    def slow_answer(_history, _question):
        time.sleep(1)
        return answer

    monkeypatch.setattr(data_chat, "answer_question", slow_answer)
    dash_duo.start_server(app)
    dash_duo.driver.execute_cdp_cmd("Emulation.setCPUThrottlingRate", {"rate": 6})

    _ask(dash_duo, "Which datasets?", 2)

    until(
        lambda: 0 <= _offset_in_log(dash_duo, ".data-chat-assistant") <= 20,
        timeout=5,
    )


def test_results_come_before_the_question_box():
    """The conversation is shown above the question field, as in a chat."""
    ids_in_order = [
        getattr(child, "id", None) or getattr(child, "className", None)
        for child in data_chat.layout.children
    ]
    assert ids_in_order.index("data-chat-log") < ids_in_order.index("data-chat-form")


def test_answer_keeps_log_and_question_box_on_screen(dash_duo, monkeypatch):
    """After an answer the page shows the log's top and the question field."""
    from app import app

    monkeypatch.setattr(data_chat, "answer_question", lambda h, q: "Short answer.")
    dash_duo.start_server(app)
    dash_duo.driver.set_window_size(1200, 900)

    _ask(dash_duo, "Which datasets?", 2)

    def chat_on_screen():
        """True when the log's top and the input's bottom are in the window."""
        return dash_duo.driver.execute_script("""
            var log = document.getElementById("data-chat-log");
            var input = document.getElementById("data-chat-input");
            return log.getBoundingClientRect().top >= 0
                && input.getBoundingClientRect().bottom <= window.innerHeight;
            """)

    until(chat_on_screen, timeout=5)


def test_disclaimer_sits_right_under_the_answers_and_starts_hidden():
    """The AI disclaimer follows the log directly and is hidden at first."""
    children = data_chat.layout.children
    ids = [getattr(child, "id", None) for child in children]
    log_index = ids.index("data-chat-log")
    assert ids[log_index + 1] == "data-chat-disclaimer"
    assert children[log_index + 1].hidden is True


def test_enter_during_an_answer_is_answered_next(dash_duo, monkeypatch):
    """Typing ahead and pressing Enter while waiting still gets an answer."""
    from app import app

    def slow_answer(_history, question):
        time.sleep(1.5)
        return f"Answer to {question}"

    monkeypatch.setattr(data_chat, "answer_question", slow_answer)
    dash_duo.start_server(app)

    box = dash_duo.wait_for_element("#data-chat-input")
    box.send_keys("First?", Keys.ENTER)
    dash_duo.wait_for_contains_text("#data-chat-log", "First?")
    box.send_keys("Second?", Keys.ENTER)
    dash_duo.wait_for_contains_text("#data-chat-queued", "Second?")

    dash_duo.wait_for_contains_text("#data-chat-log", "Answer to Second?", timeout=10)
    answers = [
        element.text for element in dash_duo.find_elements(".data-chat-assistant")
    ]
    assert [answer.splitlines()[-1] for answer in answers] == [
        "Answer to First?",
        "Answer to Second?",
    ]
    assert not dash_duo.find_element("#data-chat-queued").is_displayed()
