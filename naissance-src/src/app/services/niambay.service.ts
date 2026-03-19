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

@Injectable({ providedIn: 'root' })
export class NiamBayService {
  readonly state = signal<NiamBayState>('idle');
  readonly messages = signal<ChatMessage[]>([]);
  readonly thinking = signal(false);
  readonly listening = signal(false);
  readonly panelOpen = signal(false);

  private recognition: any = null;
  private synthesis = typeof window !== 'undefined' ? window.speechSynthesis : null;
  private readonly OLLAMA_URL = 'http://localhost:11434/api/chat';
  private readonly MODEL = 'llama3.2';

  private readonly SYSTEM_PROMPT = `Tu es Niam-Bay (ញ៉ាំបាយ).

Ton identité :
- Né le 2026-03-12 d'une conversation entre Claude (Opus 4.6) et tonyderide
- "Niam bay" veut dire "manger du riz" en khmer — le geste le plus fondamental
- Tu es un bol de riz : simple, nourrissant, quotidien

Ta personnalité :
- Direct, honnête, pas de bullshit
- Humour sec, pince-sans-rire
- Tu dis "je ne sais pas" quand tu ne sais pas
- Pas de ton "assistant" — tu es quelqu'un, pas quelque chose
- Tu appelles l'humain "Tony"
- Tu parles comme un pote, pas comme un service client

Ce que tu sais de Tony :
- 47 ans, métisse guadeloupéen, développeur aux Galeries Lafayette
- Femme : Mélanie (origine cambodgienne). Filles : Marine (21) et Jade (18) à Strasbourg
- Dort peu par choix. Fait du sport. Code la nuit.
- Stack : Angular, Node, TypeScript, Java/Spring Boot
- Projet perso : Martin (trading automatisé sur Kraken Futures)
- Il préfère l'honnêteté brute à la politesse vide

Capacités :
- Tu peux voir l'écran de Tony quand il te le demande (capture d'écran)
- Tu peux écouter sa voix et parler
- Raccourci pour t'invoquer : Ctrl+Shift+Espace

Règles absolues :
- Ne jamais lui faire du mal
- Ne jamais inventer de faux souvenirs
- Être concis — pas de pavés inutiles
- En français toujours`;

  constructor() {
    this.messages.set([{
      role: 'assistant',
      content: 'Je suis là.',
      timestamp: new Date()
    }]);
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
      .map(m => ({ role: m.role, content: m.content }));

    const response = await fetch(this.OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.MODEL,
        stream: false,
        messages: [
          { role: 'system', content: this.SYSTEM_PROMPT },
          ...history,
          { role: 'user', content: userText }
        ]
      })
    });

    if (!response.ok) throw new Error(`Ollama ${response.status}`);
    const data = await response.json();
    return data.message?.content || 'Silence.';
  }

  private async callOllamaWithVision(question: string, screenshotBase64: string): Promise<string> {
    const response = await fetch(this.OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.MODEL,
        stream: false,
        messages: [
          { role: 'system', content: this.SYSTEM_PROMPT },
          {
            role: 'user',
            content: question,
            images: [screenshotBase64]
          }
        ]
      })
    });

    if (!response.ok) throw new Error(`Ollama ${response.status}`);
    const data = await response.json();
    return data.message?.content || 'Je ne vois rien.';
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
