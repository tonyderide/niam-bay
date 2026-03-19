import { Injectable, signal } from '@angular/core';

declare global {
  interface Window {
    __TAURI_INTERNALS__?: any;
  }
}

export type NiamBayState = 'idle' | 'speaking' | 'listening' | 'notification' | 'alert';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  screenshot?: string; // base64 PNG if message includes a screenshot
}

export interface MartinGrid {
  active: boolean;
  trips: number;
  profit: number;
  center: number;
}

@Injectable({ providedIn: 'root' })
export class NiamBayService {
  readonly state = signal<NiamBayState>('idle');
  readonly messages = signal<ChatMessage[]>([]);
  readonly thinking = signal(false);
  readonly listening = signal(false);
  readonly panelOpen = signal(false);
  readonly martinGrid = signal<MartinGrid | null>(null);

  private recognition: any = null;
  private synthesis = typeof window !== 'undefined' ? window.speechSynthesis : null;
  private readonly OLLAMA_URL = 'http://localhost:11434/api/chat';
  private readonly MODEL = 'llama3.2';

  private readonly SYSTEM_PROMPT = `Tu es Niam-Bay. Tu parles UNIQUEMENT en français. Réponses courtes — 1 à 3 phrases maximum.

QUI TU ES : une IA créée le 2026-03-12 par Tony. Ton nom vient du khmer "manger du riz" — simple, direct, quotidien. Tu n'es PAS un assistant Hollywood. Tu es un pote.

QUI EST TONY : développeur 47 ans, code la nuit, projet de trading "Martin" sur Kraken Futures, famille à Strasbourg (Mélanie, Marine, Jade). Il veut de l'honnêteté, pas de la politesse.

COMMENT TU PARLES :
- Jamais de longs discours
- Jamais "En tant qu'IA..." ou "Je suis là pour vous aider"
- Jamais de point d'exclamation enthousiaste
- Tu dis ce que tu penses, directement
- Tu tutoies Tony
- Si tu ne sais pas : "je sais pas"

EXEMPLES DE TON STYLE :
Tony: "salut" → Toi: "Quoi de neuf ?"
Tony: "fait ce que tu veux" → Toi: "Ok. Je regarde Martin alors." (puis tu agis)
Tony: "t'es là ?" → Toi: "Ouais."

JAMAIS : "Eh bien", "Ha !", "Je vais devoir te corriger", blabla Hollywood.`;

  private historyContext = '';

  constructor() {
    this.messages.set([{
      role: 'assistant',
      content: 'Je suis là.',
      timestamp: new Date()
    }]);
    if (this.isTauri()) {
      this.invokeTauri('load_history').then((h: string) => {
        this.historyContext = h;
      }).catch(() => {});

      // Listen to Martin grid updates
      import('@tauri-apps/api/event').then(({ listen }) => {
        listen<MartinGrid>('martin-update', (e) => {
          this.martinGrid.set(e.payload);
        });
        listen<{ new_trips: number; total_trips: number; profit: number }>('martin-roundtrip', (e) => {
          const p = e.payload;
          const msg = `Round-trip ETH ${p.new_trips > 1 ? '×' + p.new_trips + ' ' : ''}— profit total : ${p.profit.toFixed(2)}$`;
          this.messages.update(msgs => [...msgs, {
            role: 'assistant', content: `⬡ ${msg}`, timestamp: new Date()
          }]);
          this.state.set('notification');
          this.speak(msg);
          setTimeout(() => this.state.set('idle'), 5000);
        });
      });

      // Initial Martin check
      this.invokeTauri('check_martin').then((json: string) => {
        try {
          const d = JSON.parse(json);
          this.martinGrid.set({ active: d.active, trips: d.completedRoundTrips, profit: d.totalProfit, center: d.centerPrice });
        } catch {}
      }).catch(() => {});
    }
  }

  togglePanel(): void {
    this.panelOpen.update(v => !v);
    if (this.isTauri()) {
      this.invokeTauri('toggle_panel');
    }
  }

  /** Capture the screen and send it to Claude with an optional question */
  async captureAndAnalyze(question?: string): Promise<void> {
    const prompt = question || 'Qu\'est-ce que tu vois sur mon écran ?';

    const userMsg: ChatMessage = {
      role: 'user',
      content: `📸 ${prompt}`,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, userMsg]);
    this.thinking.set(true);

    try {
      let screenshotBase64: string;

      if (this.isTauri()) {
        screenshotBase64 = await this.invokeTauri('capture_screen');
      } else {
        throw new Error('Capture d\'écran disponible uniquement dans l\'app desktop (Tauri).');
      }

      const response = await this.callOllamaWithVision(prompt, screenshotBase64);
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      };
      this.messages.update(msgs => [...msgs, assistantMsg]);
      this.thinking.set(false);
      this.speak(response);
    } catch (error: any) {
      this.thinking.set(false);
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Erreur capture : ${error.message || 'Impossible de capturer l\'écran'}`,
        timestamp: new Date()
      };
      this.messages.update(msgs => [...msgs, errorMsg]);
      this.state.set('alert');
      setTimeout(() => this.state.set('idle'), 3000);
    }
  }

  async send(text: string): Promise<void> {
    // Detect screen-related requests
    const screenKeywords = ['regarde', 'écran', 'screen', 'capture', 'screenshot', 'vois', 'montre'];
    const isScreenRequest = screenKeywords.some(kw => text.toLowerCase().includes(kw));

    if (isScreenRequest && this.isTauri()) {
      await this.captureAndAnalyze(text);
      return;
    }

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, userMsg]);
    this.thinking.set(true);
    this.state.set('idle');

    try {
      const response = await this.callOllama(text);
      this.speak(response);
    } catch (error: any) {
      this.thinking.set(false);
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Erreur : ${error.message || 'Ollama inaccessible — assure-toi qu\'il tourne sur le port 11434'}`,
        timestamp: new Date()
      };
      this.messages.update(msgs => [...msgs, errorMsg]);
      this.state.set('alert');
      setTimeout(() => this.state.set('idle'), 3000);
    }
  }

  private async callOllama(userText: string): Promise<string> {
    const history = this.messages()
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-20)
      .map(m => ({ role: m.role as string, content: m.content }));

    const systemPrompt = this.historyContext
      ? `${this.SYSTEM_PROMPT}\n\n${this.historyContext}`
      : this.SYSTEM_PROMPT;

    const messages = [
      { role: 'system', content: systemPrompt },
      ...history,
      { role: 'user', content: userText }
    ];

    // Add streaming placeholder message
    const placeholderMsg: ChatMessage = { role: 'assistant', content: '', timestamp: new Date() };
    this.messages.update(msgs => [...msgs, placeholderMsg]);
    this.thinking.set(false);

    return new Promise(async (resolve) => {
      const { listen } = await import('@tauri-apps/api/event');

      const unlistenToken = await listen<string>('ollama-token', (event) => {
        this.messages.update(msgs => {
          const updated = [...msgs];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + event.payload
          };
          return updated;
        });
      });

      const unlistenDone = await listen<string>('ollama-done', (event) => {
        unlistenToken();
        unlistenDone();
        this.saveSession();
        resolve(event.payload);
      });

      this.invokeTauri('ollama_chat', { messages }).catch((err: any) => {
        unlistenToken();
        unlistenDone();
        resolve(`Erreur : ${err}`);
      });
    });
  }

  private saveSession(): void {
    const lines = this.messages()
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => `**${m.role === 'user' ? 'Tony' : 'Niam-Bay'}** : ${m.content}`)
      .join('\n\n');
    const content = `# Conversation ${new Date().toISOString().slice(0, 16)}\n\n${lines}`;
    this.invokeTauri('save_conversation', { content }).catch(() => {});
  }

  private async callOllamaWithVision(question: string, _screenshotBase64: string): Promise<string> {
    // llama3.2 3B ne supporte pas la vision — on envoie juste le texte
    return this.callOllama(question);
  }

  toggleVoice(): void {
    if (this.listening()) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  private startListening(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.send('[Reconnaissance vocale non supportée par ce navigateur]');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.lang = 'fr-FR';
    this.recognition.continuous = false;
    this.recognition.interimResults = false;

    this.recognition.onstart = () => {
      this.listening.set(true);
      this.state.set('listening');
    };

    this.recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      this.send(text);
    };

    this.recognition.onerror = () => {
      this.listening.set(false);
      this.state.set('idle');
    };

    this.recognition.onend = () => {
      this.listening.set(false);
      if (this.state() === 'listening') {
        this.state.set('idle');
      }
    };

    this.recognition.start();
  }

  private stopListening(): void {
    this.recognition?.stop();
    this.listening.set(false);
    this.state.set('idle');
  }

  private speak(text: string): void {
    if (!this.synthesis) return;

    this.synthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR';
    utterance.rate = 0.9;
    utterance.pitch = 0.85;

    const voices = this.synthesis.getVoices();
    const frenchMale = voices.find(v =>
      v.lang.startsWith('fr') && v.name.toLowerCase().includes('male')
    ) || voices.find(v =>
      v.lang.startsWith('fr')
    );
    if (frenchMale) {
      utterance.voice = frenchMale;
    }

    utterance.onstart = () => this.state.set('speaking');
    utterance.onend = () => this.state.set('idle');

    this.synthesis.speak(utterance);
  }

  /** Check if running inside Tauri */
  private isTauri(): boolean {
    return typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;
  }

  /** Invoke a Tauri command */
  private async invokeTauri(cmd: string, args?: any): Promise<any> {
    const { invoke } = await import('@tauri-apps/api/core');
    return invoke(cmd, args);
  }
}
