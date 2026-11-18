// Keeps the home-page data chat log (#data-chat-log, components/data_chat.py)
// scrolled to the newest exchange.
//
// The log is a fixed-height scroll box, so without this a new answer lands
// out of sight below its visible area. The newest question is scrolled to
// the top of the box with its answer under it; if the two don't fit together
// the answer's first line is shown instead, so long answers are read from
// the start, not the end.
//
// A MutationObserver is used rather than a Dash callback because the answer's
// Markdown is drawn some time after Dash updates the log (the Markdown
// component loads on demand, and slower machines draw later), so a scroll
// made right after the update measures the old content. Here the scroll runs
// once the new message is actually in the page, and is re-applied while the
// message finishes drawing (tables, links) for a short settle period. Any
// scrolling by the user during that period stops it, so it never fights them.
//
// When a message was just added, the page also scrolls just enough to bring
// the box into view; restoring a saved conversation on page load does not
// move the page. Smooth scrolling is skipped under prefers-reduced-motion,
// and focus is never moved (the log's aria-live region announces replies).
(function () {
    "use strict";

    var LOG_ID = "data-chat-log";
    var SETTLE_MS = 1500;

    var log = null;
    var messageCount = 0;
    var settleUntil = 0;
    var revealPage = false;
    var frameRequested = false;

    function scrollBehavior() {
        var reduceMotion = window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        return reduceMotion ? "auto" : "smooth";
    }

    function lastOf(selector) {
        var items = log.querySelectorAll(selector);
        return items.length ? items[items.length - 1] : null;
    }

    // Scroll position (in the log's own coordinates) that puts the element at
    // the top of the box's visible area.
    function scrollTopFor(element) {
        var padding = parseFloat(window.getComputedStyle(log).paddingTop) || 0;
        return element.getBoundingClientRect().top -
            log.getBoundingClientRect().top + log.scrollTop - padding;
    }

    function applyScroll() {
        frameRequested = false;
        if (!log || !document.body.contains(log)) { return; }
        var newest = lastOf(".data-chat-message");
        if (!newest) { return; }
        var target = lastOf(".data-chat-user") || newest;
        if (log.scrollHeight - scrollTopFor(target) > log.clientHeight) {
            target = newest;
        }
        var behavior = scrollBehavior();
        log.scrollTo({top: scrollTopFor(target), behavior: behavior});
        if (revealPage) {
            log.scrollIntoView({block: "nearest", behavior: behavior});
        }
    }

    function requestScroll() {
        if (!frameRequested) {
            frameRequested = true;
            window.requestAnimationFrame(applyScroll);
        }
    }

    function startSettling(movePage) {
        revealPage = movePage;
        settleUntil = Date.now() + SETTLE_MS;
        requestScroll();
    }

    function onMutation() {
        var current = document.getElementById(LOG_ID);
        if (!current) {
            log = null;
            return;
        }
        var count = current.querySelectorAll(".data-chat-message").length;
        if (current !== log) {
            // The log was just mounted (page load or navigation back to the
            // home page): show the newest exchange, but leave the page alone.
            log = current;
            messageCount = count;
            if (count > 0) { startSettling(false); }
            return;
        }
        if (count > messageCount) {
            messageCount = count;
            startSettling(true);
        } else {
            messageCount = count;
            if (Date.now() < settleUntil) { requestScroll(); }
        }
    }

    // The user taking over the scroll ends the settle period.
    function stopSettling() { settleUntil = 0; }

    function start() {
        new MutationObserver(onMutation).observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true,
        });
        ["wheel", "touchstart", "keydown", "mousedown"].forEach(function (name) {
            window.addEventListener(name, stopSettling, {passive: true});
        });
        onMutation();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
