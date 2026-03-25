/**
 * ollama.ts — Connect to Ollama for local LLM inference
 *
 * On Android emulator, 10.0.2.2 maps to host machine's localhost.
 * On physical device / web, use localhost directly.
 */

import { Platform } from 'react-native';

const OLLAMA_HOST = Platform.OS === 'android' ? '10.0.2.2' : 'localhost';
const OLLAMA_PORT = 11434;
const OLLAMA_URL = `http://${OLLAMA_HOST}:${OLLAMA_PORT}`;

const DEFAULT_MODEL = 'llama3.2';

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onDone: (fullResponse: string) => void;
  onError: (error: string) => void;
}

/**
 * Check if Ollama is reachable
 */
export async function checkOllamaStatus(): Promise<{
  available: boolean;
  models: string[];
}> {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) return { available: false, models: [] };

    const data = await res.json();
    const models = (data.models || []).map((m: any) => m.name);
    return { available: true, models };
  } catch {
    return { available: false, models: [] };
  }
}

/**
 * Stream a chat completion from Ollama, calling onToken for each chunk
 */
export async function streamChat(
  messages: OllamaMessage[],
  callbacks: StreamCallbacks,
  model: string = DEFAULT_MODEL
): Promise<void> {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages,
        stream: true,
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      callbacks.onError(`Ollama error ${res.status}: ${errText}`);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      callbacks.onError('No response body reader available');
      return;
    }

    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      // Ollama sends newline-delimited JSON
      const lines = chunk.split('\n').filter(l => l.trim());

      for (const line of lines) {
        try {
          const json = JSON.parse(line);
          if (json.message?.content) {
            const token = json.message.content;
            fullResponse += token;
            callbacks.onToken(token);
          }
          if (json.done) {
            callbacks.onDone(fullResponse);
            return;
          }
        } catch {
          // Partial JSON, skip
        }
      }
    }

    callbacks.onDone(fullResponse);
  } catch (err: any) {
    callbacks.onError(
      `Impossible de joindre Ollama (${OLLAMA_URL}). ` +
      `Vérifie que Ollama tourne sur ta machine.\n` +
      `Erreur: ${err.message || err}`
    );
  }
}

/**
 * Simple non-streaming chat (fallback)
 */
export async function chat(
  messages: OllamaMessage[],
  model: string = DEFAULT_MODEL
): Promise<string> {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages,
        stream: false,
      }),
    });

    if (!res.ok) throw new Error(`Ollama error: ${res.status}`);

    const data = await res.json();
    return data.message?.content || 'Pas de réponse.';
  } catch {
    return 'Ollama non disponible. Je fonctionne en mode local — cerveau seul, sans LLM.';
  }
}
