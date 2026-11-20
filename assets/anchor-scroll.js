// Scroll to (and focus) the element named in the URL hash once Dash has
// rendered it, e.g. About menu links like /about#about-group-methods-and-reuse.
//
// Dash renders pages after navigation, and async components (dcc.Markdown)
// fill in a moment later, pushing content down. So we re-align the target
// each time the page grows, until the layout has been stable for SETTLE_MS,
// MAX_MS has passed, or the user scrolls/clicks/types.
(function () {
  "use strict";

  const SETTLE_MS = 1500;
  const MAX_MS = 8000;
  let active = null; // { focused, stopAt, settleTimer } while aligning

  function hashTarget() {
    const hash = window.location.hash;
    return hash ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
  }

  // True for the About page's first group heading or its first section
  // heading (e.g. #about-group-overview, #overview).
  function isPageStart(target) {
    const firstGroup = document.querySelector(".about-group");
    if (!firstGroup) {
      return false;
    }
    return (
      target === firstGroup.querySelector(".about-group-heading") ||
      target === firstGroup.querySelector(".about-item-heading")
    );
  }

  function stop() {
    if (active) {
      window.clearTimeout(active.settleTimer);
    }
    active = null;
  }

  function align() {
    if (!active) {
      return;
    }
    if (Date.now() > active.stopAt) {
      stop();
      return;
    }
    const target = hashTarget();
    if (!target) {
      return; // Not rendered yet; observers will call again.
    }
    if (isPageStart(target)) {
      // The first section starts right under the page header (title and
      // stat tiles); show the whole top of the page instead of cutting it off.
      window.scrollTo({ top: 0, behavior: "instant" });
    } else {
      target.scrollIntoView({ block: "start" });
    }
    if (!active.focused) {
      // Move keyboard/screen-reader focus to the section (WCAG 2.4.3).
      active.focused = true;
      if (!target.hasAttribute("tabindex")) {
        target.setAttribute("tabindex", "-1");
      }
      target.focus({ preventScroll: true });
    }
    window.clearTimeout(active.settleTimer);
    active.settleTimer = window.setTimeout(stop, SETTLE_MS);
  }

  function start() {
    stop();
    if (!window.location.hash) {
      return;
    }
    active = { focused: false, stopAt: Date.now() + MAX_MS, settleTimer: null };
    window.setTimeout(align, 0);
  }

  // Re-align whenever new content appears or the page changes height.
  new MutationObserver(align).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
  new ResizeObserver(align).observe(document.body);

  // Never fight the user: any interaction after we land ends alignment.
  ["wheel", "touchstart", "keydown", "mousedown"].forEach(function (name) {
    window.addEventListener(
      name,
      function () {
        if (active && active.focused) {
          stop();
        }
      },
      { capture: true, passive: true }
    );
  });

  window.addEventListener("hashchange", start);
  window.addEventListener("popstate", start);
  // Fired by dcc.Link / dbc links after client-side navigation.
  window.addEventListener("_dashprivate_pushstate", start);
  start(); // Direct visit or reload with a hash in the URL.
})();
