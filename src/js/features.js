(function () {
  "use strict";

  // ——— Tendina lingua: la scelta vale per tutto il sito e per le visite successive ———
  var dd = document.querySelector(".lang-dd");
  if (dd) {
    var btn = dd.querySelector(".lang-btn");
    var setOpen = function (o) { dd.classList.toggle("open", o); btn.setAttribute("aria-expanded", o ? "true" : "false"); };
    btn.addEventListener("click", function (e) { e.stopPropagation(); setOpen(!dd.classList.contains("open")); });
    document.addEventListener("click", function (e) { if (!dd.contains(e.target)) setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
    try { localStorage.setItem("sbl-lang", dd.dataset.lang); } catch (e) {}
    dd.querySelectorAll("[data-set-lang]").forEach(function (a) {
      a.addEventListener("click", function () { try { localStorage.setItem("sbl-lang", a.dataset.setLang); } catch (e) {} });
    });
  }

  // ——— Carosello citazioni ———
  document.querySelectorAll("[data-qslider]").forEach(function (sl) {
    var slides = sl.querySelectorAll(".qs-slide"), dots = sl.querySelectorAll(".qs-dots button"), i = 0, timer;
    var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    function go(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle("is-active", k === i); s.setAttribute("aria-hidden", k === i ? "false" : "true"); });
      dots.forEach(function (d, k) { if (k === i) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current"); });
    }
    function auto() { clearInterval(timer); if (!reduce) timer = setInterval(function () { go(i + 1); }, 8000); }
    sl.querySelector(".qs-prev").addEventListener("click", function () { go(i - 1); auto(); });
    sl.querySelector(".qs-next").addEventListener("click", function () { go(i + 1); auto(); });
    dots.forEach(function (d, k) { d.addEventListener("click", function () { go(k); auto(); }); });
    sl.addEventListener("mouseenter", function () { clearInterval(timer); });
    sl.addEventListener("mouseleave", auto);
    auto();
  });

  // ——— Niente buchi nelle griglie: se l'ultima riga resta incompleta, l'ultima card si allarga ———
  function fillGrids() {
    document.querySelectorAll(".cards").forEach(function (g) {
      var cols = getComputedStyle(g).gridTemplateColumns.split(" ").filter(Boolean).length;
      var vis = Array.prototype.filter.call(g.children, function (c) { return !c.hidden; });
      vis.forEach(function (c) { c.classList.remove("wide"); c.style.gridColumn = ""; });
      if (cols < 2 || !vis.length) return;
      var rest = vis.length % cols;
      if (rest === 0) return;
      var last = vis[vis.length - 1];
      last.style.gridColumn = "span " + (cols - rest + 1);
      last.classList.add("wide");
    });
  }
  window.sblFillGrids = fillGrids;
  fillGrids();
  var rt;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(fillGrids, 150); });

  // ——— Bussola politica ———
  var root = document.getElementById("compass");
  var dataEl = document.getElementById("compass-data");
  if (!root || !dataEl) return;
  var D = JSON.parse(dataEl.textContent);
  var Q = D.questions, answers = [], idx = 0, score = null;
  var $ = function (s) { return root.querySelector(s); };

  function show(step) {
    root.querySelectorAll(".cp-step").forEach(function (s) { s.classList.toggle("is-active", s.dataset.step === step); });
    window.scrollTo({ top: root.getBoundingClientRect().top + window.scrollY - 90, behavior: "smooth" });
  }
  function renderQ() {
    var q = $(".cp-question");
    q.textContent = Q[idx].text;
    $(".cp-n").textContent = idx + 1;
    $(".cp-bar i").style.width = (idx / Q.length * 100) + "%";
    root.querySelectorAll(".cp-ans").forEach(function (b) {
      b.classList.toggle("picked", answers[idx] !== undefined && String(answers[idx]) === b.dataset.v);
    });
    $(".cp-back").style.visibility = idx ? "visible" : "hidden";
    q.classList.remove("in"); void q.offsetWidth; q.classList.add("in");
  }
  $(".cp-start").addEventListener("click", function () { idx = 0; answers = []; renderQ(); show("quiz"); });
  root.querySelectorAll(".cp-ans").forEach(function (b) {
    b.addEventListener("click", function () {
      answers[idx] = parseInt(b.dataset.v, 10);
      b.classList.add("picked");
      setTimeout(function () {
        if (idx < Q.length - 1) { idx++; renderQ(); }
        else {
          $(".cp-bar i").style.width = "100%";
          compute();
          show("gate");
          setTimeout(function () { $(".cp-form input[type=email]").focus({ preventScroll: true }); }, 450);
        }
      }, 220);
    });
  });
  $(".cp-back").addEventListener("click", function () { if (idx > 0) { idx--; renderQ(); } });

  function compute() {
    var sx = 0, sy = 0, nx = 0, ny = 0;
    Q.forEach(function (q, k) {
      var v = (answers[k] || 0) * q.sign;
      if (q.axis === "x") { sx += v; nx++; } else { sy += v; ny++; }
    });
    var x = Math.round(sx / (nx * 2) * 100) / 10, y = Math.round(sy / (ny * 2) * 100) / 10; // da -10 a +10
    var key;
    if (Math.abs(x) < 2.5 && Math.abs(y) < 2.5) key = "centrist";
    else if (x >= 0 && y >= 0) key = (x > 5.5 && y > 5.5) ? "libertarian" : "classical";
    else if (x >= 0) key = "conservative";
    else if (y >= 0) key = "progressive";
    else key = "statist";
    score = { x: x, y: y, key: key };
  }

  var form = $(".cp-form");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var email = form.email.value.trim();
    var okMail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email), okPriv = form.privacy.checked;
    root.querySelector('[data-err="email"]').classList.toggle("show", !okMail);
    root.querySelector('[data-err="privacy"]').classList.toggle("show", !okPriv);
    if (!okMail || !okPriv) return;
    var P = D.profiles[score.key];
    send(email, form.newsletter.checked, P.name);
    renderResult(P);
    show("result");
  });

  function send(email, nl, profile) {
    var F = D.form;
    if (!F || !F.action) return;
    var fd = new FormData();
    fd.append(F.email, email);
    fd.append(F.newsletter, nl ? "Si" : "No");
    fd.append(F.result, profile + " (economia " + score.x + ", diritti " + score.y + ")");
    if (F.lang) fd.append(F.lang, D.lang);
    try { fetch(F.action, { method: "POST", mode: "no-cors", body: fd }); } catch (err) {}
  }

  function renderResult(P) {
    $(".cp-profile").textContent = P.name;
    $(".cp-profile-text").textContent = P.text;
    var px = 200 + score.x * 18, py = 200 - score.y * 18;
    var dot = $(".cp-dot");
    dot.style.transition = "none";
    dot.style.transform = "translate(200px, 200px)";
    setTimeout(function () {
      dot.style.transition = "transform 1.3s cubic-bezier(.2,.8,.2,1)";
      dot.style.transform = "translate(" + px + "px, " + py + "px)";
    }, 350);
    root.querySelector('[data-axis="x"]').style.left = (50 + score.x * 5) + "%";
    root.querySelector('[data-axis="y"]').style.left = (50 + score.y * 5) + "%";
    var th = $(".cp-thinker");
    th.querySelector("img").src = P.thinker.img;
    th.querySelector("img").alt = P.thinker.name;
    var h = th.querySelector("h3"); h.innerHTML = "";
    var a = document.createElement("a"); a.href = P.thinker.url; a.textContent = P.thinker.name; h.appendChild(a);
    th.querySelector("blockquote").textContent = D.q_open + P.thinker.quote + D.q_close;
    var ul = $(".cp-books ul"); ul.innerHTML = "";
    P.books.forEach(function (b) {
      var li = document.createElement("li"), t = document.createElement("b"), s = document.createElement("span");
      t.textContent = b.t; s.textContent = b.a; li.appendChild(t); li.appendChild(s); ul.appendChild(li);
    });
    var txt = D.share_text + " " + D.q_open + P.name + D.q_close + ". " + D.share_url;
    var enc = encodeURIComponent;
    root.querySelector('[data-net="whatsapp"]').href = "https://wa.me/?text=" + enc(txt);
    root.querySelector('[data-net="x"]').href = "https://twitter.com/intent/tweet?text=" + enc(txt);
    root.querySelector('[data-net="linkedin"]').href = "https://www.linkedin.com/sharing/share-offsite/?url=" + enc(D.share_url);
  }
  $(".cp-retry").addEventListener("click", function () { idx = 0; answers = []; renderQ(); show("quiz"); });
})();
