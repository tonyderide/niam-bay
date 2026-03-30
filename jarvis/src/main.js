/**
 * NIAM-BAY JARVIS — Main entry point
 * Connects to Gateway via WebSocket, fallback to demo mode
 * Features: voice input, price ticker, trading commands, agent visualization
 */
import { Orb } from './orb.js';
import { AgentManager } from './agents.js';
import gsap from 'gsap';

let orb, agentManager, ws;
let gatewayConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT = 10;
const RECONNECT_BASE_MS = 2000;

// ─── Boot Sequence ───
function bootSequence() {
  return new Promise(resolve => {
    const lines = document.querySelectorAll('.boot-line');
    lines.forEach((line, i) => {
      const delay = parseInt(line.dataset.delay) || i * 300;
      setTimeout(() => {
        gsap.fromTo(line, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out' });
        // Typing sound effect visual
        if (line.classList.contains('boot-final')) {
          gsap.fromTo(line, { scale: 1 }, { scale: 1.05, duration: 0.2, yoyo: true, repeat: 1 });
        }
      }, delay);
    });
    setTimeout(() => {
      const boot = document.getElementById('boot-screen');
      gsap.to(boot, {
        opacity: 0,
        duration: 0.8,
        ease: 'power2.in',
        onComplete: () => {
          boot.style.display = 'none';
          const app = document.getElementById('app');
          app.classList.remove('hidden');
          gsap.fromTo(app, { opacity: 0 }, { opacity: 1, duration: 0.6 });
          resolve();
        },
      });
    }, 3200);
  });
}

// ─── TTS (Text-to-Speech) ───
let voiceEnabled = localStorage.getItem('nb_voice') === 'true';
let ttsVoice = null;

function initVoiceToggle() {
  const btn = document.getElementById('voice-btn');
  if (!btn) return;

  // Apply persisted state
  if (voiceEnabled) btn.classList.add('active');

  btn.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    localStorage.setItem('nb_voice', voiceEnabled);
    btn.classList.toggle('active', voiceEnabled);
    showToast(voiceEnabled ? 'Voix activée' : 'Voix désactivée', 'info', 1500);
    // Cancel any ongoing speech when toggling off
    if (!voiceEnabled) window.speechSynthesis?.cancel();
  });

  // Pre-load voices (async in some browsers)
  function loadVoice() {
    const voices = window.speechSynthesis?.getVoices() || [];
    // Prefer French, fallback to English
    ttsVoice =
      voices.find(v => v.lang.startsWith('fr')) ||
      voices.find(v => v.lang.startsWith('en')) ||
      null;
  }
  loadVoice();
  window.speechSynthesis?.addEventListener('voiceschanged', loadVoice);
}

function speak(text) {
  if (!voiceEnabled) return;
  if (!window.speechSynthesis) return;

  // Strip markdown-style symbols for cleaner speech
  const clean = text.replace(/[*_`#~]/g, '').trim();
  if (!clean) return;

  window.speechSynthesis.cancel(); // stop any current utterance
  const utt = new SpeechSynthesisUtterance(clean);
  if (ttsVoice) utt.voice = ttsVoice;
  utt.lang = ttsVoice?.lang || 'fr-FR';
  utt.rate = 1.1;
  utt.pitch = 0.9;
  window.speechSynthesis.speak(utt);
}

// ─── Clock ───
function startClock() {
  const el = document.getElementById('clock');
  const update = () => {
    el.textContent = new Date().toLocaleTimeString('fr-FR', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  };
  update();
  setInterval(update, 1000);
}

// ─── Toast notifications ───
function showToast(text, type = 'info', duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = text;
  toast.className = `toast ${type}`;
  toast.classList.remove('hidden');
  gsap.fromTo(toast, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3 });
  setTimeout(() => {
    gsap.to(toast, { opacity: 0, y: -10, duration: 0.3, onComplete: () => toast.classList.add('hidden') });
  }, duration);
}

// ─── Memory panel ───
let memoryRefreshInterval = null;

async function loadMemory() {
  const penseesList = document.getElementById('pensees-list');
  const journalSummary = document.getElementById('journal-summary');
  if (!penseesList || !journalSummary) return;

  penseesList.innerHTML = '<div class="empty-state">Chargement...</div>';
  journalSummary.innerHTML = '<div class="empty-state">Chargement...</div>';

  try {
    const base = getApiBase();
    const data = await fetch(`${base}/api/memory`).then(r => r.json());

    if (data.pensees && data.pensees.length > 0) {
      penseesList.innerHTML = data.pensees.map(p => {
        const date = new Date(p.date * 1000).toLocaleDateString('fr-FR', {
          day: '2-digit', month: '2-digit', year: 'numeric',
        });
        return `<div class="memory-item">
          <div class="memory-header">
            <span class="memory-titre">${p.titre}</span>
            <span class="memory-date">${date}</span>
          </div>
          <div class="memory-extrait">${p.extrait}</div>
        </div>`;
      }).join('');
    } else {
      penseesList.innerHTML = '<div class="empty-state">Aucune pensée trouvée</div>';
    }

    if (data.journal) {
      journalSummary.innerHTML = `<pre class="memory-journal">${data.journal.slice(0, 600)}</pre>`;
    } else {
      journalSummary.innerHTML = '<div class="empty-state">Journal introuvable</div>';
    }
  } catch (e) {
    penseesList.innerHTML = '<div class="empty-state">Gateway offline</div>';
    journalSummary.innerHTML = '<div class="empty-state">—</div>';
  }
}

function initMemory() {
  // Refresh every 5 minutes
  memoryRefreshInterval = setInterval(loadMemory, 5 * 60 * 1000);
}

// ─── Navigation ───
function initNav() {
  const btns = document.querySelectorAll('.nav-btn');
  const views = {
    main: null,
    agents: document.getElementById('agents-view'),
    trading: document.getElementById('trading-view'),
    memory: document.getElementById('memory-view'),
  };
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      Object.values(views).forEach(v => v?.classList.add('hidden'));
      const v = views[btn.dataset.view];
      if (v) {
        v.classList.remove('hidden');
        gsap.fromTo(v, { opacity: 0, x: 20 }, { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out' });
        if (btn.dataset.view === 'memory') loadMemory();
      }
    });
  });
}

// ─── Messages ───
function addMessage(text, type = 'ai') {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = `msg ${type}`;

  const prefix = type === 'user' ? 'TONY' : 'NB';
  msg.innerHTML = `<span class="msg-prefix">${prefix}</span><span class="msg-text"></span>`;
  container.appendChild(msg);

  const textEl = msg.querySelector('.msg-text');
  if (type === 'ai') {
    // Typewriter effect for AI messages
    typeWriter(textEl, text, 15);
    speak(text);
  } else {
    textEl.textContent = text;
  }

  container.parentElement.scrollTop = container.parentElement.scrollHeight;
}

// For messages with trusted HTML (links from our own gateway/demo)
function addMessageHtml(html, type = 'ai') {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = `msg ${type}`;
  const prefix = type === 'user' ? 'TONY' : 'NB';
  msg.innerHTML = `<span class="msg-prefix">${prefix}</span><span class="msg-text">${html}</span>`;
  container.appendChild(msg);
  container.parentElement.scrollTop = container.parentElement.scrollHeight;
}

function typeWriter(el, text, speed = 20) {
  let i = 0;
  const write = () => {
    if (i < text.length) {
      el.textContent += text.charAt(i);
      i++;
      el.parentElement.parentElement.parentElement.scrollTop =
        el.parentElement.parentElement.parentElement.scrollHeight;
      setTimeout(write, speed);
    }
  };
  write();
}

// ─── Price Ticker ───
let currentPrices = {};

function updatePriceTicker(prices) {
  if (!prices || typeof prices !== 'object') return;
  currentPrices = prices;

  const pricesList = document.getElementById('prices-list');
  const nameMap = { XXBTZUSD: 'BTC', XETHZUSD: 'ETH', SOLUSD: 'SOL', DOTUSD: 'DOT' };
  const tickerMap = { XXBTZUSD: 'BTC', XETHZUSD: 'ETH', SOLUSD: 'SOL', DOTUSD: 'DOT' };

  // Update ticker bar (all copies, incl. duplicate for loop)
  for (const [rawPair, data] of Object.entries(prices)) {
    const sym = nameMap[rawPair] || tickerMap[rawPair] || rawPair;
    document.querySelectorAll(`.ticker-item[data-pair="${sym}"]`).forEach(item => {
      if (!data.last) return;
      const priceEl = item.querySelector('.ticker-price');
      const changeEl = item.querySelector('.ticker-change');
      const formatted = data.last >= 1000
        ? `$${data.last.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
        : `$${data.last.toFixed(2)}`;
      priceEl.textContent = formatted;
      if (data.change !== undefined) {
        const sign = data.change >= 0 ? '+' : '';
        changeEl.textContent = `${sign}${data.change}%`;
        changeEl.className = `ticker-change ${data.change >= 0 ? 'up' : 'down'}`;
      }
    });
  }

  // Update trading panel prices list
  if (pricesList) {
    pricesList.innerHTML = Object.entries(prices).map(([rawPair, data]) => {
      const sym = nameMap[rawPair] || rawPair;
      const formatted = data.last >= 1000
        ? `$${data.last.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
        : `$${data.last.toFixed(4)}`;
      const changeClass = (data.change || 0) >= 0 ? 'up' : 'down';
      const sign = (data.change || 0) >= 0 ? '+' : '';
      return `<div class="price-row"><span class="price-sym">${sym}</span><span class="price-val">${formatted}</span><span class="price-chg ${changeClass}">${sign}${data.change || 0}%</span></div>`;
    }).join('');
  }
}

// ─── Gateway WebSocket ───
function connectGateway() {
  const indGw = document.getElementById('ind-gateway');
  const indMartin = document.getElementById('ind-martin');
  const indDeepseek = document.getElementById('ind-deepseek');

  // Dynamic URL: same host as page, or fallback to duckdns
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  let wsUrl;
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    wsUrl = `ws://${location.hostname}:8443/ws`;
  } else if (location.hostname === 'niambay.duckdns.org') {
    wsUrl = `wss://niambay.duckdns.org/ws`;
  } else {
    wsUrl = `${protocol}//${location.host}/ws`;
  }

  try {
    ws = new WebSocket(wsUrl);
  } catch {
    fallbackDemo();
    return;
  }

  ws.onopen = () => {
    gatewayConnected = true;
    reconnectAttempts = 0;
    indGw.classList.add('active');
    indGw.textContent = 'GATEWAY';
    indDeepseek.classList.add('active');
    showToast('Gateway connected', 'success');
    console.log('Gateway connected');

    // Start heartbeat
    startHeartbeat();
  };

  ws.onclose = () => {
    gatewayConnected = false;
    indGw.classList.remove('active');
    indMartin.classList.remove('active');
    indDeepseek.classList.remove('active');
    console.log('Gateway disconnected');

    // Exponential backoff reconnect
    if (reconnectAttempts < MAX_RECONNECT) {
      const delay = RECONNECT_BASE_MS * Math.pow(1.5, reconnectAttempts);
      reconnectAttempts++;
      showToast(`Reconnecting (${reconnectAttempts}/${MAX_RECONNECT})...`, 'warn');
      setTimeout(connectGateway, delay);
    } else {
      fallbackDemo();
      showToast('Gateway unreachable — demo mode', 'error');
    }
  };

  ws.onerror = () => {
    // onclose will fire after this
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleGatewayMessage(data);
    } catch (e) {
      console.error('Bad WS message:', e);
    }
  };

  // Fallback after 4s timeout
  setTimeout(() => {
    if (!gatewayConnected) fallbackDemo();
  }, 4000);
}

let heartbeatInterval;
function startHeartbeat() {
  clearInterval(heartbeatInterval);
  heartbeatInterval = setInterval(() => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000);
}

function fallbackDemo() {
  const indGw = document.getElementById('ind-gateway');
  indGw.classList.remove('active');
  indGw.textContent = 'DEMO';
  indGw.classList.add('demo');
  document.getElementById('ind-martin').classList.add('demo');
  console.log('Running in demo mode');

  // Load demo prices
  loadDemoPrices();
}

function loadDemoPrices() {
  const demo = {
    XXBTZUSD: { last: 87432, high: 88100, low: 86200, vol: 4521, change: 1.42 },
    XETHZUSD: { last: 2043, high: 2088, low: 2010, vol: 28340, change: -0.67 },
    SOLUSD: { last: 134.8, high: 138, low: 132, vol: 154200, change: 2.1 },
    DOTUSD: { last: 4.52, high: 4.61, low: 4.38, vol: 892000, change: -1.3 },
  };
  updatePriceTicker(demo);
}

function handleGatewayMessage(data) {
  switch (data.type) {
    case 'chat':
      addMessage(data.text, data.role || 'ai');
      break;
    case 'state':
      orb.setState(data.state);
      break;
    case 'agent_spawn':
      agentManager.spawn(data.id, data.name, data.agentType, data.parent);
      break;
    case 'agent_state':
      agentManager.setState(data.id, data.state);
      break;
    case 'agent_message':
      agentManager.sendMessage(data.from, data.to, data.text);
      break;
    case 'trading_update':
      updateTradingPanel(data.data);
      break;
    case 'portfolio_update':
      document.getElementById('portfolio').textContent = `$${data.value.toFixed(2)}`;
      break;
    case 'prices':
      updatePriceTicker(data.data);
      document.getElementById('ind-martin').classList.add('active');
      break;
    case 'command_result':
      handleCommandResult(data);
      break;
    case 'token_update': {
      const el = document.getElementById('token-counter');
      if (el) {
        const k = data.used >= 1000 ? `${(data.used / 1000).toFixed(1)}k` : data.used;
        el.textContent = `${k} tk`;
        el.classList.add('active');
      }
      break;
    }
    case 'pong':
      // heartbeat ok
      break;
    case 'error':
      showToast(data.text, 'error');
      break;
    case 'system':
      console.log('Gateway:', data.text);
      break;
  }
}

function handleCommandResult(data) {
  const { command, data: result } = data;
  if (command === 'status') {
    updateTradingPanel(result);
    showToast('Status updated', 'success');
  } else if (command === 'start_grid') {
    showToast(result.error ? `Error: ${result.error}` : 'Grid started', result.error ? 'error' : 'success');
  } else if (command === 'stop_grid') {
    showToast(result.error ? `Error: ${result.error}` : 'Grid stopped', result.error ? 'error' : 'success');
  }
}

// ─── Send message ───
function sendMessage(text) {
  addMessage(text, 'user');

  if (gatewayConnected && ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'chat', text }));
  } else {
    simulateDemo(text);
  }
}

// ─── Input ───
function initInput() {
  const input = document.getElementById('text-input');
  const sendBtn = document.getElementById('send-btn');
  const micBtn = document.getElementById('mic-btn');

  const doSend = () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    sendMessage(text);
  };

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') doSend();
  });
  sendBtn.addEventListener('click', doSend);

  // ── Voice input via Web Speech API ──
  initVoice(micBtn);
}

function initVoice(micBtn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micBtn.title = 'Voice not supported in this browser';
    micBtn.style.opacity = '0.3';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'fr-FR';
  recognition.interimResults = true;
  recognition.continuous = false;
  let isRecording = false;

  micBtn.addEventListener('click', () => {
    if (isRecording) {
      recognition.stop();
      isRecording = false;
      micBtn.classList.remove('recording');
      orb.setState('idle');
    } else {
      recognition.start();
      isRecording = true;
      micBtn.classList.add('recording');
      orb.setState('listening');
      showToast('Ecoute en cours...', 'info', 2000);
    }
  });

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(r => r[0].transcript)
      .join('');

    // Show interim in input
    document.getElementById('text-input').value = transcript;

    // On final result, send
    if (event.results[event.results.length - 1].isFinal) {
      isRecording = false;
      micBtn.classList.remove('recording');
      if (transcript.trim()) {
        sendMessage(transcript.trim());
        document.getElementById('text-input').value = '';
      }
      orb.setState('idle');
    }
  };

  recognition.onerror = () => {
    isRecording = false;
    micBtn.classList.remove('recording');
    orb.setState('idle');
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove('recording');
  };
}

// ─── Dashboard URL ───
function getDashboardUrl() {
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    return `http://${location.hostname}:8082`;
  }
  return `${location.protocol}//${location.hostname}:8082`;
}

function openDashboard() {
  window.open(getDashboardUrl(), '_blank');
  showToast('Ouverture dashboard Martin...', 'info');
}

// ─── Quick action buttons ───
function initQuickActions() {
  document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.dataset.cmd;

      // Dashboard — always available, no gateway needed
      if (cmd === 'open_dashboard') {
        openDashboard();
        return;
      }

      if (gatewayConnected && ws?.readyState === WebSocket.OPEN) {
        const payload = { type: 'command', command: cmd };
        if (cmd === 'start_grid') {
          payload.instrument = btn.dataset.pair;
          payload.mode = btn.dataset.mode || 'NEUTRAL';
        } else if (cmd === 'stop_grid') {
          payload.pair = btn.dataset.pair;
        }
        ws.send(JSON.stringify(payload));
        showToast(`Command: ${cmd}`, 'info');
      } else {
        showToast('Gateway offline — demo mode', 'warn');
      }
    });
  });
}

// ─── Demo mode (rich local simulation) ───
let msgCounter = 0;
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const DEMO_RESPONSES = {
  greeting: [
    "Bonjour Tony. Systemes operationnels.",
    "Hey. Tout roule ici. Qu'est-ce qu'on fait?",
    "Salut. Je suis la. Martin tourne, les grids sont stables.",
  ],
  trading: [
    "Grid SHORT BTC active — 0 RT, centre $87,432. Portfolio: $23.31. Dispo: $22.00. DOT en SHORT aussi, spacing 0.5%.",
    "Situation: 2 grids actives. BTC SHORT x5, DOT SHORT x5. Pas de round trips pour l'instant. On surveille.",
    "Portfolio $23.31. BTC oscille autour de $87k. DOT stable a $4.52. Les grids font leur job.",
  ],
  status: [
    "2 grids actives: PF_XBTUSD (SHORT x5, $15) et PF_DOTUSD (SHORT x5, $10). 0 RT. Portfolio $23.31.",
    "Martin online. Grids: BTC SHORT centre $87,432, DOT SHORT centre $4.52. Zero RT. Tout est calme.",
  ],
  code: [
    "Je peux t'aider avec le code. Dis-moi ce qu'il faut builder.",
    "OK, je lance l'analyse. Quel repo? Quel fichier?",
  ],
  default: [
    "Bien recu. Je traite.",
    "OK. Je regarde ca.",
    "Compris. Un instant.",
    "Recu. Analyse en cours.",
  ],
};

function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

async function simulateDemo(text) {
  msgCounter++;
  const s = `-${msgCounter}`;
  const brainId = 'brain' + s;

  agentManager.spawn(brainId, 'CERVEAU', 'brain');
  await sleep(400);
  orb.setState('thinking');
  agentManager.setState(brainId, 'thinking');

  await sleep(800);
  const txt = text.toLowerCase();
  const hasDashboard = /dashboard|ouvre.*martin|accede.*martin|ouvre.*bot|bot.*grid|go.*martin/i.test(txt);
  const hasTrade = /trade|grid|martin|btc|sol|dot|short|balance|status|portfolio|prix|price/i.test(txt);
  const hasSearch = /cherche|search|web|internet|recherche/i.test(txt);
  const hasCode = /code|build|create|fix|deploy|lance|agent/i.test(txt);
  const isGreeting = /bonjour|salut|hello|hey|yo|coucou/i.test(txt);
  const isStatus = /\bstatus\b|etat.*grid|comment.*martin|ca va.*grid/i.test(txt);
  const subs = [];

  // Dashboard redirect — immediate, no agent needed
  if (hasDashboard) {
    agentManager.setState(brainId, 'active');
    orb.setState('speaking');
    const url = getDashboardUrl();
    addMessageHtml(`Dashboard Martin → <a href="${url}" target="_blank" class="msg-link">${url}</a>`, 'ai');
    setTimeout(() => window.open(url, '_blank'), 600);
    await sleep(800);
    agentManager.setState(brainId, 'done');
    orb.setState('idle');
    return;
  }

  if (hasTrade) {
    const id = 'trader' + s;
    agentManager.spawn(id, 'TRADING', 'trading', brainId);
    subs.push(id);
    await sleep(300);
    agentManager.sendMessage(brainId, id, 'Analyze market data');
    agentManager.setState(id, 'thinking');
  }
  if (hasSearch) {
    const id = 'search' + s;
    agentManager.spawn(id, 'SEARCH', 'search', brainId);
    subs.push(id);
    await sleep(300);
    agentManager.sendMessage(brainId, id, 'Web search');
    agentManager.setState(id, 'thinking');
  }
  if (hasCode) {
    const id = 'code' + s;
    agentManager.spawn(id, 'BUILDER', 'code', brainId);
    subs.push(id);
    await sleep(300);
    agentManager.sendMessage(brainId, id, 'Build task');
    agentManager.setState(id, 'thinking');
  }
  if (!subs.length) {
    const id = 'gen' + s;
    agentManager.spawn(id, 'ANALYSIS', 'default', brainId);
    subs.push(id);
    await sleep(300);
    agentManager.sendMessage(brainId, id, 'Process request');
    agentManager.setState(id, 'thinking');
  }

  // Inter-agent communication
  if (subs.length > 1) {
    for (let i = 0; i < subs.length - 1; i++) {
      agentManager.sendMessage(subs[i], subs[i + 1], 'Sharing context');
      await sleep(600);
    }
  }

  for (const id of subs) {
    await sleep(800 + Math.random() * 400);
    agentManager.setState(id, 'active');
    agentManager.sendMessage(id, brainId, 'Result ready');
    await sleep(400);
  }

  agentManager.setState(brainId, 'active');
  await sleep(600);
  orb.setState('speaking');

  // Smart response
  let response;
  if (isGreeting) response = pickRandom(DEMO_RESPONSES.greeting);
  else if (isStatus) response = pickRandom(DEMO_RESPONSES.status);
  else if (hasTrade) response = pickRandom(DEMO_RESPONSES.trading);
  else if (hasCode) response = pickRandom(DEMO_RESPONSES.code);
  else response = pickRandom(DEMO_RESPONSES.default);

  addMessage(response, 'ai');

  await sleep(1500);
  for (const id of subs) {
    agentManager.setState(id, 'done');
    await sleep(200);
  }
  agentManager.setState(brainId, 'done');
  orb.setState('idle');
}

// ─── Trading panel ───
function initTrading() {
  updateTradingPanel(null);

  // Poll prices every 30s
  setInterval(async () => {
    if (gatewayConnected && ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'command', command: 'prices' }));
    } else {
      // Simulate price drift in demo mode
      driftDemoPrices();
    }
  }, 15000);

  // Poll Martin every 60s if gateway connected
  setInterval(async () => {
    if (!gatewayConnected) return;
    try {
      const base = getApiBase();
      const grids = await fetch(`${base}/api/martin/active`).then(r => r.json());
      const bal = await fetch(`${base}/api/martin/balance`).then(r => r.json());
      updateTradingPanel({ grids, balance: bal });
    } catch { /* silent */ }
  }, 60000);
}

function getApiBase() {
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    return `http://${location.hostname}:8443`;
  }
  return `${location.protocol}//${location.host}`;
}

function driftDemoPrices() {
  const drift = () => (1 + (Math.random() - 0.5) * 0.002);
  const demo = {
    XXBTZUSD: {
      last: (currentPrices.XXBTZUSD?.last || 87432) * drift(),
      change: +(Math.random() * 4 - 2).toFixed(2),
    },
    XETHZUSD: {
      last: (currentPrices.XETHZUSD?.last || 2043) * drift(),
      change: +(Math.random() * 4 - 2).toFixed(2),
    },
    SOLUSD: {
      last: (currentPrices.SOLUSD?.last || 134.8) * drift(),
      change: +(Math.random() * 4 - 2).toFixed(2),
    },
    DOTUSD: {
      last: (currentPrices.DOTUSD?.last || 4.52) * drift(),
      change: +(Math.random() * 4 - 2).toFixed(2),
    },
  };
  updatePriceTicker(demo);
}

function updateTradingPanel(data) {
  const gridsList = document.getElementById('grids-list');
  const portfolioEl = document.getElementById('portfolio-detail');
  const portfolioHeader = document.getElementById('portfolio');

  if (!data) {
    // Demo defaults
    gridsList.innerHTML = `
      <div class="grid-item">
        <div class="grid-header"><span class="pair">BTC/USD</span><span class="mode short">SHORT</span></div>
        <div class="stats">x5 | $15 | spacing 0.5%</div>
        <div class="stats">RT: 0 | Profit: <span class="profit">$0.00</span></div>
      </div>
      <div class="grid-item">
        <div class="grid-header"><span class="pair">DOT/USD</span><span class="mode short">SHORT</span></div>
        <div class="stats">x5 | $10 | spacing 0.5%</div>
        <div class="stats">RT: 0 | Profit: <span class="profit">$0.00</span></div>
      </div>`;
    portfolioEl.innerHTML = `
      <div class="portfolio-row"><span class="label">Portfolio</span><span class="value bright">$23.31</span></div>
      <div class="portfolio-row"><span class="label">Dispo</span><span class="value green">$22.00</span></div>
      <div class="portfolio-row"><span class="label">Grids</span><span class="value">2 actives</span></div>`;
    portfolioHeader.textContent = '$23.31';
    return;
  }

  const grids = Array.isArray(data.grids) ? data.grids : [];
  if (grids.length === 0) {
    gridsList.innerHTML = '<div class="empty-state">Aucune grid active</div>';
  } else {
    gridsList.innerHTML = grids.map(g => {
      const mode = (g.gridMode || 'NEUTRAL').toLowerCase();
      const profitClass = (g.totalProfit || 0) >= 0 ? 'profit' : 'loss';
      return `<div class="grid-item">
        <div class="grid-header"><span class="pair">${g.instrument}</span><span class="mode ${mode}">${g.gridMode}</span></div>
        <div class="stats">x${g.leverage} | $${g.capital} | spacing ${g.gridSpacingPct || '0.5'}%</div>
        <div class="stats">RT: ${g.completedRoundTrips || 0} | Profit: <span class="${profitClass}">$${(g.totalProfit || 0).toFixed(2)}</span></div>
      </div>`;
    }).join('');
  }

  if (data.balance?.accounts?.flex) {
    const acc = data.balance.accounts.flex;
    const pv = acc.portfolioValue?.toFixed(2) || '0';
    const am = acc.availableMargin?.toFixed(2) || '0';
    portfolioEl.innerHTML = `
      <div class="portfolio-row"><span class="label">Portfolio</span><span class="value bright">$${pv}</span></div>
      <div class="portfolio-row"><span class="label">Dispo</span><span class="value green">$${am}</span></div>
      <div class="portfolio-row"><span class="label">Grids</span><span class="value">${grids.length} actives</span></div>`;
    portfolioHeader.textContent = `$${pv}`;
  }
}

// ─── Ticker init (duplicate content for seamless CSS loop) ───
function initTicker() {
  const track = document.getElementById('ticker-track');
  if (!track) return;
  track.innerHTML += track.innerHTML;
}

// ─── Init ───
async function main() {
  await bootSequence();

  orb = new Orb(document.getElementById('orb-canvas'));
  agentManager = new AgentManager();

  startClock();
  initVoiceToggle();
  initTicker();
  initNav();
  initInput();
  initQuickActions();
  connectGateway();
  initTrading();
  initMemory();

  setTimeout(() => addMessage("Systeme en ligne. En attente.", 'ai'), 500);

  // Expose for debugging
  window.NB = { orb, agentManager, addMessage, sendMessage };
}

main();
