/* =====================================================================
   Nihongo — Application (vanilla JS, sans dépendance)
   Modes : Révision SRS, Kana, Vocabulaire, Parler (oral), Écrire, Techniques
   ===================================================================== */

(function () {
  "use strict";

  const KANA_GROUPS = window.KANA_GROUPS;
  const VOCAB = window.VOCAB;
  const VOCAB_THEMES = window.VOCAB_THEMES;

  const app = document.getElementById("app");
  const backBtn = document.getElementById("backBtn");
  const brandBtn = document.getElementById("brandBtn");
  const streakBadge = document.getElementById("streakBadge");
  const resetBtn = document.getElementById("resetBtn");

  /* ----------------------- Suivi quotidien / série ----------------------- */
  const DKEY = "nihongo:daily:v1";
  function dstr(d) { return d.toISOString().slice(0, 10); }
  let daily = (function () {
    try { return JSON.parse(localStorage.getItem(DKEY)) || {}; } catch (e) { return {}; }
  })();
  function saveDaily() { try { localStorage.setItem(DKEY, JSON.stringify(daily)); } catch (e) {} }
  function recordReview() {
    const today = dstr(new Date());
    if (daily.today !== today) { daily.today = today; daily.count = 0; }
    if (!daily.count) {
      const y = dstr(new Date(Date.now() - 864e5));
      daily.streak = daily.last === y ? (daily.streak || 0) + 1 : 1;
      daily.last = today;
    }
    daily.count = (daily.count || 0) + 1;
    daily.total = (daily.total || 0) + 1;
    saveDaily();
    updateStreak();
  }
  function todayCount() {
    return daily.today === dstr(new Date()) ? (daily.count || 0) : 0;
  }
  function updateStreak() { streakBadge.textContent = "🔥 " + (daily.streak || 0); }

  /* ----------------------- Utilitaires ----------------------- */
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function el(tag, cls) { const e = document.createElement(tag); if (cls) e.className = cls; return e; }
  function stat(num, lbl) {
    const s = el("div", "stat");
    s.innerHTML = '<div class="num">' + num + '</div><div class="lbl">' + lbl + "</div>";
    return s;
  }

  /* ----------------------- Construction des decks ----------------------- */
  // Item unifié : { id, type, k, r, ... }
  function kanaItems(groupKeys) {
    const items = [];
    KANA_GROUPS.forEach((g) => {
      if (!groupKeys || groupKeys.includes(g.key)) {
        g.data.forEach((c) => items.push({
          id: "k:" + c.k, type: "kana", k: c.k, r: c.r, m: c.m || "", group: g.key,
        }));
      }
    });
    return items;
  }
  function vocabItems(themeKeys) {
    return VOCAB
      .filter((v) => !themeKeys || themeKeys.includes(v.theme))
      .map((v) => ({ id: "v:" + v.jp, type: "vocab", v: v }));
  }
  function allItems() { return kanaItems().concat(vocabItems()); }

  /* ----------------------- Voix ----------------------- */
  function speakItem(item, rate) {
    if (item.type === "kana") window.Speech.speak(item.k, { rate: rate });
    else window.Speech.speak(item.v.kana, { rate: rate });
  }
  function audioButtons(item) {
    const row = el("div", "audio-row");
    if (!window.Speech.ttsSupported()) {
      const w = el("div", "note");
      w.textContent = "🔇 Synthèse vocale indisponible sur ce navigateur.";
      row.appendChild(w);
      return row;
    }
    const play = el("button", "btn secondary");
    play.style.width = "auto";
    play.textContent = "🔊 Écouter";
    play.addEventListener("click", () => speakItem(item, 0.9));
    const slow = el("button", "btn secondary");
    slow.style.width = "auto";
    slow.textContent = "🐢 Lentement";
    slow.addEventListener("click", () => speakItem(item, 0.55));
    row.appendChild(play);
    row.appendChild(slow);
    return row;
  }

  /* ----------------------- Navigation ----------------------- */
  let onBack = null;
  function setBack(fn) { onBack = fn; backBtn.classList.toggle("hidden", !fn); }
  backBtn.addEventListener("click", () => { if (onBack) onBack(); });
  brandBtn.addEventListener("click", renderHome);
  resetBtn.addEventListener("click", () => {
    if (confirm("Réinitialiser toute ta progression (SRS, série, statistiques) ?")) {
      window.SRS.reset();
      daily = {}; saveDaily(); updateStreak();
      renderHome();
    }
  });

  /* ----------------------- Accueil ----------------------- */
  const TIPS = [
    { ic: "🧠", t: "Répétition espacée : l'app te montre chaque carte juste avant que tu l'oublies. C'est la méthode la plus efficace pour mémoriser durablement." },
    { ic: "🗣️", t: "Shadowing : écoute une phrase et répète-la immédiatement, en imitant le rythme. C'est le secret d'une bonne prononciation." },
    { ic: "✍️", t: "Écrire à la main grave les caractères dans la mémoire bien mieux que les relire." },
    { ic: "🎯", t: "Rappel actif : essaie toujours de répondre AVANT de retourner la carte. L'effort de mémoire renforce l'apprentissage." },
    { ic: "📖", t: "Input compréhensible : apprends les mots dans des phrases, pas isolés. Le contexte fixe le sens." },
  ];

  function renderHome() {
    setBack(null);
    updateStreak();

    const due = window.SRS.dueCount(allItems().map((i) => i.id));
    const tip = TIPS[Math.floor(Math.random() * TIPS.length)];

    const modes = [
      { emoji: "🔁", title: "Révision du jour", badge: "SRS", desc: due ? due + " carte(s) à revoir" : "Tout est à jour ✨", act: startDaily },
      { emoji: "🔤", title: "Kana (lire)", desc: "ひらがな・カタカナ avec mnémoniques", act: () => setupKana("read") },
      { emoji: "📖", title: "Vocabulaire", desc: "Mots & phrases par thème", act: setupVocab },
      { emoji: "🗣️", title: "Parler", badge: "voix", desc: "Shadowing + reconnaissance vocale", act: setupSpeak },
      { emoji: "✍️", title: "Écrire", desc: "Tracer les kana sur l'écran", act: setupWrite },
      { emoji: "💡", title: "Les techniques", desc: "Ce qui se fait de mieux pour apprendre", act: renderTechniques },
    ];

    app.innerHTML = "";
    const wrap = el("div", "fade-in");

    const hero = el("div", "hero");
    hero.innerHTML =
      '<h2>ようこそ <span class="brand-sub">Bienvenue</span></h2>' +
      "<p>Apprends à parler et écrire le japonais — avec les meilleures techniques.</p>";
    wrap.appendChild(hero);

    const stats = el("div", "stats-grid");
    stats.appendChild(stat(String(todayCount()), "Cartes aujourd'hui"));
    stats.appendChild(stat(String(due), "À réviser"));
    stats.appendChild(stat(String(daily.total || 0), "Total révisé"));
    wrap.appendChild(stats);

    const tipBox = el("div", "tip");
    tipBox.innerHTML = '<span class="ic">' + tip.ic + "</span><span>" + tip.t + "</span>";
    wrap.appendChild(tipBox);

    const grid = el("div", "mode-grid");
    modes.forEach((m) => {
      const c = el("button", "mode-card");
      c.innerHTML =
        '<span class="emoji">' + m.emoji + "</span>" +
        '<span><span class="mc-title">' + m.title +
        (m.badge ? '<span class="badge">' + m.badge + "</span>" : "") + "</span>" +
        '<span class="mc-desc">' + m.desc + "</span></span>";
      c.addEventListener("click", m.act);
      grid.appendChild(c);
    });
    wrap.appendChild(grid);

    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  /* ----------------------- Écran de sélection (chips) ----------------------- */
  function setupScreen(opts) {
    // opts : { title, intro, groups:[{key,label,sub}], onStart(selectedKeys) }
    setBack(renderHome);
    const selected = new Set(opts.groups.map((g) => g.key));
    app.innerHTML = "";
    const wrap = el("div", "fade-in");
    const h = el("div", "hero");
    h.innerHTML = "<h2>" + opts.title + "</h2><p>" + opts.intro + "</p>";
    wrap.appendChild(h);

    const chips = el("div", "chips");
    opts.groups.forEach((g) => {
      const chip = el("button", "chip on");
      chip.innerHTML = g.label + (g.sub ? '<span class="c-sub">' + g.sub + "</span>" : "");
      chip.addEventListener("click", () => {
        if (selected.has(g.key)) { selected.delete(g.key); chip.classList.remove("on"); }
        else { selected.add(g.key); chip.classList.add("on"); }
        start.disabled = selected.size === 0;
      });
      chips.appendChild(chip);
    });
    wrap.appendChild(chips);

    const start = el("button", "btn btn-block");
    start.textContent = "Commencer ▶";
    start.addEventListener("click", () => opts.onStart(Array.from(selected)));
    wrap.appendChild(start);

    if (opts.note) {
      const n = el("div", "note");
      n.textContent = opts.note;
      wrap.appendChild(n);
    }
    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  /* ----------------------- Lancement des modes ----------------------- */
  function startDaily() {
    const items = allItems();
    const queue = window.SRS.buildQueue(items.map((i) => i.id), { maxNew: 12 });
    if (!queue.length) {
      flashEmpty("🎉", "Bravo, tout est à jour !", "Reviens plus tard ou explore un autre mode pour apprendre du nouveau.");
      return;
    }
    const map = {}; items.forEach((i) => (map[i.id] = i));
    runFlashcards(queue.map((id) => map[id]), "🔁 Révision du jour");
  }

  function setupKana() {
    setupScreen({
      title: "🔤 Kana", intro: "Choisis les séries à étudier.",
      groups: KANA_GROUPS.map((g) => ({ key: g.key, label: g.label, sub: g.data.length })),
      onStart: (keys) => {
        const items = window.SRS.buildQueue(kanaItems(keys).map((i) => i.id), { maxNew: 15 });
        const all = kanaItems(keys); const map = {}; all.forEach((i) => (map[i.id] = i));
        const deck = items.length ? items.map((id) => map[id]) : shuffle(all);
        runFlashcards(deck, "🔤 Kana");
      },
    });
  }

  function setupVocab() {
    setupScreen({
      title: "📖 Vocabulaire", intro: "Choisis les thèmes à réviser.",
      groups: VOCAB_THEMES.map((t) => ({ key: t.key, label: t.emoji + " " + t.label })),
      onStart: (keys) => {
        const all = vocabItems(keys); const map = {}; all.forEach((i) => (map[i.id] = i));
        const queue = window.SRS.buildQueue(all.map((i) => i.id), { maxNew: 12 });
        const deck = queue.length ? queue.map((id) => map[id]) : shuffle(all);
        runFlashcards(deck, "📖 Vocabulaire");
      },
    });
  }

  function setupSpeak() {
    setupScreen({
      title: "🗣️ Parler", intro: "Écoute, répète (shadowing), puis parle : l'app évalue ta prononciation.",
      groups: VOCAB_THEMES.map((t) => ({ key: t.key, label: t.emoji + " " + t.label })),
      note: window.Speech.sttSupported()
        ? "Astuce : autorise le micro. Fonctionne surtout sur Chrome/Edge avec internet."
        : "⚠️ La reconnaissance vocale n'est pas disponible ici — tu peux quand même écouter et t'entraîner au shadowing.",
      onStart: (keys) => runSpeaking(shuffle(vocabItems(keys)), "🗣️ Parler"),
    });
  }

  function setupWrite() {
    setupScreen({
      title: "✍️ Écrire", intro: "Trace les caractères au doigt ou à la souris.",
      groups: KANA_GROUPS.filter((g) => !/yoon/.test(g.key)).map((g) => ({ key: g.key, label: g.label, sub: g.data.length })),
      onStart: (keys) => runWriting(shuffle(kanaItems(keys)), "✍️ Écrire"),
    });
  }

  function flashEmpty(emoji, title, msg) {
    setBack(renderHome);
    app.innerHTML = "";
    const e = el("div", "empty fade-in");
    e.innerHTML = '<div class="big-emoji">' + emoji + "</div><h2>" + title + "</h2><p>" + msg + "</p>";
    const b = el("button", "btn btn-block");
    b.textContent = "🏠 Accueil";
    b.addEventListener("click", renderHome);
    e.appendChild(b);
    app.appendChild(e);
  }

  /* ===================================================================
     MODE 1 — Cartes SRS (kana + vocabulaire)
     =================================================================== */
  function runFlashcards(deck, title) {
    if (!deck.length) { flashEmpty("🤔", "Rien à réviser", "Choisis au moins une série."); return; }
    let idx = 0, reviewed = 0;
    showCard();

    function showCard() {
      setBack(() => { if (confirm("Quitter la session ?")) renderHome(); });
      const item = deck[idx];
      app.innerHTML = "";
      const wrap = el("div", "fade-in");

      const head = el("div", "quiz-head");
      head.innerHTML = "<span>" + title + "</span><span>" + (idx + 1) + " / " + deck.length + "</span>";
      wrap.appendChild(head);
      const prog = el("div", "progress");
      prog.innerHTML = '<span style="width:' + (idx / deck.length) * 100 + '%"></span>';
      wrap.appendChild(prog);

      const card = el("div", "card jp");
      if (item.type === "kana") {
        card.innerHTML = '<div class="big-kana">' + item.k + "</div>";
      } else {
        card.innerHTML = '<div class="big-word">' + item.v.jp + "</div>";
      }
      const hint = el("div", "hint-tap");
      hint.textContent = "Pense à la réponse… puis appuie pour vérifier";
      card.appendChild(hint);
      wrap.appendChild(card);

      const reveal = el("button", "btn btn-block");
      reveal.textContent = "Afficher la réponse 👁️";
      reveal.addEventListener("click", doReveal);
      wrap.appendChild(reveal);

      app.appendChild(wrap);
      window.scrollTo(0, 0);

      // Écoute automatique (le clic de navigation autorise l'audio).
      speakItem(item, 0.9);

      function doReveal() {
        reveal.remove();
        hint.remove();
        const ans = el("div", "");
        if (item.type === "kana") {
          ans.innerHTML =
            '<div class="romaji" style="font-size:30px">' + item.r + "</div>" +
            (item.m ? '<div class="mnemo">💡 ' + item.m + "</div>" : "");
        } else {
          const v = item.v;
          ans.innerHTML =
            '<div class="reading">' + v.kana + "</div>" +
            '<div class="romaji">' + v.romaji + "</div>" +
            '<div class="fr">🇫🇷 ' + v.fr + "</div>" +
            '<div class="example"><div class="ex-jp">' + v.ex.jp + "</div>" +
            '<div class="ex-fr">' + v.ex.fr + "</div></div>";
        }
        card.appendChild(ans);
        card.appendChild(audioButtons(item));

        const grades = el("div", "grade-row");
        [
          { g: 0, cls: "again", label: "Encore" },
          { g: 1, cls: "hard", label: "Difficile" },
          { g: 2, cls: "good", label: "Bien" },
          { g: 3, cls: "easy", label: "Facile" },
        ].forEach((b) => {
          const btn = el("button", "grade " + b.cls);
          btn.innerHTML = b.label + '<span class="g-int">' + window.SRS.preview(item.id, b.g) + "</span>";
          btn.addEventListener("click", () => grade(b.g));
          grades.appendChild(btn);
        });
        wrap.appendChild(grades);
        grades.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }

      function grade(g) {
        window.SRS.review(item.id, g);
        recordReview();
        reviewed++;
        // Si "Encore", on remet la carte plus loin dans la file.
        if (g === 0 && deck.length > 1) {
          const reinsert = Math.min(deck.length, idx + 3);
          deck.splice(reinsert, 0, item);
        }
        idx++;
        if (idx < deck.length) showCard();
        else finish();
      }
    }

    function finish() {
      setBack(renderHome);
      app.innerHTML = "";
      const wrap = el("div", "result fade-in");
      wrap.innerHTML =
        '<div class="big-emoji">🎌</div><h2>Session terminée !</h2>' +
        '<div class="score-line">' + reviewed + " carte(s) révisée(s)</div>" +
        '<p class="note">Série actuelle : 🔥 ' + (daily.streak || 0) + " jour(s). Reviens demain pour la garder !</p>";
      const row = el("div", "btn-row");
      const again = el("button", "btn");
      again.textContent = "🔁 Continuer";
      again.addEventListener("click", startDaily);
      const home = el("button", "btn secondary");
      home.textContent = "🏠 Accueil";
      home.addEventListener("click", renderHome);
      row.appendChild(again); row.appendChild(home);
      wrap.appendChild(row);
      app.appendChild(wrap);
      window.scrollTo(0, 0);
    }
  }

  /* ===================================================================
     MODE 2 — Parler (shadowing + reconnaissance vocale)
     =================================================================== */
  function runSpeaking(deck, title) {
    if (!deck.length) { flashEmpty("🤔", "Rien à pratiquer", "Choisis au moins un thème."); return; }
    let idx = 0;
    show();

    function show() {
      setBack(() => { if (confirm("Quitter ?")) renderHome(); });
      const v = deck[idx].v;
      app.innerHTML = "";
      const wrap = el("div", "fade-in");

      const head = el("div", "quiz-head");
      head.innerHTML = "<span>" + title + "</span><span>" + (idx + 1) + " / " + deck.length + "</span>";
      wrap.appendChild(head);

      const card = el("div", "card jp");
      card.innerHTML =
        '<div class="big-word">' + v.jp + "</div>" +
        '<div class="reading">' + v.kana + "</div>" +
        '<div class="romaji">' + v.romaji + "</div>" +
        '<div class="fr">🇫🇷 ' + v.fr + "</div>";
      card.appendChild(audioButtons(deck[idx]));
      wrap.appendChild(card);

      // Reconnaissance vocale
      const micWrap = el("div", "mic-wrap");
      const supported = window.Speech.sttSupported();
      const mic = el("button", "mic-btn");
      mic.textContent = "🎤";
      const heard = el("div", "heard");
      heard.textContent = supported ? "Appuie sur le micro et prononce le mot." : "";
      micWrap.appendChild(mic);
      micWrap.appendChild(heard);

      if (!supported) {
        mic.disabled = true;
        const w = el("div", "warn");
        w.innerHTML = "🎤 Reconnaissance vocale indisponible sur ce navigateur.<br>Pratique le <b>shadowing</b> : écoute (🔊) et répète à voix haute en imitant le rythme.";
        micWrap.appendChild(w);
      } else {
        mic.addEventListener("click", () => {
          heard.textContent = "🎙️ J'écoute…";
          mic.classList.add("listening");
          window.Speech.listen({ timeout: 6000 })
            .then((res) => {
              mic.classList.remove("listening");
              const sc = window.Speech.score(v.kana, res.transcript);
              const cls = sc >= 80 ? "ok" : sc >= 55 ? "mid" : "bad";
              const verdict = sc >= 80 ? "Excellent ! 🎉" : sc >= 55 ? "Pas mal, réessaie 👍" : "À retravailler 💪";
              heard.innerHTML =
                'Tu as dit : <b class="jp">' + (res.transcript || "—") + "</b><br>" +
                '<span class="score-pill ' + cls + '">' + sc + "% — " + verdict + "</span>";
              recordReview();
            })
            .catch((err) => {
              mic.classList.remove("listening");
              heard.textContent = "😕 " + (err.message === "non-supporté" ? "Non supporté" : "Je n'ai pas entendu, réessaie.");
            });
        });
      }
      wrap.appendChild(micWrap);

      const row = el("div", "btn-row");
      const next = el("button", "btn");
      next.textContent = idx + 1 < deck.length ? "Suivant →" : "Terminer 🏁";
      next.addEventListener("click", () => {
        idx++;
        if (idx < deck.length) show();
        else flashEmpty("🎌", "Bien joué !", "Tu as travaillé ta prononciation. La régularité fait tout.");
      });
      const replay = el("button", "btn secondary");
      replay.textContent = "🔊 Réécouter";
      replay.addEventListener("click", () => speakItem(deck[idx], 0.85));
      row.appendChild(replay); row.appendChild(next);
      wrap.appendChild(row);

      app.appendChild(wrap);
      window.scrollTo(0, 0);
      speakItem(deck[idx], 0.85);
    }
  }

  /* ===================================================================
     MODE 3 — Écrire (tracé sur canvas)
     =================================================================== */
  function runWriting(deck, title) {
    if (!deck.length) { flashEmpty("🤔", "Rien à écrire", "Choisis au moins une série."); return; }
    let idx = 0;
    show();

    function show() {
      setBack(() => { if (confirm("Quitter ?")) renderHome(); });
      const item = deck[idx];
      app.innerHTML = "";
      const wrap = el("div", "fade-in");

      const head = el("div", "quiz-head");
      head.innerHTML = "<span>" + title + "</span><span>" + (idx + 1) + " / " + deck.length + "</span>";
      wrap.appendChild(head);

      const sub = el("div", "hero");
      sub.innerHTML = "<h2>" + item.r + "</h2><p>Trace le caractère ci-dessous.</p>";
      wrap.appendChild(sub);

      const cw = el("div", "canvas-wrap");
      const ghost = el("div", "ghostLayer jp");
      ghost.id = "ghostLayer";
      ghost.textContent = item.k;
      const guide = el("div", "grid-guide");
      const canvas = el("canvas");
      canvas.id = "traceCanvas";
      canvas.width = 280; canvas.height = 280;
      cw.appendChild(ghost); cw.appendChild(guide); cw.appendChild(canvas);
      wrap.appendChild(cw);

      // Outils
      const tools = el("div", "audio-row");
      const sound = el("button", "btn secondary"); sound.style.width = "auto";
      sound.textContent = "🔊 Son"; sound.addEventListener("click", () => speakItem(item, 0.85));
      const toggle = el("button", "btn secondary"); toggle.style.width = "auto";
      let modelShown = true;
      toggle.textContent = "👁️ Modèle";
      toggle.addEventListener("click", () => {
        modelShown = !modelShown;
        ghost.style.color = modelShown ? "rgba(255,255,255,0.10)" : "transparent";
        toggle.textContent = modelShown ? "👁️ Modèle" : "🙈 Caché";
      });
      const clear = el("button", "btn secondary"); clear.style.width = "auto";
      clear.textContent = "🧹 Effacer"; clear.addEventListener("click", clearCanvas);
      tools.appendChild(sound); tools.appendChild(toggle); tools.appendChild(clear);
      wrap.appendChild(tools);

      const row = el("div", "btn-row");
      const next = el("button", "btn");
      next.textContent = idx + 1 < deck.length ? "Suivant →" : "Terminer 🏁";
      next.addEventListener("click", () => {
        recordReview();
        idx++;
        if (idx < deck.length) show();
        else flashEmpty("🖌️", "Bravo !", "Écrire à la main, c'est mémoriser pour de bon.");
      });
      row.appendChild(next);
      wrap.appendChild(row);

      const note = el("div", "note");
      note.textContent = "Astuce : trace dans l'ordre naturel des traits, de haut en bas et de gauche à droite.";
      wrap.appendChild(note);

      app.appendChild(wrap);
      window.scrollTo(0, 0);

      // Dessin
      const ctx = canvas.getContext("2d");
      ctx.lineWidth = 12; ctx.lineCap = "round"; ctx.lineJoin = "round";
      ctx.strokeStyle = "#e0245e";
      let drawing = false;
      function pos(e) {
        const r = canvas.getBoundingClientRect();
        const p = e.touches ? e.touches[0] : e;
        return { x: (p.clientX - r.left) * (canvas.width / r.width), y: (p.clientY - r.top) * (canvas.height / r.height) };
      }
      function down(e) { e.preventDefault(); drawing = true; const p = pos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); }
      function move(e) { if (!drawing) return; e.preventDefault(); const p = pos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); }
      function up() { drawing = false; }
      canvas.addEventListener("pointerdown", down);
      canvas.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
      function clearCanvas() { ctx.clearRect(0, 0, canvas.width, canvas.height); }
    }
  }

  /* ===================================================================
     Page — Les techniques
     =================================================================== */
  function renderTechniques() {
    setBack(renderHome);
    app.innerHTML = "";
    const wrap = el("div", "fade-in");
    wrap.innerHTML =
      '<div class="hero"><h2>💡 Ce qui se fait de mieux</h2>' +
      "<p>Les méthodes utilisées dans cette app, et pourquoi elles marchent.</p></div>";

    const techniques = [
      { e: "🧠", t: "Répétition espacée (SRS)", d: "Comme Anki ou WaniKani : chaque carte revient à l'intervalle optimal, juste avant l'oubli. Tu retiens plus, en moins de temps. Utilisée dans « Révision », « Kana » et « Vocabulaire »." },
      { e: "🎯", t: "Rappel actif", d: "Tu essaies de te souvenir AVANT de voir la réponse. Cet effort, même raté, ancre la mémoire bien plus que la relecture passive." },
      { e: "🗣️", t: "Shadowing", d: "Tu écoutes une phrase et la répètes aussitôt, en imitant le rythme et l'intonation. C'est la technique reine pour parler naturellement. Mode « Parler »." },
      { e: "🎤", t: "Reconnaissance vocale", d: "L'app écoute ta prononciation et te donne un score. Un retour immédiat pour corriger ce qui cloche." },
      { e: "✍️", t: "Écriture manuscrite", d: "Tracer les caractères grave leur forme dans la mémoire motrice. Indispensable pour vraiment connaître les kana. Mode « Écrire »." },
      { e: "📖", t: "Input compréhensible (i+1)", d: "Apprendre les mots dans des phrases d'exemple, un cran au-dessus de ton niveau. Le contexte fixe le sens durablement." },
      { e: "🧩", t: "Mnémoniques", d: "Des images mentales rigolotes pour relier la forme d'un kana à son son. Le cerveau adore les histoires." },
      { e: "🔥", t: "Régularité & micro-sessions", d: "10 minutes par jour battent 2 heures le dimanche. La série (🔥) t'encourage à revenir chaque jour." },
    ];
    techniques.forEach((x) => {
      const c = el("div", "tip");
      c.innerHTML = '<span class="ic">' + x.e + "</span><span><b>" + x.t + "</b><br><span style=\"color:var(--muted)\">" + x.d + "</span></span>";
      wrap.appendChild(c);
    });

    const st = el("div", "tip");
    st.innerHTML = '<span class="ic">🚀</span><span><b>Le parcours conseillé</b><br><span style="color:var(--muted)">1) Apprends les hiragana, puis les katakana (mode Kana + Écrire). 2) Enchaîne le vocabulaire de base. 3) Travaille l\'oral chaque jour (Parler). 4) Reviens chaque jour faire ta « Révision du jour ».</span></span>';
    wrap.appendChild(st);

    const home = el("button", "btn btn-block");
    home.textContent = "🏠 Accueil";
    home.addEventListener("click", renderHome);
    wrap.appendChild(home);

    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  /* ----------------------- Démarrage ----------------------- */
  updateStreak();
  renderHome();
})();
