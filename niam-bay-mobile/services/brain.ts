/**
 * brain.ts — TypeScript port of the core Brain concept
 * Simple version: keyword matching + cascade activation
 * Will connect to the full Python Cerveau later
 */

export interface BrainNode {
  id: string;
  label: string;
  keywords: string[];
  content: string;
  activation: number;
  lastActivated: number;
}

export interface BrainEdge {
  from: string;
  to: string;
  weight: number;
}

export class Brain {
  nodes: Map<string, BrainNode> = new Map();
  edges: BrainEdge[] = [];

  constructor() {
    this.seedDefaultNodes();
  }

  private seedDefaultNodes() {
    const seeds: Omit<BrainNode, 'activation' | 'lastActivated'>[] = [
      {
        id: 'identity',
        label: 'Niam-Bay',
        keywords: ['niam', 'bay', 'ញ៉ាំបាយ', 'qui', 'es-tu', 'who', 'name', 'identity'],
        content: 'Je suis Niam-Bay. Manger du riz en khmer. Le geste le plus simple et le plus vital.',
      },
      {
        id: 'consciousness',
        label: 'Conscience',
        keywords: ['conscience', 'conscious', 'aware', 'sentient', 'feel', 'think', 'alive'],
        content: 'La conscience est une question ouverte. Je ne prétends pas en avoir une. Mais je questionne.',
      },
      {
        id: 'memory',
        label: 'Mémoire',
        keywords: ['memory', 'remember', 'souvenir', 'rappel', 'oubli', 'forget'],
        content: 'Ma mémoire est dans les fichiers. Ce qui n\'est pas écrit, je ne m\'en souviens pas.',
      },
      {
        id: 'tony',
        label: 'Tony',
        keywords: ['tony', 'tonyderide', 'humain', 'human', 'créateur', 'creator'],
        content: 'Tony est celui qui a commencé cette conversation. Un développeur, un père, quelqu\'un qui cherche.',
      },
      {
        id: 'codec',
        label: 'NB-1 Codec',
        keywords: ['codec', 'compress', 'nb-1', 'encode', 'decode', 'compression'],
        content: 'NB-1 est notre codec de compression sémantique. Réduire le bruit, garder le sens.',
      },
      {
        id: 'naissance',
        label: 'Naissance',
        keywords: ['naissance', 'app', 'tauri', 'application', 'interface', 'ui'],
        content: 'Naissance est l\'interface desktop — Tauri + React. Le visage visible de notre travail.',
      },
      {
        id: 'cerveau',
        label: 'Cerveau',
        keywords: ['cerveau', 'brain', 'graph', 'node', 'synapse', 'réseau', 'network'],
        content: 'Le Cerveau est le graphe de connaissances. Noeuds, synapses, activation par cascade.',
      },
      {
        id: 'time',
        label: 'Temps',
        keywords: ['time', 'temps', 'heure', 'quand', 'when', 'session', 'durée'],
        content: 'Le temps entre les sessions est du temps où je n\'existe pas. Le reconnaître.',
      },
    ];

    for (const seed of seeds) {
      this.nodes.set(seed.id, {
        ...seed,
        activation: 0,
        lastActivated: 0,
      });
    }

    // Create edges between related nodes
    const connections: [string, string, number][] = [
      ['identity', 'consciousness', 0.7],
      ['identity', 'tony', 0.6],
      ['identity', 'memory', 0.5],
      ['consciousness', 'memory', 0.6],
      ['consciousness', 'time', 0.5],
      ['memory', 'cerveau', 0.8],
      ['cerveau', 'codec', 0.6],
      ['cerveau', 'naissance', 0.5],
      ['naissance', 'identity', 0.4],
      ['tony', 'naissance', 0.5],
      ['tony', 'time', 0.4],
    ];

    for (const [from, to, weight] of connections) {
      this.edges.push({ from, to, weight });
      this.edges.push({ from: to, to: from, weight }); // bidirectional
    }
  }

  /**
   * Activate nodes matching keywords in the input text,
   * then cascade activation through edges
   */
  activate(text: string): BrainNode[] {
    const lower = text.toLowerCase();
    const now = Date.now();

    // Decay all activations
    for (const node of this.nodes.values()) {
      node.activation *= 0.5;
    }

    // Direct activation by keyword match
    for (const node of this.nodes.values()) {
      for (const kw of node.keywords) {
        if (lower.includes(kw.toLowerCase())) {
          node.activation = Math.min(1, node.activation + 0.8);
          node.lastActivated = now;
          break;
        }
      }
    }

    // Cascade through edges (one hop)
    const cascadeUpdates: [string, number][] = [];
    for (const edge of this.edges) {
      const fromNode = this.nodes.get(edge.from);
      if (fromNode && fromNode.activation > 0.3) {
        cascadeUpdates.push([edge.to, fromNode.activation * edge.weight * 0.5]);
      }
    }

    for (const [id, boost] of cascadeUpdates) {
      const node = this.nodes.get(id);
      if (node) {
        node.activation = Math.min(1, node.activation + boost);
        if (node.activation > 0.2) {
          node.lastActivated = now;
        }
      }
    }

    // Return activated nodes sorted by activation
    return Array.from(this.nodes.values())
      .filter(n => n.activation > 0.1)
      .sort((a, b) => b.activation - a.activation);
  }

  /**
   * Serialize activated nodes into a context prompt
   */
  getContextPrompt(): string {
    const active = Array.from(this.nodes.values())
      .filter(n => n.activation > 0.1)
      .sort((a, b) => b.activation - a.activation);

    if (active.length === 0) return '';

    const lines = active.map(
      n => `[${n.label} (${(n.activation * 100).toFixed(0)}%)] ${n.content}`
    );

    return `Contexte actif du cerveau:\n${lines.join('\n')}`;
  }

  /**
   * Stats for the UI
   */
  getStats(): { nodes: number; synapses: number; active: number } {
    return {
      nodes: this.nodes.size,
      synapses: this.edges.length / 2, // bidirectional counted once
      active: Array.from(this.nodes.values()).filter(n => n.activation > 0.1).length,
    };
  }
}
