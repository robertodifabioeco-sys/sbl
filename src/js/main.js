(function () {
  "use strict";

  // Menu mobile
  var nav = document.getElementById("nav");
  var openBtn = document.querySelector(".menu-btn");
  var closeBtn = document.querySelector(".nav-close");
  function setMenu(open) {
    if (!nav) return;
    nav.classList.toggle("open", open);
    document.body.classList.toggle("menu-open", open);
    if (openBtn) openBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && closeBtn) closeBtn.focus();
  }
  if (openBtn) openBtn.addEventListener("click", function () { setMenu(true); });
  if (closeBtn) closeBtn.addEventListener("click", function () { setMenu(false); if (openBtn) openBtn.focus(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });

  // Comparsa morbida degli elementi
  var els = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    els.forEach(function (el) { io.observe(el); });
  } else {
    els.forEach(function (el) { el.classList.add("in"); });
  }

  // Filtro e ricerca articoli
  var list = document.getElementById("article-list");
  if (list) {
    var cards = Array.prototype.slice.call(list.querySelectorAll("[data-cat]"));
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
    var input = document.getElementById("q");
    var empty = document.getElementById("empty");
    var count = document.getElementById("count");
    var state = { cat: "all", q: "" };
    var norm = function (s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); };
    var fromHash = decodeURIComponent((location.hash || "").slice(1));
    if (fromHash && chips.some(function (c) { return c.dataset.filter === fromHash; })) state.cat = fromHash;
    function apply() {
      var n = 0;
      cards.forEach(function (c) {
        var ok = (state.cat === "all" || c.dataset.cat === state.cat) && (!state.q || norm(c.dataset.search).indexOf(state.q) !== -1);
        c.hidden = !ok;
        if (ok) n++;
      });
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.filter === state.cat ? "true" : "false"); });
      if (empty) empty.style.display = n ? "none" : "block";
      if (count) count.textContent = n;
      if (window.sblFillGrids) window.sblFillGrids();
    }
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        state.cat = c.dataset.filter;
        history.replaceState(null, "", state.cat === "all" ? location.pathname : "#" + state.cat);
        apply();
      });
    });
    if (input) input.addEventListener("input", function () { state.q = norm(input.value.trim()); apply(); });
    apply();
  }

  // Copia link articolo
  var copy = document.querySelector("[data-copy]");
  if (copy) {
    copy.addEventListener("click", function () {
      var done = function () {
        var m = document.querySelector(".copied");
        if (m) { m.classList.add("show"); setTimeout(function () { m.classList.remove("show"); }, 2000); }
      };
      if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(done, done);
    });
  }
})();
