// Question field of the home-page data chat (#data-chat-input, a textarea in
// components/data_chat.py):
//
// - Grows with its text, one line at first, up to MAX_HEIGHT_PX, then scrolls.
// - Enter asks the question: it sets the data-chat-send store to a fresh
//   timestamp, which starts submit_question() (there is no Ask button).
//   Shift+Enter adds a new line. Enter while an input method is composing
//   text (e.g. Japanese or Chinese) is left alone so it can finish the
//   character.
// - Links the "Press Enter to ask" hint with aria-describedby, which
//   dcc.Textarea has no prop for.
//
// Listeners are attached to the document, so they keep working when Dash
// re-creates the field after navigating between pages.
(function () {
    "use strict";

    var FIELD_ID = "data-chat-input";
    var HINT_ID = "data-chat-input-hint";
    var SEND_STORE_ID = "data-chat-send";
    var MAX_HEIGHT_PX = 200;
    // How long to watch for the server clearing the field after a question
    // is sent, so the box shrinks back to one line.
    var CLEAR_WATCH_MS = 10000;

    function resize(field) {
        // Reset first so the box can shrink as well as grow.
        field.style.height = "auto";
        var height = Math.min(field.scrollHeight + 2, MAX_HEIGHT_PX);
        field.style.height = height + "px";
        field.style.overflowY = field.scrollHeight + 2 > MAX_HEIGHT_PX
            ? "auto" : "hidden";
    }

    // Dash clears the field when the answer request is accepted; that
    // change does not fire an input event, so watch for it briefly.
    function shrinkWhenCleared(field) {
        var started = Date.now();
        var sentValue = field.value;
        var timer = window.setInterval(function () {
            var current = document.getElementById(FIELD_ID);
            if (!current || Date.now() - started > CLEAR_WATCH_MS) {
                window.clearInterval(timer);
                return;
            }
            if (current.value !== sentValue) {
                resize(current);
                window.clearInterval(timer);
            }
        }, 100);
    }

    document.addEventListener("input", function (event) {
        if (event.target && event.target.id === FIELD_ID) {
            resize(event.target);
        }
    });

    document.addEventListener("keydown", function (event) {
        var field = event.target;
        if (!field || field.id !== FIELD_ID || event.key !== "Enter") {
            return;
        }
        if (event.shiftKey || event.isComposing || event.keyCode === 229) {
            return;
        }
        event.preventDefault();
        var clientside = window.dash_clientside;
        if (clientside && clientside.set_props) {
            clientside.set_props(SEND_STORE_ID, {data: Date.now()});
            shrinkWhenCleared(field);
        }
    });

    function linkHint() {
        var field = document.getElementById(FIELD_ID);
        if (field && document.getElementById(HINT_ID) &&
                field.getAttribute("aria-describedby") !== HINT_ID) {
            field.setAttribute("aria-describedby", HINT_ID);
            resize(field);
        }
    }

    function start() {
        new MutationObserver(linkHint).observe(document.body, {
            childList: true,
            subtree: true,
        });
        linkHint();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
