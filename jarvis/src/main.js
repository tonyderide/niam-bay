/**
 * NIAM-BAY JARVIS — Main entry point
 * Connects to Gateway via WebSocket, fallback to demo mode
 */
import { Orb } from './orb.js';
import { AgentManager } from './agents.js';
import gsap from 'gsap';

let orb, agentManager, ws;
let gatewayConnected = false;

// ─── Boot Sequence ───
function bootSequence() {
  return new Promise(resolve => {
    const lines = document.querySelectorAll('.boot-line');
    lines.forEach((line, i) => {
      const delay = parseInt(line.dataset.delay) || i * 300;
      setTimeout(() => {
        gsap.fromTo(line, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.4 });
      }, delay);
    });
    setTimeout(() => {
      const boot = document.getElementById('boot-screen');
      boot.classList.add('fade-out');
      setTimeout(() => {
        boot.style.display = 'none';
        document.getElementById('app').classList.remove('hidden');
        resolve();
      }, 800);
    }, 2800);
  });
}

// ─── Clock ───
function startClock() {
  const el = document.getElementById('clock');
  const update = () => {
    el.textContent = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  update();
  setInterval(update, 1000);
}

// ─── Navigation ───
function initNav() {
  const btns = document.querySelectorAll('.nav-btn');
  const views = { main: null, agents: document.getElementById('agents-view'), trading: document.getElementById('trading-view') };
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      Object.values(views).forEach(v => v?.classList.add('hidden'));
      const v = views[btn.dataset.view];
      if (v) { v.classList.remove('hidden'); gsap.fromTo(v, { opacity: 0 }, { opacity: 1, duration: 0.4 }); }
    });
  });
}

// ─── Messages ───
function addMessage(text, type = 'ai') {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = `msg ${type}`;
  msg.innerHTML = `<span class="msg-prefix">${type === 'user' ? 'TONY' : 'NB'}</span>${text}`;
  container.appendChild(msg);
  container.parentElement.scrollTop = container.parentElement.scrollHeight;
}

// ─── Gateway WebSocket ───
function connectGateway() {
  const indGw = document.getElementById('ind-gateway');
  const indMartin = document.getElementById('ind-martin');

  // Connect via SSL domain
  const wsUrl = `wss://niambay.duckdns.org/ws`;
  try {
    ws = new WebSocket(wsUrl);
  } catch { return fallbackDemo(); }

  ws.onopen = () => {
    gatewayConnected = true;
    indGw.classList.add('active');
    indMartin.classList.add('active');
    console.log('Gateway connected');
  };

  ws.onclose = () => {
    gatewayConnected = false;
    indGw.classList.remove('active');
    console.log('Gateway disconnected, using demo mode');
    // Reconnect after 5s
    setTimeout(connectGateway, 5000);
  };

  ws.onerror = () => {
    fallbackDemo();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleGatewayMessage(data);
  };

  // Fallback after 3s timeout
  setTimeout(() => {
    if (!gatewayConnected) fallbackDemo();
  }, 3000);
}

function fallbackDemo() {
  const indGw = document.getElementById('ind-gateway');
  indGw.classList.remove('active');
  indGw.textContent = 'DEMO';
  document.getElementById('ind-martin').classList.add('active');
  console.log('Running in demo mode');
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
    case 'system':
      console.log('Gateway:', data.text);
      break;
  }
}

// ─── Send message ───
function sendMessage(text) {
  addMessage(text, 'user');

  if (gatewayConnected && ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'chat', text }));
  } else {
    // Demo mode — simulate locally
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

  input.addEventListener('keydown', e => { if (e.key === 'Enter') doSend(); });
  sendBtn.addEventListener('click', doSend);

  let recording = false;
  micBtn.addEventListener('click', () => {
    recording = !recording;
    micBtn.classList.toggle('recording', recording);
    orb.setState(recording ? 'listening' : 'idle');
  });
}

// ─── Demo mode (local simulation) ───
let msgCounter = 0;
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function simulateDemo(text) {
  msgCounter++;
  const s = `-${msgCounter}`;
  const brainId = 'brain' + s;

  agentManager.spawn(brainId, 'CERVEAU', 'brain');
  await sleep(400);
  orb.setState('thinking');
  agentManager.setState(brainId, 'thinking');

  await sleep(800);
  const hasTrade = /trade|grid|martin|btc|sol|dot|short|balance|status/i.test(text);
  const hasSearch = /cherche|search|web|internet|recherche/i.test(text);
  const hasCode = /code|build|create|fix|deploy|lance|agent/i.test(text);
  const subs = [];

  if (hasTrade) { const id = 'trader'+s; agentManager.spawn(id,'TRADING','trading',brainId); subs.push(id); await sleep(300); agentManager.sendMessage(brainId,id,'Analyze'); agentManager.setState(id,'thinking'); }
  if (hasSearch) { const id = 'search'+s; agentManager.spawn(id,'SEARCH','search',brainId); subs.push(id); await sleep(300); agentManager.sendMessage(brainId,id,'Search'); agentManager.setState(id,'thinking'); }
  if (hasCode) { const id = 'code'+s; agentManager.spawn(id,'BUILDER','code',brainId); subs.push(id); await sleep(300); agentManager.sendMessage(brainId,id,'Build'); agentManager.setState(id,'thinking'); }
  if (!subs.length) { const id = 'gen'+s; agentManager.spawn(id,'ANALYSIS','default',brainId); subs.push(id); await sleep(300); agentManager.sendMessage(brainId,id,'Process'); agentManager.setState(id,'thinking'); }

  // Work
  if (subs.length > 1) { for (let i=0; i<subs.length-1; i++) { agentManager.sendMessage(subs[i],subs[i+1],'Context'); await sleep(600); } }
  for (const id of subs) { await sleep(1000); agentManager.setState(id,'active'); agentManager.sendMessage(id,brainId,'Done'); await sleep(500); }

  agentManager.setState(brainId, 'active');
  await sleep(800);
  orb.setState('speaking');

  // Response
  if (hasTrade) addMessage("Grid SHORT BTC active — 0 RT, centre $66,482. Portfolio: $23.31.", 'ai');
  else if (/bonjour|salut|hello/i.test(text)) addMessage("Bonjour Tony.", 'ai');
  else addMessage("Bien reçu. Je traite ta demande.", 'ai');

  await sleep(1500);
  for (const id of subs) { agentManager.setState(id,'done'); await sleep(300); }
  agentManager.setState(brainId, 'done');
  orb.setState('idle');
}

// ─── Trading panel ───
function initTrading() {
  updateTradingPanel(null);
  // Poll Martin every 30s if gateway connected
  setInterval(async () => {
    if (!gatewayConnected) return;
    try {
      const grids = await fetch('https://niambay.duckdns.org/gw/api/martin/active').then(r => r.json());
      const bal = await fetch('https://niambay.duckdns.org/gw/api/martin/balance').then(r => r.json());
      updateTradingPanel({ grids, balance: bal });
    } catch {}
  }, 30000);
}

function updateTradingPanel(data) {
  const gridsList = document.getElementById('grids-list');
  const portfolioEl = document.getElementById('portfolio-detail');
  const portfolioHeader = document.getElementById('portfolio');

  if (!data) {
    // Default
    gridsList.innerHTML = `<div class="grid-item"><span class="pair">BTC/USD</span><span class="mode short">SHORT</span><div class="stats">x5 | $15 | spacing 0.5%<br>RT: 0 | Profit: <span class="profit">$0.00</span></div></div>`;
    portfolioEl.innerHTML = `<div style="font-family:var(--font-mono);font-size:12px;color:var(--text-dim);line-height:2">Portfolio: <span style="color:var(--text-bright)">$23.31</span><br>Dispo: <span style="color:var(--green)">$22.00</span></div>`;
    portfolioHeader.textContent = '$23.31';
    return;
  }

  const grids = Array.isArray(data.grids) ? data.grids : [];
  if (grids.length === 0) {
    gridsList.innerHTML = '<div style="color:var(--text-dim);font-size:12px">Aucune grid active</div>';
  } else {
    gridsList.innerHTML = grids.map(g => {
      const mode = (g.gridMode || 'NEUTRAL').toLowerCase();
      return `<div class="grid-item"><span class="pair">${g.instrument}</span><span class="mode ${mode}">${g.gridMode}</span><div class="stats">x${g.leverage} | $${g.capital} | RT: ${g.completedRoundTrips || 0}</div></div>`;
    }).join('');
  }

  if (data.balance?.accounts?.flex) {
    const acc = data.balance.accounts.flex;
    const pv = acc.portfolioValue?.toFixed(2) || '0';
    const am = acc.availableMargin?.toFixed(2) || '0';
    portfolioEl.innerHTML = `<div style="font-family:var(--font-mono);font-size:12px;color:var(--text-dim);line-height:2">Portfolio: <span style="color:var(--text-bright)">$${pv}</span><br>Dispo: <span style="color:var(--green)">$${am}</span></div>`;
    portfolioHeader.textContent = `$${pv}`;
  }
}

// ─── Init ───
async function main() {
  await bootSequence();

  orb = new Orb(document.getElementById('orb-canvas'));
  agentManager = new AgentManager();

  startClock();
  initNav();
  initInput();
  connectGateway();
  initTrading();

  setTimeout(() => addMessage("Système en ligne. En attente.", 'ai'), 500);

  window.NB = { orb, agentManager, addMessage, sendMessage };
}

main();
