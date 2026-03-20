import { Injectable, signal } from '@angular/core';

declare global {
  interface Window {
    __TAURI_INTERNALS__?: any;
  }
}

export type NiamBayState = 'idle' | 'speaking' | 'listening' | 'notification' | 'alert' | 'wakeword';

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
  readonly wakeWordListening = signal(false);

  private recognition: any = null;
  private wakeRecognition: any = null;
  private commandRecognition: any = null;
  private commandBuffer = '';
  private commandSilenceTimer: any = null;
  private wakeWordRestartTimer: any = null;
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
          setTimeout(() => this.state.set(this.wakeWordListening() ? 'wakeword' : 'idle'), 5000);
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

    // Auto-start wake word listener
    // Delay slightly to let the app settle and avoid permission prompts on load
    setTimeout(() => this.startWakeWordListener(), 2000);
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
      setTimeout(() => this.state.set(this.wakeWordListening() ? 'wakeword' : 'idle'), 3000);
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
      setTimeout(() => this.state.set(this.wakeWordListening() ? 'wakeword' : 'idle'), 3000);
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

  // ─── Wake Word Detection ───────────────────────────────────────

  private static readonly WAKE_PATTERNS = [
    /\bni[ay]m\s*ba[yi]l?l?e?\b/i,
    /\bnyam\s*bay?\b/i,
    /\bniambay\b/i,
    /\bniam\b/i,
    /\bnyam\b/i,
  ];

  /** Start always-on wake word listener. Call once at app init. */
  startWakeWordListener(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('[Niam-Bay] SpeechRecognition not supported — wake word disabled');
      return;
    }

    // Don't start twice
    if (this.wakeRecognition) return;

    const reco = new SpeechRecognition();
    reco.lang = 'fr-FR';
    reco.continuous = true;
    reco.interimResults = true;
    reco.maxAlternatives = 3;

    reco.onstart = () => {
      this.wakeWordListening.set(true);
      // Only set visual state if we're idle (don't override speaking/notification)
      if (this.state() === 'idle') {
        this.state.set('wakeword');
      }
    };

    reco.onresult = (event: any) => {
      // Check all results for wake word
      for (let i = event.resultIndex; i < event.results.length; i++) {
        // Check all alternatives for each result
        for (let alt = 0; alt < event.results[i].length; alt++) {
          const transcript = event.results[i][alt].transcript.toLowerCase().trim();
          if (this.containsWakeWord(transcript)) {
            // Extract everything after the wake word as potential command start
            const afterWake = this.extractAfterWakeWord(transcript);
            this.onWakeWordDetected(afterWake);
            return;
          }
        }
      }
    };

    reco.onerror = (event: any) => {
      console.warn('[Niam-Bay] Wake word recognition error:', event.error);
      this.wakeWordListening.set(false);
      // Auto-restart on recoverable errors
      if (event.error !== 'not-allowed' && event.error !== 'service-not-allowed') {
        this.scheduleWakeWordRestart();
      }
    };

    reco.onend = () => {
      this.wakeWordListening.set(false);
      if (this.state() === 'wakeword') {
        this.state.set('idle');
      }
      // Auto-restart: wake word listener should always be running
      // (unless we intentionally stopped it for command mode)
      if (this.wakeRecognition === reco) {
        this.scheduleWakeWordRestart();
      }
    };

    this.wakeRecognition = reco;
    try {
      reco.start();
    } catch (e) {
      console.warn('[Niam-Bay] Failed to start wake word listener:', e);
      this.scheduleWakeWordRestart();
    }
  }

  /** Stop wake word listener */
  stopWakeWordListener(): void {
    clearTimeout(this.wakeWordRestartTimer);
    if (this.wakeRecognition) {
      const reco = this.wakeRecognition;
      this.wakeRecognition = null; // set to null before stop to prevent auto-restart
      try { reco.stop(); } catch {}
    }
    this.wakeWordListening.set(false);
    if (this.state() === 'wakeword') {
      this.state.set('idle');
    }
  }

  private scheduleWakeWordRestart(): void {
    clearTimeout(this.wakeWordRestartTimer);
    this.wakeWordRestartTimer = setTimeout(() => {
      if (this.wakeRecognition) {
        // Still intending to listen — restart
        this.wakeRecognition = null;
        this.startWakeWordListener();
      }
    }, 1000);
  }

  private containsWakeWord(text: string): boolean {
    return NiamBayService.WAKE_PATTERNS.some(p => p.test(text));
  }

  private extractAfterWakeWord(text: string): string {
    for (const pattern of NiamBayService.WAKE_PATTERNS) {
      const match = text.match(pattern);
      if (match) {
        const idx = match.index! + match[0].length;
        return text.slice(idx).trim();
      }
    }
    return '';
  }

  /** Called when wake word is detected — switch to command mode */
  private onWakeWordDetected(initialText: string): void {
    console.log('[Niam-Bay] Wake word detected!', initialText ? `(initial: "${initialText}")` : '');

    // Stop wake word listener (we'll restart it after command is done)
    const wakeReco = this.wakeRecognition;
    this.wakeRecognition = null;
    try { wakeReco?.stop(); } catch {}

    // Open panel and set listening state
    if (!this.panelOpen()) {
      this.togglePanel();
    }
    this.state.set('listening');
    this.listening.set(true);

    // Play activation feedback via a short beep
    this.playActivationSound();

    // Start command recognition
    this.startCommandCapture(initialText);
  }

  private startCommandCapture(initialText: string): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    this.commandBuffer = initialText;

    // If we already got some text with the wake word, start the silence timer
    if (initialText) {
      this.resetCommandSilenceTimer();
    }

    const reco = new SpeechRecognition();
    reco.lang = 'fr-FR';
    reco.continuous = true;
    reco.interimResults = false;

    reco.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          const text = event.results[i][0].transcript.trim();
          if (text) {
            this.commandBuffer += (this.commandBuffer ? ' ' : '') + text;
            this.resetCommandSilenceTimer();
          }
        }
      }
    };

    reco.onerror = (event: any) => {
      console.warn('[Niam-Bay] Command recognition error:', event.error);
      this.finishCommandCapture();
    };

    reco.onend = () => {
      // If command capture ended but we have no buffer yet, just go back to wake word
      if (!this.commandBuffer.trim()) {
        this.finishCommandCapture();
      } else {
        // Speech ended naturally — process what we have
        clearTimeout(this.commandSilenceTimer);
        this.processCommand();
      }
    };

    this.commandRecognition = reco;
    try {
      reco.start();
    } catch (e) {
      console.warn('[Niam-Bay] Failed to start command capture:', e);
      this.finishCommandCapture();
    }

    // Safety timeout: if no speech after 5 seconds, abort
    if (!initialText) {
      setTimeout(() => {
        if (this.commandRecognition === reco && !this.commandBuffer.trim()) {
          this.finishCommandCapture();
        }
      }, 5000);
    }
  }

  private resetCommandSilenceTimer(): void {
    clearTimeout(this.commandSilenceTimer);
    this.commandSilenceTimer = setTimeout(() => {
      this.processCommand();
    }, 3000);
  }

  private processCommand(): void {
    const command = this.commandBuffer.trim();
    clearTimeout(this.commandSilenceTimer);

    // Stop command recognition
    try { this.commandRecognition?.stop(); } catch {}
    this.commandRecognition = null;

    this.listening.set(false);
    this.state.set('idle');

    if (command) {
      console.log('[Niam-Bay] Processing command:', command);
      this.send(command);
    }

    // Restart wake word listener after a short delay
    setTimeout(() => this.startWakeWordListener(), 500);
  }

  private finishCommandCapture(): void {
    clearTimeout(this.commandSilenceTimer);
    try { this.commandRecognition?.stop(); } catch {}
    this.commandRecognition = null;
    this.commandBuffer = '';
    this.listening.set(false);
    if (this.state() === 'listening') {
      this.state.set('idle');
    }

    // Restart wake word listener
    setTimeout(() => this.startWakeWordListener(), 500);
  }

  private playActivationSound(): void {
    try {
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.08);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);

      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.2);

      // Clean up
      setTimeout(() => ctx.close(), 500);
    } catch {
      // Audio not available — no problem
    }
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
    utterance.onend = () => this.state.set(this.wakeWordListening() ? 'wakeword' : 'idle');

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
