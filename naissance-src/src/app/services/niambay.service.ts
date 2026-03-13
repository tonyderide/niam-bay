import { Injectable, signal, computed } from '@angular/core';

export type NiamBayState = 'idle' | 'speaking' | 'listening' | 'notification' | 'alert';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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
  private apiKey = '';

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

  setApiKey(key: string): void {
    this.apiKey = key;
    localStorage.setItem('niambay_api_key', key);
  }

  loadApiKey(): void {
    this.apiKey = localStorage.getItem('niambay_api_key') || '';
  }

  togglePanel(): void {
    this.panelOpen.update(v => !v);
    // In Tauri, this would show/hide the panel window
    // For now, handled by the app component
  }

  async send(text: string): Promise<void> {
    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, userMsg]);
    this.thinking.set(true);
    this.state.set('idle');

    try {
      const response = await this.callAnthropic(text);
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      };
      this.messages.update(msgs => [...msgs, assistantMsg]);
      this.thinking.set(false);

      // Speak the response
      this.speak(response);
    } catch (error: any) {
      this.thinking.set(false);
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: error.message?.includes('api_key')
          ? 'Il me faut une clé API Anthropic. Clique sur le cercle, va dans les paramètres.'
          : `Erreur : ${error.message || 'Connexion impossible'}`,
        timestamp: new Date()
      };
      this.messages.update(msgs => [...msgs, errorMsg]);
      this.state.set('alert');
      setTimeout(() => this.state.set('idle'), 3000);
    }
  }

  private async callAnthropic(userText: string): Promise<string> {
    if (!this.apiKey) {
      throw new Error('Pas de clé API. Configure-la dans les paramètres (api_key).');
    }

    const conversationHistory = this.messages()
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-20) // Keep last 20 messages for context
      .map(m => ({ role: m.role, content: m.content }));

    // Add the new user message
    conversationHistory.push({ role: 'user', content: userText });

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1024,
        system: this.SYSTEM_PROMPT,
        messages: conversationHistory
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return data.content[0]?.text || 'Silence.';
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

    // Try to find a French male voice
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
}
