// Scroll to the element named in the URL hash once Dash has rendered it.
// Dash builds page content after load, so a cross-page link such as
// /about#missing-values would otherwise land at the top of the page.
(function () {
  function scrollToHash() {
    var id = decodeURIComponent(window.location.hash.slice(1));
    if (!id) {
      return;
    }
    var attempts = 0;
    var timer = setInterval(function () {
      var target = document.getElementById(id);
      attempts += 1;
      if (target) {
        target.scrollIntoView();
        clearInterval(timer);
      } else if (attempts > 50) {
        clearInterval(timer);
      }
    }, 100);
  }
  window.addEventListener("load", scrollToHash);
  window.addEventListener("hashchange", scrollToHash);
})();
