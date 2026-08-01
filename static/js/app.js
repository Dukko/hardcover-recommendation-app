(function () {
  "use strict";

  function initSingleRange(input) {
    if (!input) return;
    var valueEl = document.getElementById(input.id + "-val");
    function update() {
      var pct = ((input.value - input.min) / (input.max - input.min)) * 100;
      input.style.setProperty("--fill", pct + "%");
      if (valueEl) valueEl.textContent = input.value;
    }
    input.addEventListener("input", update);
    update();
  }

  function initDualRange(minInput, maxInput, fillEl) {
    if (!minInput || !maxInput || !fillEl) return;
    var minValEl = document.getElementById(minInput.id + "-val");
    var maxValEl = document.getElementById(maxInput.id + "-val");
    var min = parseFloat(minInput.min);
    var max = parseFloat(minInput.max);
    var range = max - min || 1;

    function update() {
      var minV = parseFloat(minInput.value);
      var maxV = parseFloat(maxInput.value);
      if (minV > maxV) {
        minV = maxV;
        minInput.value = String(minV);
      }
      minInput.max = String(maxV);
      maxInput.min = String(minV);

      var left = ((minV - min) / range) * 100;
      var right = ((maxV - min) / range) * 100;
      fillEl.style.left = left + "%";
      fillEl.style.width = right - left + "%";
      if (minValEl) minValEl.textContent = minV;
      if (maxValEl) maxValEl.textContent = maxV;
    }

    minInput.addEventListener("input", update);
    maxInput.addEventListener("input", update);
    update();
  }

  function initSliders() {
    initSingleRange(document.getElementById("pages"));
    initSingleRange(document.getElementById("min-rating"));
    initDualRange(
      document.getElementById("year-start"),
      document.getElementById("year-end"),
      document.getElementById("year-fill")
    );
  }

  // --- Skew books: up to 3, selected via autocomplete, synced to hidden inputs ---

  var MAX_SKEW_BOOKS = 3;
  var skewBooks = [];

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderSkewChips() {
    var chipsWrap = document.getElementById("skew-chips");
    var hiddenWrap = document.getElementById("skew-hidden-inputs");
    var searchInput = document.getElementById("skew-search");
    if (!chipsWrap || !hiddenWrap) return;

    chipsWrap.innerHTML = skewBooks
      .map(function (title) {
        return (
          '<span class="chip chip-skew">' +
          escapeHtml(title) +
          '<button type="button" aria-label="Remove" onclick="window.removeSkewBook(' +
          JSON.stringify(title) +
          ')">×</button></span>'
        );
      })
      .join("");

    hiddenWrap.innerHTML = skewBooks
      .map(function (title) {
        return '<input type="hidden" name="skew_books" value="' + escapeHtml(title) + '">';
      })
      .join("");

    if (searchInput) {
      var atMax = skewBooks.length >= MAX_SKEW_BOOKS;
      searchInput.disabled = atMax;
      searchInput.placeholder = atMax
        ? "Maximum of " + MAX_SKEW_BOOKS + " reached"
        : "Search your Hardcover library...";
    }
  }

  window.addSkewBook = function (el) {
    var title = el.getAttribute("data-title");
    if (!title || skewBooks.length >= MAX_SKEW_BOOKS || skewBooks.indexOf(title) !== -1) return;
    skewBooks.push(title);
    renderSkewChips();
    var searchInput = document.getElementById("skew-search");
    var suggestions = document.getElementById("skew-suggestions");
    if (searchInput) searchInput.value = "";
    if (suggestions) suggestions.innerHTML = "";
  };

  window.removeSkewBook = function (title) {
    skewBooks = skewBooks.filter(function (t) {
      return t !== title;
    });
    renderSkewChips();
  };

  function initSkewSearchEnter() {
    var searchInput = document.getElementById("skew-search");
    if (!searchInput) return;
    searchInput.addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      var suggestions = document.getElementById("skew-suggestions");
      var first = suggestions && suggestions.querySelector(".autocomplete-item");
      if (first) window.addSkewBook(first);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSliders();
    renderSkewChips();
    initSkewSearchEnter();
  });
})();
