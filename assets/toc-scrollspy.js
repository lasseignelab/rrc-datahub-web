// About page scroll-spy: marks the sidebar link for the section currently in
// view with aria-current="location" (styled green + bold in style.css).
//
// Accessibility: never moves keyboard focus, never announces changes (no
// live region; screen readers read aria-current when the user reaches the
// link), and only scrolls the sidebar itself, never the page.
(function () {
  "use strict";

  // A section counts as "current" once its heading passes this line
  // (px from the top of the viewport).
  const ACTIVE_LINE_PX = 120;
  // Keys that scroll the page; used to release a clicked link (see below).
  const SCROLL_KEYS = [
    "ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " ",
  ];
  let frameRequested = false;
  // A sidebar link the user clicked stays highlighted until they scroll
  // themselves. Sections near the end of the page can't scroll up to the
  // active line, so position alone would highlight a neighbouring section.
  let pinnedId = null;

  function updateActiveLink() {
    frameRequested = false;
    const toc = document.querySelector(".about-toc");
    if (!toc) {
      return; // Not on the About page.
    }
    const links = Array.from(toc.querySelectorAll(".about-toc-item"));
    if (!links.length) {
      return;
    }

    // Last section heading that has scrolled past the active line.
    let activeId = links[0].getAttribute("href").slice(1);
    links.forEach(function (link) {
      const id = link.getAttribute("href").slice(1);
      const heading = document.getElementById(id);
      if (heading && heading.getBoundingClientRect().top <= ACTIVE_LINE_PX) {
        activeId = id;
      }
    });
    // At the very bottom, the last sections may never reach the line.
    const atBottom =
      window.innerHeight + window.scrollY >=
      document.documentElement.scrollHeight - 2;
    if (atBottom) {
      activeId = links[links.length - 1].getAttribute("href").slice(1);
    }
    if (pinnedId && document.getElementById(pinnedId)) {
      activeId = pinnedId;
    }

    links.forEach(function (link) {
      const isActive = link.getAttribute("href") === "#" + activeId;
      if (isActive) {
        if (link.getAttribute("aria-current") !== "location") {
          link.setAttribute("aria-current", "location");
          keepVisibleInSidebar(toc, link);
        }
      } else if (link.hasAttribute("aria-current")) {
        link.removeAttribute("aria-current");
      }
    });
  }

  // If the sidebar has its own scrollbar (short screens), scroll only the
  // sidebar so the active link stays in view. Instant, no animation.
  function keepVisibleInSidebar(toc, link) {
    if (toc.scrollHeight <= toc.clientHeight) {
      return;
    }
    const tocBox = toc.getBoundingClientRect();
    const linkBox = link.getBoundingClientRect();
    if (linkBox.top < tocBox.top) {
      toc.scrollTop -= tocBox.top - linkBox.top;
    } else if (linkBox.bottom > tocBox.bottom) {
      toc.scrollTop += linkBox.bottom - tocBox.bottom;
    }
  }

  function requestUpdate() {
    if (!frameRequested) {
      frameRequested = true;
      window.requestAnimationFrame(updateActiveLink);
    }
  }

  document.addEventListener("click", function (event) {
    const link = event.target.closest && event.target.closest(".about-toc-item");
    if (link) {
      pinnedId = link.getAttribute("href").slice(1);
      requestUpdate();
    }
  });
  function releasePin() {
    if (pinnedId) {
      pinnedId = null;
      requestUpdate();
    }
  }
  window.addEventListener("wheel", releasePin, { passive: true });
  window.addEventListener("touchmove", releasePin, { passive: true });
  window.addEventListener("keydown", function (event) {
    if (SCROLL_KEYS.indexOf(event.key) !== -1) {
      releasePin();
    }
  });

  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", requestUpdate);
  // Dash renders pages after navigation and fills Markdown in later.
  new MutationObserver(requestUpdate).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
