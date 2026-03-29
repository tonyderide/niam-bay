/**
 * NIAM-BAY Agent Orchestration Visualizer
 * Shows agents spawning, communicating, thinking, and dying
 * With animated data packets flowing between nodes
 */
import gsap from 'gsap';

const AGENT_ICONS = {
  brain: `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`,
  trading: `<svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  search: `<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  code: `<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  monitor: `<svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
  default: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`,
};

// Fixed positions — agents go to specific corners/edges, always on screen
const SLOTS = [
  { xPct: 0.12, yPct: 0.18 },  // top-left
  { xPct: 0.88, yPct: 0.18 },  // top-right
  { xPct: 0.12, yPct: 0.78 },  // bottom-left
  { xPct: 0.88, yPct: 0.78 },  // bottom-right
  { xPct: 0.50, yPct: 0.12 },  // top-center
  { xPct: 0.50, yPct: 0.85 },  // bottom-center
  { xPct: 0.08, yPct: 0.48 },  // mid-left
  { xPct: 0.92, yPct: 0.48 },  // mid-right
];

function getSlotPosition(index) {
  const slot = SLOTS[index % SLOTS.length];
  return {
    x: Math.max(40, Math.min(window.innerWidth - 80, slot.xPct * window.innerWidth - 28)),
    y: Math.max(55, Math.min(window.innerHeight - 90, slot.yPct * window.innerHeight - 28)),
  };
}

export class AgentManager {
  constructor() {
    this.agents = new Map();
    this.links = [];
    this.nodesEl = document.getElementById('agent-nodes');
    this.linksEl = document.getElementById('agent-links');
    this.panelEl = document.getElementById('agent-panel');
    this.panelLogsEl = document.getElementById('agent-logs');
    this.panelNameEl = document.getElementById('panel-agent-name');
    this.panelStatusEl = document.getElementById('panel-agent-status');
    this.countEl = document.querySelector('.agent-count');
    this.selectedAgent = null;

    document.getElementById('panel-close').addEventListener('click', () => {
      this.panelEl.classList.add('hidden');
      this.selectedAgent = null;
    });
  }

  /** Spawn a new agent node */
  spawn(id, name, type = 'default', parentId = null) {
    const agent = {
      id, name, type,
      state: 'spawning',
      logs: [],
      parentId,
      el: null,
    };

    // Create DOM element
    const node = document.createElement('div');
    node.className = 'agent-node spawning';
    node.innerHTML = `
      <div class="agent-node-inner">
        ${AGENT_ICONS[type] || AGENT_ICONS.default}
        <div class="agent-pulse-ring"></div>
      </div>
      <div class="agent-node-label">${name}</div>
    `;
    node.addEventListener('click', () => this._selectAgent(id));
    this.nodesEl.appendChild(node);
    agent.el = node;

    this.agents.set(id, agent);
    this._repositionAll();

    // If has parent, create link
    if (parentId && this.agents.has(parentId)) {
      this._createLink(parentId, id);
    }

    // After spawn animation, set to active
    setTimeout(() => {
      node.classList.remove('spawning');
      node.classList.add('active');
      agent.state = 'active';
    }, 600);

    this._updateCount();
    this._addLog(id, 'system', `Agent "${name}" spawned`);

    return agent;
  }

  /** Update agent state */
  setState(id, state) {
    const agent = this.agents.get(id);
    if (!agent) return;
    agent.state = state;
    agent.el.className = `agent-node ${state}`;
    this._addLog(id, 'system', `State → ${state.toUpperCase()}`);

    if (this.selectedAgent === id) {
      this.panelStatusEl.textContent = state.toUpperCase();
    }
  }

  /** Send message between agents (animated) */
  sendMessage(fromId, toId, message, type = 'data') {
    this._addLog(fromId, 'sent', `→ ${this.agents.get(toId)?.name || toId}: ${message}`);
    this._addLog(toId, 'received', `← ${this.agents.get(fromId)?.name || fromId}: ${message}`);

    // Animate data packet along the link
    this._animatePacket(fromId, toId);

    // Briefly highlight both agents
    const fromAgent = this.agents.get(fromId);
    const toAgent = this.agents.get(toId);
    if (fromAgent?.el) {
      fromAgent.el.querySelector('.agent-node-inner').style.boxShadow = '0 0 30px var(--blue-glow)';
      setTimeout(() => {
        fromAgent.el.querySelector('.agent-node-inner').style.boxShadow = '';
      }, 800);
    }
    if (toAgent?.el) {
      setTimeout(() => {
        toAgent.el.querySelector('.agent-node-inner').style.boxShadow = '0 0 30px var(--green-glow)';
        setTimeout(() => {
          toAgent.el.querySelector('.agent-node-inner').style.boxShadow = '';
        }, 800);
      }, 400);
    }
  }

  /** Fade agent to done state (persistent — stays visible but dimmed) */
  destroy(id) {
    const agent = this.agents.get(id);
    if (!agent) return;
    agent.state = 'done';
    agent.el.className = 'agent-node done';
    this._addLog(id, 'system', 'Task complete.');
    this._updateCount();
    // Don't remove — stays visible as a ghost
  }

  /** Actually remove agent from DOM (call only on new conversation) */
  clearAll() {
    for (const [, agent] of this.agents) {
      agent.el.remove();
    }
    this.agents.clear();
    this.links.forEach(l => l.el.remove());
    this.links = [];
    this._updateCount();
  }

  _selectAgent(id) {
    const agent = this.agents.get(id);
    if (!agent) return;
    this.selectedAgent = id;
    this.panelNameEl.textContent = agent.name;
    this.panelStatusEl.textContent = agent.state.toUpperCase();
    this.panelEl.classList.remove('hidden');

    // Render logs
    this.panelLogsEl.innerHTML = '';
    agent.logs.forEach(log => this._renderLog(log));
  }

  _addLog(agentId, type, message) {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    const log = { time, type, message };
    agent.logs.push(log);

    // If this agent is selected, render live
    if (this.selectedAgent === agentId) {
      this._renderLog(log);
      this.panelLogsEl.scrollTop = this.panelLogsEl.scrollHeight;
    }
  }

  _renderLog(log) {
    const el = document.createElement('div');
    el.className = `log-entry ${log.type}`;
    el.innerHTML = `<span class="log-time">${log.time}</span>${log.message}`;
    this.panelLogsEl.appendChild(el);
  }

  _repositionAll() {
    let idx = 0;
    for (const [, agent] of this.agents) {
      const pos = getSlotPosition(idx);
      gsap.to(agent.el, {
        left: pos.x, top: pos.y,
        duration: 0.8,
        ease: 'power3.out',
      });
      idx++;
    }
    // Update links after repositioning
    setTimeout(() => this._updateLinks(), 850);
  }

  _createLink(fromId, toId) {
    const link = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    link.classList.add('agent-link');
    link.dataset.from = fromId;
    link.dataset.to = toId;
    this.linksEl.appendChild(link);
    this.links.push({ fromId, toId, el: link });
    this._updateLinks();
  }

  _updateLinks() {
    for (const link of this.links) {
      const from = this.agents.get(link.fromId);
      const to = this.agents.get(link.toId);
      if (!from?.el || !to?.el) continue;
      const fr = from.el.getBoundingClientRect();
      const tr = to.el.getBoundingClientRect();
      link.el.setAttribute('x1', fr.left + 28);
      link.el.setAttribute('y1', fr.top + 28);
      link.el.setAttribute('x2', tr.left + 28);
      link.el.setAttribute('y2', tr.top + 28);
    }
  }

  _removeLinks(id) {
    this.links = this.links.filter(l => {
      if (l.fromId === id || l.toId === id) {
        l.el.remove();
        return false;
      }
      return true;
    });
  }

  _animatePacket(fromId, toId) {
    const from = this.agents.get(fromId);
    const to = this.agents.get(toId);
    if (!from?.el || !to?.el) return;

    const fr = from.el.getBoundingClientRect();
    const tr = to.el.getBoundingClientRect();
    const fx = fr.left + 28, fy = fr.top + 28;
    const tx = tr.left + 28, ty = tr.top + 28;

    // Find the link and activate it
    const link = this.links.find(l =>
      (l.fromId === fromId && l.toId === toId) ||
      (l.fromId === toId && l.toId === fromId)
    );
    if (link) link.el.classList.add('active');

    // ── Outgoing packet (blue) ──
    const packetOut = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    packetOut.setAttribute('cx', fx);
    packetOut.setAttribute('cy', fy);
    packetOut.setAttribute('r', '4');
    packetOut.setAttribute('fill', '#00d4ff');
    packetOut.setAttribute('filter', 'drop-shadow(0 0 6px #00d4ff)');
    this.linksEl.appendChild(packetOut);

    // Trail for outgoing
    const trailOut = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    trailOut.setAttribute('x1', fx); trailOut.setAttribute('y1', fy);
    trailOut.setAttribute('x2', fx); trailOut.setAttribute('y2', fy);
    trailOut.setAttribute('stroke', '#00d4ff');
    trailOut.setAttribute('stroke-width', '1.5');
    trailOut.setAttribute('opacity', '0.4');
    this.linksEl.appendChild(trailOut);

    gsap.to(packetOut, {
      attr: { cx: tx, cy: ty },
      duration: 0.7,
      ease: 'power2.inOut',
      onUpdate: () => {
        // Trail follows the packet with a lag
        const cx = parseFloat(packetOut.getAttribute('cx'));
        const cy = parseFloat(packetOut.getAttribute('cy'));
        const progress = gsap.getProperty(packetOut, 'cx');
        // Trail start lags behind
        const lagX = fx + (cx - fx) * 0.4;
        const lagY = fy + (cy - fy) * 0.4;
        trailOut.setAttribute('x1', lagX);
        trailOut.setAttribute('y1', lagY);
        trailOut.setAttribute('x2', cx);
        trailOut.setAttribute('y2', cy);
      },
      onComplete: () => {
        // Flash on arrival
        gsap.to(packetOut, { attr: { r: 8 }, opacity: 0, duration: 0.3, onComplete: () => packetOut.remove() });
        gsap.to(trailOut, { opacity: 0, duration: 0.3, onComplete: () => trailOut.remove() });

        // ── Return packet (green) — response going back ──
        setTimeout(() => {
          const packetBack = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          packetBack.setAttribute('cx', tx);
          packetBack.setAttribute('cy', ty);
          packetBack.setAttribute('r', '3');
          packetBack.setAttribute('fill', '#00ff88');
          packetBack.setAttribute('filter', 'drop-shadow(0 0 6px #00ff88)');
          this.linksEl.appendChild(packetBack);

          const trailBack = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          trailBack.setAttribute('x1', tx); trailBack.setAttribute('y1', ty);
          trailBack.setAttribute('x2', tx); trailBack.setAttribute('y2', ty);
          trailBack.setAttribute('stroke', '#00ff88');
          trailBack.setAttribute('stroke-width', '1.5');
          trailBack.setAttribute('opacity', '0.4');
          this.linksEl.appendChild(trailBack);

          gsap.to(packetBack, {
            attr: { cx: fx, cy: fy },
            duration: 0.7,
            ease: 'power2.inOut',
            onUpdate: () => {
              const cx2 = parseFloat(packetBack.getAttribute('cx'));
              const cy2 = parseFloat(packetBack.getAttribute('cy'));
              const lagX2 = tx + (cx2 - tx) * 0.4;
              const lagY2 = ty + (cy2 - ty) * 0.4;
              trailBack.setAttribute('x1', lagX2);
              trailBack.setAttribute('y1', lagY2);
              trailBack.setAttribute('x2', cx2);
              trailBack.setAttribute('y2', cy2);
            },
            onComplete: () => {
              gsap.to(packetBack, { attr: { r: 6 }, opacity: 0, duration: 0.3, onComplete: () => packetBack.remove() });
              gsap.to(trailBack, { opacity: 0, duration: 0.3, onComplete: () => trailBack.remove() });
              if (link) setTimeout(() => link.el.classList.remove('active'), 300);
            }
          });
        }, 200);
      }
    });
  }

  _updateCount() {
    const active = [...this.agents.values()].filter(a => a.state !== 'done').length;
    this.countEl.textContent = active;
    const indicator = document.getElementById('ind-agents');
    if (active > 0) {
      indicator.classList.add('active');
    } else {
      indicator.classList.remove('active');
    }
  }
}
