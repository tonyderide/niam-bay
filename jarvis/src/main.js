/**
 * NIAM-BAY JARVIS — Main entry point
 */
import { Orb } from './orb.js';
import { AgentManager } from './agents.js';
import gsap from 'gsap';

// ─── Boot Sequence ───
function bootSequence() {
  return new Promise(resolve => {
    const lines = document.querySelectorAll('.boot-line');
    lines.forEach((line, i) => {
      const delay = parseInt(line.dataset.delay) || i * 300;
      setTimeout(() => {
        line.style.animationDelay = '0s';
        line.style.animationPlayState = 'running';
        // Add typing effect
        if (i === lines.length - 1) {
          line.classList.add('boot-highlight');
        }
        gsap.fromTo(line, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.4, delay: 0 });
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
  function update() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  update();
  setInterval(update, 1000);
}

// ─── Navigation ───
function initNav() {
  const btns = document.querySelectorAll('.nav-btn');
  const views = {
    main: null,
    agents: document.getElementById('agents-view'),
    trading: document.getElementById('trading-view'),
  };

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const view = btn.dataset.view;
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Hide all views
      Object.values(views).forEach(v => v?.classList.add('hidden'));

      // Show selected
      if (views[view]) {
        views[view].classList.remove('hidden');
        gsap.fromTo(views[view], { opacity: 0 }, { opacity: 1, duration: 0.4 });
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
  msg.innerHTML = `<span class="msg-prefix">${prefix}</span>${text}`;
  container.appendChild(msg);
  container.parentElement.scrollTop = container.parentElement.scrollHeight;
  return msg;
}

// ─── Input handling ───
function initInput(orb, agentManager) {
  const input = document.getElementById('text-input');
  const sendBtn = document.getElementById('send-btn');
  const micBtn = document.getElementById('mic-btn');

  function send() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage(text, 'user');
    orb.setState('thinking');

    // Simulate agent processing
    simulateAgentWork(agentManager, orb, text);
  }

  input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
  sendBtn.addEventListener('click', send);

  // Mic button (placeholder for real STT)
  let recording = false;
  micBtn.addEventListener('click', () => {
    recording = !recording;
    micBtn.classList.toggle('recording', recording);
    if (recording) {
      orb.setState('listening');
    } else {
      orb.setState('idle');
    }
  });
}

// ─── Demo: Simulate agent orchestration ───
let msgCounter = 0;

async function simulateAgentWork(am, orb, userMessage) {
  msgCounter++;
  const suffix = `-${msgCounter}`;

  // Main brain — reuse if already exists and done, else spawn new
  const brainId = 'brain' + suffix;
  am.spawn(brainId, 'CERVEAU', 'brain');
  await sleep(400);

  am._addLog(brainId, 'system', `Processing: "${userMessage}"`);
  am.setState(brainId, 'thinking');
  orb.setState('thinking');

  await sleep(800);

  const hasTrading = /trade|grid|martin|btc|sol|dot|short|balance|portfolio|status/i.test(userMessage);
  const hasSearch = /cherche|find|search|web|internet|recherche/i.test(userMessage);
  const hasCode = /code|build|create|fix|deploy|script|lance|agent/i.test(userMessage);

  const subAgents = [];

  if (hasTrading) {
    const id = 'trader' + suffix;
    am.spawn(id, 'TRADING', 'trading', brainId);
    subAgents.push(id);
    await sleep(300);
    am.sendMessage(brainId, id, 'Analyze market conditions');
    am.setState(id, 'thinking');
  }

  if (hasSearch) {
    const id = 'searcher' + suffix;
    am.spawn(id, 'SEARCH', 'search', brainId);
    subAgents.push(id);
    await sleep(300);
    am.sendMessage(brainId, id, 'Search for relevant information');
    am.setState(id, 'thinking');
  }

  if (hasCode) {
    const id = 'coder' + suffix;
    am.spawn(id, 'BUILDER', 'code', brainId);
    subAgents.push(id);
    await sleep(300);
    am.sendMessage(brainId, id, 'Implement requested changes');
    am.setState(id, 'thinking');
  }

  if (subAgents.length === 0) {
    const id = 'general' + suffix;
    am.spawn(id, 'ANALYSIS', 'default', brainId);
    subAgents.push(id);
    await sleep(300);
    am.sendMessage(brainId, id, 'Process request');
    am.setState(id, 'thinking');
  }

  // Simulate work — agents communicate back and forth
  await sleep(1500);

  // Inter-agent communication (if multiple agents)
  if (subAgents.length > 1) {
    for (let i = 0; i < subAgents.length - 1; i++) {
      am.sendMessage(subAgents[i], subAgents[i + 1], 'Sharing context data');
      await sleep(800);
      am.sendMessage(subAgents[i + 1], subAgents[i], 'Acknowledged');
      await sleep(600);
    }
  }

  // Each agent does work and reports back
  for (let i = 0; i < subAgents.length; i++) {
    const agentId = subAgents[i];
    await sleep(1200);
    am._addLog(agentId, 'system', 'Processing data...');
    await sleep(1000);
    am._addLog(agentId, 'system', 'Analysis complete.');
    am.setState(agentId, 'active');
    am.sendMessage(agentId, brainId, `Results ready`);
    await sleep(800);
  }

  // Brain synthesizes
  am.setState(brainId, 'active');
  am._addLog(brainId, 'system', 'Synthesizing all agent results...');
  await sleep(1200);
  orb.setState('speaking');

  addMessage(generateDemoResponse(userMessage), 'ai');

  await sleep(2000);

  // Agents finish — they stay visible but dimmed (persistent)
  for (const agentId of subAgents) {
    am.setState(agentId, 'done');
    await sleep(400);
  }

  am.setState(brainId, 'done');
  orb.setState('idle');
}

function generateDemoResponse(input) {
  if (/status|grid|martin/i.test(input)) {
    return "Grid SHORT BTC active — 0 RT, centre $66,482. Portfolio: $23.31. Marge dispo: $22.00.";
  }
  if (/balance|portfolio/i.test(input)) {
    return "Portfolio: $23.31 | Disponible: $22.00 | Grid BTC SHORT x5 en cours.";
  }
  if (/bonjour|salut|hello/i.test(input)) {
    return "Bonjour Tony. Grid BTC SHORT tourne. 0 fills pour l'instant, le marché est calme.";
  }
  return "Bien reçu. Je traite ta demande.";
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Gateway connection (placeholder for real WebSocket) ───
function initGateway() {
  const indicator = document.getElementById('ind-gateway');
  const martinInd = document.getElementById('ind-martin');

  // Simulate connected state
  indicator.classList.add('active');
  martinInd.classList.add('active');

  // TODO: Replace with real WebSocket connection
  // const ws = new WebSocket('wss://141.253.108.141:8443/ws');
  // ws.onmessage = (e) => { ... };
}

// ─── Trading panel ───
function initTrading() {
  const gridsList = document.getElementById('grids-list');
  const portfolioEl = document.getElementById('portfolio-detail');
  const portfolioHeader = document.getElementById('portfolio');

  // Demo data (will be replaced by real API calls)
  function updateTrading() {
    gridsList.innerHTML = `
      <div class="grid-item">
        <span class="pair">BTC/USD</span>
        <span class="mode short">SHORT</span>
        <div class="stats">
          x5 | $15 capital | 10 levels | spacing 0.5%<br>
          RT: 0 | Profit: <span class="profit">$0.00</span><br>
          Range: $64,820 — $68,144
        </div>
      </div>
    `;
    portfolioEl.innerHTML = `
      <div style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim); line-height: 2;">
        Portfolio: <span style="color: var(--text-bright);">$23.31</span><br>
        Disponible: <span style="color: var(--green);">$22.00</span><br>
        En position: <span style="color: var(--orange);">$1.31</span>
      </div>
    `;
    portfolioHeader.textContent = '$23.31';
  }

  updateTrading();
}

// ─── Initialize everything ───
async function main() {
  await bootSequence();

  const orb = new Orb(document.getElementById('orb-canvas'));
  const agentManager = new AgentManager();

  startClock();
  initNav();
  initInput(orb, agentManager);
  initGateway();
  initTrading();

  // Welcome message
  setTimeout(() => {
    addMessage("Système en ligne. Grid SHORT BTC active. En attente.", 'ai');
  }, 500);

  // Cycle through orb states for demo
  setTimeout(() => orb.setState('listening'), 8000);
  setTimeout(() => orb.setState('thinking'), 11000);
  setTimeout(() => orb.setState('speaking'), 14000);
  setTimeout(() => orb.setState('idle'), 17000);

  // Expose for debugging
  window.NB = { orb, agentManager, addMessage };
}

main();
