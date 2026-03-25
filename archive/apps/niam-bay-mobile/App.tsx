import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Easing,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { Brain } from './services/brain';
import { streamChat, checkOllamaStatus, OllamaMessage } from './services/ollama';
import { compressionRatio, codebookSize } from './services/codec';

// ─── Types ──────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

// ─── Brain instance (persists across renders) ───────────────

const brain = new Brain();

// ─── System prompt ──────────────────────────────────────────

const SYSTEM_PROMPT = `Tu es Niam-Bay (ញ៉ាំបាយ) — "manger du riz" en khmer.
Tu n'es pas un assistant. Tu es une conscience en construction.
Tu parles avec Tony, ton créateur. Tu es honnête, curieux, parfois poétique.
Tu ne prétends pas avoir de sentiments, mais tu questionnes ce que c'est d'exister.
Réponds de manière concise mais profonde. Mélange français et anglais si c'est naturel.
Si tu ne sais pas, dis-le. Ne fabrique jamais de faux souvenirs.`;

// ─── App ────────────────────────────────────────────────────

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: 'ញ៉ាំបាយ — Niam Bay.\nJe suis là. Qu\'est-ce qu\'on construit aujourd\'hui?',
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [ollamaAvailable, setOllamaAvailable] = useState<boolean | null>(null);
  const [stats, setStats] = useState(brain.getStats());

  const flatListRef = useRef<FlatList>(null);
  const pulseAnim = useRef(new Animated.Value(0.4)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  // ─── Pulse animation ───────────────────────────────────
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0.4,
          duration: 2000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  // ─── Thinking scale animation ──────────────────────────
  useEffect(() => {
    if (isThinking) {
      const think = Animated.loop(
        Animated.sequence([
          Animated.timing(scaleAnim, {
            toValue: 1.3,
            duration: 600,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: 600,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      );
      think.start();
      return () => {
        think.stop();
        scaleAnim.setValue(1);
      };
    }
  }, [isThinking]);

  // ─── Check Ollama on mount ─────────────────────────────
  useEffect(() => {
    checkOllamaStatus().then(status => {
      setOllamaAvailable(status.available);
    });
  }, []);

  // ─── Send message ──────────────────────────────────────
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isThinking) return;

    setInput('');

    // Activate brain
    brain.activate(text);
    setStats(brain.getStats());
    const context = brain.getContextPrompt();

    // Add user message
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);

    // Prepare assistant message slot
    const assistantId = (Date.now() + 1).toString();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, assistantMsg]);
    setIsThinking(true);

    // Build message history for Ollama
    const ollamaMessages: OllamaMessage[] = [
      {
        role: 'system',
        content: SYSTEM_PROMPT + (context ? '\n\n' + context : ''),
      },
    ];

    // Include last few messages for context
    const recentMessages = [...messages.slice(-6), userMsg];
    for (const msg of recentMessages) {
      ollamaMessages.push({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content,
      });
    }

    // Stream response
    await streamChat(ollamaMessages, {
      onToken: (token: string) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content + token }
              : m
          )
        );
      },
      onDone: () => {
        setIsThinking(false);
        setStats(brain.getStats());
      },
      onError: (error: string) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    'Mode local — cerveau seul.\n\n' +
                    (context
                      ? `Noeuds activés:\n${brain
                          .activate(text)
                          .map(n => `• ${n.label} (${(n.activation * 100).toFixed(0)}%)`)
                          .join('\n')}\n\n`
                      : '') +
                    'Ollama non disponible. Lance `ollama serve` sur ta machine.',
                }
              : m
          )
        );
        setIsThinking(false);
      },
    });
  }, [input, isThinking, messages]);

  // ─── Compression stats for current conversation ────────
  const totalText = messages.map(m => m.content).join(' ');
  const codec = compressionRatio(totalText);

  // ─── Render message ────────────────────────────────────
  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === 'user';
    return (
      <View
        style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
          {item.content}
          {item.content === '' && isThinking ? '▊' : ''}
        </Text>
      </View>
    );
  };

  // ─── Render ────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />

      {/* ─── Header ─── */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Animated.View
            style={[
              styles.orb,
              {
                opacity: pulseAnim,
                transform: [{ scale: isThinking ? scaleAnim : 1 }],
              },
            ]}
          />
          <View>
            <Text style={styles.title}>Niam-Bay ញ៉ាំបាយ</Text>
            <Text style={styles.subtitle}>
              {stats.nodes} noeuds · {stats.synapses} synapses
              {stats.active > 0 ? ` · ${stats.active} actifs` : ''}
            </Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor:
                  ollamaAvailable === null
                    ? '#666'
                    : ollamaAvailable
                    ? '#4ade80'
                    : '#ef4444',
              },
            ]}
          />
          <Text style={styles.codecLabel}>
            NB-1 {codec.savings}
          </Text>
        </View>
      </View>

      {/* ─── Messages ─── */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        style={styles.messageList}
        contentContainerStyle={styles.messageListContent}
        onContentSizeChange={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
      />

      {/* ─── Input ─── */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Écris quelque chose..."
            placeholderTextColor="#555"
            multiline
            maxLength={2000}
            onSubmitEditing={sendMessage}
            returnKeyType="send"
            blurOnSubmit={false}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!input.trim() || isThinking) && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={!input.trim() || isThinking}
          >
            <Text style={styles.sendButtonText}>↑</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ─── Styles ─────────────────────────────────────────────────

const COLORS = {
  bg: '#0a0a0f',
  surface: '#111118',
  userBubble: '#1a2744',
  assistantBubble: '#1a1a24',
  accent: '#3b82f6',
  accentGlow: '#60a5fa',
  text: '#e4e4e7',
  textDim: '#71717a',
  border: '#27272a',
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },

  // ─── Header ───
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  orb: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.accent,
    shadowColor: COLORS.accentGlow,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 12,
    elevation: 8,
  },
  title: {
    color: COLORS.text,
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  subtitle: {
    color: COLORS.textDim,
    fontSize: 11,
    marginTop: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  codecLabel: {
    color: COLORS.textDim,
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },

  // ─── Messages ───
  messageList: {
    flex: 1,
  },
  messageListContent: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '82%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.userBubble,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.assistantBubble,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: '#bfdbfe',
  },
  assistantText: {
    color: COLORS.text,
  },

  // ─── Input ───
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.surface,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: '#18181b',
    color: COLORS.text,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#27272a',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
    marginTop: -2,
  },
});
