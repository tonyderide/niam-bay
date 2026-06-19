/* =====================================================================
   Code Moto — Logique de l'application (vanilla JS, sans dépendance)
   ===================================================================== */

(function () {
  "use strict";

  const THEMES = window.THEMES;
  const QUESTIONS = window.QUESTIONS;
  const STORE_KEY = "codemoto:v1";

  const app = document.getElementById("app");
  const backBtn = document.getElementById("backBtn");
  const brandBtn = document.getElementById("brandBtn");
  const streakBadge = document.getElementById("streakBadge");
  const resetBtn = document.getElementById("resetBtn");

  /* ----------------------- Stockage local ----------------------- */
  function loadStore() {
    try {
      return JSON.parse(localStorage.getItem(STORE_KEY)) || {};
    } catch (e) {
      return {};
    }
  }
  function saveStore(s) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(s)); } catch (e) {}
  }
  let store = loadStore();
  store.seen = store.seen || {};        // id -> true si correctement répondu au moins une fois
  store.mistakes = store.mistakes || {}; // id -> true si déjà raté
  store.streak = store.streak || 0;
  store.bestExam = store.bestExam || 0;
  store.examsDone = store.examsDone || 0;

  function persist() { saveStore(store); }

  /* ----------------------- Utilitaires ----------------------- */
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function byTheme(key) { return QUESTIONS.filter((q) => q.theme === key); }
  function themeMeta(key) { return THEMES.find((t) => t.key === key); }
  function updateStreakBadge() { streakBadge.textContent = "🔥 " + store.streak; }

  /* ----------------------- Navigation ----------------------- */
  let onBack = null;
  function setBack(fn) {
    onBack = fn;
    backBtn.classList.toggle("hidden", !fn);
  }
  backBtn.addEventListener("click", () => { if (onBack) onBack(); });
  brandBtn.addEventListener("click", renderHome);
  resetBtn.addEventListener("click", () => {
    if (confirm("Réinitialiser toute ta progression (questions vues, erreurs, score) ?")) {
      store = { seen: {}, mistakes: {}, streak: 0, bestExam: 0, examsDone: 0 };
      persist();
      updateStreakBadge();
      renderHome();
    }
  });

  /* ----------------------- Écran d'accueil ----------------------- */
  function renderHome() {
    setBack(null);
    updateStreakBadge();

    const totalQ = QUESTIONS.length;
    const seenCount = Object.keys(store.seen).length;
    const mistakeCount = Object.keys(store.mistakes).length;

    const modes = [
      { emoji: "📚", title: "Apprendre par thème", desc: "Réviser tranquillement, thème par thème", act: renderThemes },
      { emoji: "⚡", title: "Quiz rapide", desc: "10 questions au hasard", act: () => startQuiz(pickRandom(10), "Quiz rapide") },
      { emoji: "📝", title: "Examen blanc", desc: "40 questions comme à l'épreuve", act: () => startQuiz(pickRandom(40), "Examen blanc", true) },
      { emoji: "🔁", title: "Mes erreurs", desc: mistakeCount ? mistakeCount + " question(s) à revoir" : "Aucune erreur pour l'instant", act: startMistakes },
    ];

    app.innerHTML = "";
    const wrap = el("div", "fade-in");

    const hero = el("div", "hero");
    hero.innerHTML =
      "<h2>🏍️ Prêt à réviser ?</h2>" +
      "<p>Apprends le code moto (ETM) simplement, à ton rythme.</p>";
    wrap.appendChild(hero);

    // Statistiques
    const stats = el("div", "stats-grid");
    stats.appendChild(stat(seenCount + "/" + totalQ, "Questions réussies"));
    stats.appendChild(stat(store.bestExam + "%", "Meilleur examen"));
    stats.appendChild(stat(String(store.examsDone), "Examens faits"));
    wrap.appendChild(stats);

    // Modes
    const grid = el("div", "mode-grid");
    modes.forEach((m) => {
      const c = el("button", "mode-card");
      c.innerHTML =
        '<span class="emoji">' + m.emoji + "</span>" +
        '<span><span class="mc-title">' + m.title + "</span>" +
        '<span class="mc-desc">' + m.desc + "</span></span>";
      c.addEventListener("click", m.act);
      grid.appendChild(c);
    });
    wrap.appendChild(grid);

    // Aperçu thèmes
    const st = el("div", "section-title");
    st.textContent = "Les thèmes";
    wrap.appendChild(st);
    wrap.appendChild(buildThemeList());

    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  function pickRandom(n) {
    return shuffle(QUESTIONS).slice(0, Math.min(n, QUESTIONS.length));
  }

  /* ----------------------- Liste des thèmes ----------------------- */
  function buildThemeList() {
    const list = el("div", "theme-list");
    THEMES.forEach((t) => {
      const qs = byTheme(t.key);
      const done = qs.filter((q) => store.seen[q.id]).length;
      const pct = qs.length ? Math.round((done / qs.length) * 100) : 0;

      const row = el("button", "theme-row");
      const info = el("div", "t-info");
      info.innerHTML =
        '<div style="display:flex;align-items:center;gap:8px">' +
        '<span class="t-name">' + t.name + "</span>" +
        '<span class="t-count">' + done + "/" + qs.length + "</span></div>" +
        '<div class="t-bar"><span style="width:' + pct + '%"></span></div>';

      row.innerHTML = '<span class="t-emoji">' + t.emoji + "</span>";
      row.appendChild(info);
      row.addEventListener("click", () =>
        startQuiz(shuffle(qs), t.emoji + " " + t.name)
      );
      list.appendChild(row);
    });
    return list;
  }

  function renderThemes() {
    setBack(renderHome);
    app.innerHTML = "";
    const wrap = el("div", "fade-in");
    const h = el("div", "hero");
    h.innerHTML = "<h2>📚 Apprendre par thème</h2><p>Choisis un thème à réviser.</p>";
    wrap.appendChild(h);
    wrap.appendChild(buildThemeList());
    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  function startMistakes() {
    const ids = Object.keys(store.mistakes).map(Number);
    const qs = QUESTIONS.filter((q) => ids.includes(q.id));
    if (!qs.length) {
      setBack(renderHome);
      app.innerHTML = "";
      const e = el("div", "empty fade-in");
      e.innerHTML =
        '<div class="big-emoji">🎉</div>' +
        "<h2>Aucune erreur à revoir</h2>" +
        "<p>Continue comme ça ! Fais un quiz pour t'entraîner.</p>";
      const b = el("button", "btn");
      b.textContent = "⚡ Quiz rapide";
      b.addEventListener("click", () => startQuiz(pickRandom(10), "Quiz rapide"));
      e.appendChild(b);
      app.appendChild(e);
      return;
    }
    startQuiz(shuffle(qs), "🔁 Mes erreurs");
  }

  /* ----------------------- Moteur de quiz ----------------------- */
  function startQuiz(questions, title, isExam) {
    const session = {
      questions: questions,
      title: title,
      isExam: !!isExam,
      idx: 0,
      correct: 0,
      answeredLog: [], // {q, good}
    };
    renderQuestion(session);
  }

  function renderQuestion(session) {
    setBack(() => {
      if (confirm("Quitter ? Ta progression dans ce quiz sera perdue.")) renderHome();
    });

    const q = session.questions[session.idx];
    const theme = themeMeta(q.theme);
    const total = session.questions.length;
    const num = session.idx + 1;

    app.innerHTML = "";
    const wrap = el("div", "fade-in");

    // En-tête + progression
    const head = el("div", "quiz-head");
    head.innerHTML =
      "<span>" + session.title + "</span>" +
      "<span>Question " + num + " / " + total + "</span>";
    wrap.appendChild(head);

    const prog = el("div", "progress");
    prog.innerHTML = '<span style="width:' + ((num - 1) / total) * 100 + '%"></span>';
    wrap.appendChild(prog);

    const tag = el("div", "q-theme-tag");
    tag.textContent = theme.emoji + " " + theme.name;
    wrap.appendChild(tag);

    if (q.illu) {
      const illu = el("div", "q-illu");
      illu.textContent = q.illu;
      wrap.appendChild(illu);
    }

    const qt = el("h2", "q-text");
    qt.textContent = q.q;
    wrap.appendChild(qt);

    const hint = el("p", "q-hint");
    hint.textContent = q.multi
      ? "Plusieurs réponses possibles — coche toutes les bonnes, puis valide."
      : "Une seule bonne réponse.";
    wrap.appendChild(hint);

    // Réponses (ordre mélangé)
    const order = shuffle(q.answers.map((_, i) => i));
    const selected = new Set();
    let locked = false;

    const answersBox = el("div", "answers");
    const btns = [];
    order.forEach((origIdx, displayIdx) => {
      const a = q.answers[origIdx];
      const b = el("button", "answer");
      const letter = String.fromCharCode(65 + displayIdx);
      b.innerHTML = '<span class="marker">' + letter + "</span><span>" + a.t + "</span>";
      b.dataset.orig = origIdx;
      b.addEventListener("click", () => {
        if (locked) return;
        if (q.multi) {
          if (selected.has(origIdx)) { selected.delete(origIdx); b.classList.remove("selected"); }
          else { selected.add(origIdx); b.classList.add("selected"); }
          validateBtn.disabled = selected.size === 0;
        } else {
          selected.clear();
          selected.add(origIdx);
          reveal();
        }
      });
      btns.push(b);
      answersBox.appendChild(b);
    });
    wrap.appendChild(answersBox);

    // Bouton valider (multi uniquement)
    let validateBtn;
    if (q.multi) {
      validateBtn = el("button", "btn");
      validateBtn.textContent = "Valider";
      validateBtn.disabled = true;
      validateBtn.addEventListener("click", reveal);
      wrap.appendChild(validateBtn);
    }

    app.appendChild(wrap);
    window.scrollTo(0, 0);

    function reveal() {
      if (locked) return;
      locked = true;

      const correctIdx = new Set(q.answers.map((a, i) => (a.ok ? i : -1)).filter((i) => i >= 0));
      let good = selected.size === correctIdx.size;
      selected.forEach((i) => { if (!correctIdx.has(i)) good = false; });

      btns.forEach((b) => {
        const oi = Number(b.dataset.orig);
        b.disabled = true;
        if (correctIdx.has(oi)) b.classList.add("correct");
        else if (selected.has(oi)) b.classList.add("wrong");
      });

      if (validateBtn) validateBtn.classList.add("hidden");

      // Mémorisation
      if (good) {
        session.correct++;
        store.seen[q.id] = true;
        delete store.mistakes[q.id];
        store.streak++;
      } else {
        store.mistakes[q.id] = true;
        store.streak = 0;
      }
      persist();
      updateStreakBadge();
      session.answeredLog.push({ q: q, good: good });

      // Explication
      const ex = el("div", "explain " + (good ? "good" : "bad"));
      ex.innerHTML =
        '<div class="verdict ' + (good ? "good" : "bad") + '">' +
        (good ? "✅ Bonne réponse !" : "❌ Mauvaise réponse") + "</div>" +
        "<p>" + q.explain + "</p>";
      wrap.appendChild(ex);

      const next = el("button", "btn");
      next.textContent = session.idx + 1 < total ? "Question suivante →" : "Voir mon résultat 🏁";
      next.addEventListener("click", () => {
        session.idx++;
        if (session.idx < total) renderQuestion(session);
        else renderResult(session);
      });
      wrap.appendChild(next);
      ex.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  /* ----------------------- Résultat ----------------------- */
  function renderResult(session) {
    setBack(renderHome);
    const total = session.questions.length;
    const score = session.correct;
    const pct = Math.round((score / total) * 100);

    if (session.isExam) {
      store.examsDone++;
      if (pct > store.bestExam) store.bestExam = pct;
      persist();
    }

    // À l'ETM : 35/40 minimum pour réussir (87,5 %). On applique un seuil de 88 %.
    const pass = pct >= 88;
    let emoji, title, msg;
    if (pct >= 95) { emoji = "🏆"; title = "Excellent !"; msg = "Tu maîtrises, prêt(e) pour l'examen !"; }
    else if (pass) { emoji = "🎉"; title = "Réussi !"; msg = "Au-dessus du seuil de l'épreuve. Bravo !"; }
    else if (pct >= 70) { emoji = "💪"; title = "Presque !"; msg = "Encore un petit effort, revois tes erreurs."; }
    else { emoji = "📚"; title = "À retravailler"; msg = "Pas de panique, l'entraînement paie. Continue !"; }

    app.innerHTML = "";
    const wrap = el("div", "result fade-in");
    wrap.innerHTML =
      '<div class="big-emoji">' + emoji + "</div>" +
      "<h2>" + title + "</h2>" +
      '<div class="ring" style="--p:' + pct + '"><span class="pct">' + pct + "%</span></div>" +
      '<div class="score-line">' + score + " / " + total + " bonnes réponses</div>" +
      "<p style=\"color:var(--muted)\">" + msg + "</p>";

    if (session.isExam) {
      const note = el("p", "q-hint");
      note.style.textAlign = "center";
      note.textContent = "À l'épreuve théorique moto, il faut au moins 35 bonnes réponses sur 40 (88 %).";
      wrap.appendChild(note);
    }

    // Boutons d'action
    const row = el("div", "btn-row");
    const retry = el("button", "btn");
    retry.textContent = "🔁 Recommencer";
    retry.addEventListener("click", () =>
      startQuiz(shuffle(session.questions), session.title, session.isExam)
    );
    const home = el("button", "btn secondary");
    home.textContent = "🏠 Accueil";
    home.addEventListener("click", renderHome);
    row.appendChild(retry);
    row.appendChild(home);
    wrap.appendChild(row);

    // Correction des erreurs
    const wrongs = session.answeredLog.filter((l) => !l.good);
    if (wrongs.length) {
      const st = el("div", "section-title");
      st.textContent = "À revoir (" + wrongs.length + ")";
      st.style.textAlign = "left";
      wrap.appendChild(st);
      wrongs.forEach((l) => {
        const good = l.q.answers.filter((a) => a.ok).map((a) => a.t).join(" • ");
        const item = el("div", "review-item");
        item.innerHTML =
          '<div class="ri-q">' + l.q.q + "</div>" +
          '<div class="ri-a">✅ ' + good + "</div>";
        wrap.appendChild(item);
      });
      const revBtn = el("button", "btn secondary");
      revBtn.textContent = "🔁 Rejouer seulement mes erreurs";
      revBtn.addEventListener("click", () =>
        startQuiz(shuffle(wrongs.map((l) => l.q)), "🔁 Mes erreurs")
      );
      wrap.appendChild(revBtn);
    }

    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  /* ----------------------- Helpers DOM ----------------------- */
  function el(tag, cls) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    return e;
  }
  function stat(num, lbl) {
    const s = el("div", "stat");
    s.innerHTML = '<div class="num">' + num + '</div><div class="lbl">' + lbl + "</div>";
    return s;
  }

  /* ----------------------- Démarrage ----------------------- */
  updateStreakBadge();
  renderHome();
})();
