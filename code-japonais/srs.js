/* =====================================================================
   Nihongo — Moteur de répétition espacée (SRS)
   ---------------------------------------------------------------------
   Algorithme inspiré de SM-2 (Anki). Chaque carte est identifiée par
   un id unique. On stocke : facilité (ease), intervalle (jours),
   prochaine échéance (due, en ms), répétitions et oublis.

   Notes de qualité :
     0 = "Encore" (raté)      1 = "Difficile"
     2 = "Bien"               3 = "Facile"
   ===================================================================== */

const SRS = (function () {
  "use strict";
  const KEY = "nihongo:srs:v1";
  const DAY = 24 * 60 * 60 * 1000;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch (e) { return {}; }
  }
  function save(db) {
    try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) {}
  }

  let db = load();

  function get(id) { return db[id] || null; }

  function isNew(id) { return !db[id]; }

  // Une carte est "à réviser" si elle est nouvelle ou si son échéance est passée.
  function isDue(id, now) {
    now = now || Date.now();
    const c = db[id];
    if (!c) return true;
    return c.due <= now;
  }

  function dueCount(ids, now) {
    now = now || Date.now();
    let n = 0;
    ids.forEach((id) => { if (isDue(id, now)) n++; });
    return n;
  }

  function newCount(ids) {
    let n = 0;
    ids.forEach((id) => { if (isNew(id)) n++; });
    return n;
  }

  // Met à jour une carte selon la note (0..3) et renvoie le nouvel état.
  function review(id, grade) {
    const now = Date.now();
    let c = db[id] || { ease: 2.5, interval: 0, reps: 0, lapses: 0, due: now };

    if (grade === 0) {
      // Raté : on recommence bientôt, on baisse la facilité.
      c.reps = 0;
      c.lapses++;
      c.ease = Math.max(1.3, c.ease - 0.2);
      c.interval = 0;
      c.due = now + 60 * 1000; // revu dans ~1 min (dans la session)
    } else {
      c.reps++;
      if (c.reps === 1) c.interval = grade === 1 ? 1 : grade === 3 ? 4 : 1;
      else if (c.reps === 2) c.interval = grade === 3 ? 6 : 3;
      else c.interval = Math.round(c.interval * c.ease);

      // Ajustement de la facilité selon la note.
      if (grade === 1) c.ease = Math.max(1.3, c.ease - 0.15);
      else if (grade === 3) c.ease = c.ease + 0.15;
      c.due = now + c.interval * DAY;
    }
    db[id] = c;
    save(db);
    return c;
  }

  // Tri des ids : d'abord les cartes en retard, puis les nouvelles.
  function buildQueue(ids, opts) {
    opts = opts || {};
    const now = Date.now();
    const maxNew = opts.maxNew != null ? opts.maxNew : 12;
    const due = [];
    const fresh = [];
    ids.forEach((id) => {
      if (isNew(id)) fresh.push(id);
      else if (db[id].due <= now) due.push({ id: id, due: db[id].due });
    });
    due.sort((a, b) => a.due - b.due);
    const queue = due.map((d) => d.id).concat(fresh.slice(0, maxNew));
    return queue;
  }

  function reset() { db = {}; save(db); }

  // Prochain intervalle prévisible (pour afficher sur les boutons).
  function preview(id, grade) {
    const c = db[id];
    if (grade === 0) return "1 min";
    if (!c || c.reps === 0) {
      const d = grade === 3 ? 4 : 1;
      return d + " j";
    }
    let interval;
    if (c.reps === 1) interval = grade === 3 ? 6 : 3;
    else interval = Math.round(c.interval * c.ease);
    return interval + " j";
  }

  return { get, isNew, isDue, dueCount, newCount, review, buildQueue, reset, preview };
})();

window.SRS = SRS;
