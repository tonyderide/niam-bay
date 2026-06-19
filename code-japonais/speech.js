/* =====================================================================
   Nihongo — Voix : synthèse vocale (TTS) + reconnaissance vocale (STT)
   ---------------------------------------------------------------------
   Utilise l'API Web Speech du navigateur. Aucune clé, aucun serveur.
   - Synthèse : fonctionne sur la plupart des navigateurs modernes.
   - Reconnaissance : surtout Chrome / Edge (et nécessite internet + micro).
   ===================================================================== */

const Speech = (function () {
  "use strict";

  /* ----------------------- Synthèse vocale (TTS) ----------------------- */
  const synth = window.speechSynthesis || null;
  let jaVoice = null;

  function pickVoice() {
    if (!synth) return;
    const voices = synth.getVoices();
    // Préférence : voix japonaise (ja-JP). Sinon, première disponible.
    jaVoice =
      voices.find((v) => /ja[-_]JP/i.test(v.lang)) ||
      voices.find((v) => /^ja/i.test(v.lang)) ||
      null;
  }
  if (synth) {
    pickVoice();
    if (typeof synth.onvoiceschanged !== "undefined") {
      synth.onvoiceschanged = pickVoice;
    }
  }

  function ttsSupported() { return !!synth; }
  function hasJaVoice() { return !!jaVoice; }

  function speak(text, opts) {
    opts = opts || {};
    if (!synth) return false;
    try {
      synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "ja-JP";
      if (jaVoice) u.voice = jaVoice;
      u.rate = opts.rate != null ? opts.rate : 0.9; // un peu plus lent pour apprendre
      u.pitch = opts.pitch != null ? opts.pitch : 1;
      if (opts.onend) u.onend = opts.onend;
      synth.speak(u);
      return true;
    } catch (e) { return false; }
  }

  /* ----------------------- Reconnaissance vocale (STT) ----------------------- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition || null;

  function sttSupported() { return !!SR; }

  // Renvoie une promesse résolue avec { transcript, confidence }.
  function listen(opts) {
    opts = opts || {};
    return new Promise((resolve, reject) => {
      if (!SR) { reject(new Error("non-supporté")); return; }
      const rec = new SR();
      rec.lang = "ja-JP";
      rec.interimResults = false;
      rec.maxAlternatives = 3;
      let done = false;

      rec.onresult = (e) => {
        done = true;
        const res = e.results[0];
        const alts = [];
        for (let i = 0; i < res.length; i++) alts.push(res[i].transcript);
        resolve({ transcript: res[0].transcript, confidence: res[0].confidence, alternatives: alts });
      };
      rec.onerror = (e) => { if (!done) reject(new Error(e.error || "erreur")); };
      rec.onend = () => { if (!done) reject(new Error("aucun son détecté")); };

      if (opts.onstart) rec.onstart = opts.onstart;
      try { rec.start(); } catch (e) { reject(e); }
      // Sécurité : on arrête après quelques secondes.
      setTimeout(() => { try { rec.stop(); } catch (e) {} }, opts.timeout || 6000);
    });
  }

  /* ----------------------- Comparaison / score ----------------------- */
  // Normalise un texte japonais : enlève espaces, ponctuation, particules courantes.
  function normalize(s) {
    return (s || "")
      .replace(/[\s。、！？!?.,「」『』]/g, "")
      .replace(/[ー－]/g, "")
      .trim();
  }

  // Distance de Levenshtein.
  function lev(a, b) {
    const m = a.length, n = b.length;
    if (!m) return n; if (!n) return m;
    const dp = Array.from({ length: m + 1 }, (_, i) => [i].concat(new Array(n).fill(0)));
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    for (let i = 1; i <= m; i++)
      for (let j = 1; j <= n; j++)
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,
          dp[i][j - 1] + 1,
          dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
    return dp[m][n];
  }

  // Score 0..100 entre la cible (kana) et ce qui a été reconnu.
  function score(target, heard) {
    const t = normalize(target);
    const h = normalize(heard);
    if (!t.length) return 0;
    if (t === h) return 100;
    const d = lev(t, h);
    return Math.max(0, Math.round((1 - d / Math.max(t.length, h.length)) * 100));
  }

  return {
    ttsSupported, hasJaVoice, speak,
    sttSupported, listen,
    normalize, score,
  };
})();

window.Speech = Speech;
