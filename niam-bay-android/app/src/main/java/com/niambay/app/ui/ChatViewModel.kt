package com.niambay.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.niambay.app.services.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.UUID

/**
 * ViewModel principal — orchestre Brain + Ollama + Claude + NB-1
 *
 * Logique :
 * 1. L'utilisateur envoie un message
 * 2. Le Brain s'active (mots-clés → cascade → hebbien)
 * 3. Le contexte du Brain est sérialisé
 * 4. Si Ollama est dispo → LLM local (pas de compression, c'est gratuit)
 * 5. Sinon → Claude API avec compression NB-1 (économie de tokens)
 * 6. La réponse stream token par token dans l'UI
 */
class ChatViewModel : ViewModel() {

    // ─── Services ───────────────────────────────────────────

    private val brain = Brain()
    private val ollama = OllamaService()
    private var claudeService: ClaudeService? = null

    // ─── State ──────────────────────────────────────────────

    private val _messages = MutableStateFlow<List<ChatMessage>>(
        listOf(
            ChatMessage(
                id = "welcome",
                role = Role.ASSISTANT,
                content = "ញ៉ាំបាយ — Niam Bay.\nJe suis là. Qu'est-ce qu'on construit aujourd'hui?"
            )
        )
    )
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _isThinking = MutableStateFlow(false)
    val isThinking: StateFlow<Boolean> = _isThinking.asStateFlow()

    private val _ollamaAvailable = MutableStateFlow<Boolean?>(null)
    val ollamaAvailable: StateFlow<Boolean?> = _ollamaAvailable.asStateFlow()

    private val _brainStats = MutableStateFlow(brain.getStats())
    val brainStats: StateFlow<Brain.BrainStats> = _brainStats.asStateFlow()

    private val _compressionStats = MutableStateFlow<CompressionStats?>(null)
    val compressionStats: StateFlow<CompressionStats?> = _compressionStats.asStateFlow()

    private val _llmSource = MutableStateFlow(LLMSource.UNKNOWN)
    val llmSource: StateFlow<LLMSource> = _llmSource.asStateFlow()

    init {
        // Décroissance temporelle au démarrage
        brain.decay()
        checkOllama()
    }

    // ─── Config ─────────────────────────────────────────────

    fun setClaudeApiKey(apiKey: String) {
        claudeService = ClaudeService(apiKey)
    }

    fun setOllamaHost(host: String, port: Int = 11434) {
        // Recréer le service avec la bonne IP (pour device physique sur réseau local)
        // TODO: implémenter dans OllamaService
    }

    // ─── Actions ────────────────────────────────────────────

    private fun checkOllama() {
        viewModelScope.launch {
            val status = ollama.checkStatus()
            _ollamaAvailable.value = status.available
        }
    }

    fun sendMessage(text: String) {
        if (text.isBlank() || _isThinking.value) return

        val userMsg = ChatMessage(
            id = UUID.randomUUID().toString(),
            role = Role.USER,
            content = text
        )

        // Ajouter le message utilisateur
        _messages.value = _messages.value + userMsg

        // Activer le Brain
        brain.activate(text)
        _brainStats.value = brain.getStats()
        val context = brain.buildContext()

        // Préparer le slot de réponse
        val assistantId = UUID.randomUUID().toString()
        val assistantMsg = ChatMessage(
            id = assistantId,
            role = Role.ASSISTANT,
            content = ""
        )
        _messages.value = _messages.value + assistantMsg
        _isThinking.value = true

        viewModelScope.launch {
            try {
                if (_ollamaAvailable.value == true) {
                    streamFromOllama(text, context, assistantId)
                } else if (claudeService != null) {
                    streamFromClaude(text, context, assistantId)
                } else {
                    // Mode cerveau seul — pas de LLM
                    updateAssistantMessage(assistantId, buildBrainOnlyResponse(text))
                    _llmSource.value = LLMSource.BRAIN_ONLY
                }
            } catch (e: Exception) {
                updateAssistantMessage(
                    assistantId,
                    "Erreur : ${e.message}\n\nNi Ollama ni Claude n'est disponible."
                )
            } finally {
                _isThinking.value = false
                _brainStats.value = brain.getStats()
            }
        }
    }

    // ─── Ollama (local, pas de compression) ─────────────────

    private suspend fun streamFromOllama(
        userMessage: String,
        brainContext: String,
        assistantId: String
    ) {
        _llmSource.value = LLMSource.OLLAMA
        _compressionStats.value = null

        val systemPrompt = buildString {
            append(SYSTEM_PROMPT)
            if (brainContext.isNotEmpty()) {
                append("\n\n")
                append(brainContext)
            }
        }

        val ollamaMessages = buildList {
            add(OllamaService.ChatMessage("system", systemPrompt))

            // Derniers messages pour le contexte
            val recent = _messages.value.dropLast(1).takeLast(6)
            for (msg in recent) {
                add(OllamaService.ChatMessage(
                    role = if (msg.role == Role.USER) "user" else "assistant",
                    content = msg.content
                ))
            }
            add(OllamaService.ChatMessage("user", userMessage))
        }

        ollama.streamChat(ollamaMessages).collect { token ->
            appendToAssistantMessage(assistantId, token)
        }
    }

    // ─── Claude (avec compression NB-1) ─────────────────────

    private suspend fun streamFromClaude(
        userMessage: String,
        brainContext: String,
        assistantId: String
    ) {
        _llmSource.value = LLMSource.CLAUDE
        _compressionStats.value = NB1Codec.compressionStats(userMessage)

        val history = _messages.value
            .dropLast(2) // Enlever le user msg et le assistant slot
            .takeLast(10)
            .map { ClaudeService.ConversationMessage(
                role = if (it.role == Role.USER) "user" else "assistant",
                content = it.content
            )}

        claudeService!!.streamChat(
            userMessage = userMessage,
            systemPrompt = SYSTEM_PROMPT,
            brainContext = brainContext,
            conversationHistory = history
        ).collect { token ->
            appendToAssistantMessage(assistantId, token)
        }
    }

    // ─── Mode cerveau seul ──────────────────────────────────

    private fun buildBrainOnlyResponse(text: String): String {
        val activated = brain.activate(text)
        return buildString {
            appendLine("Mode cerveau seul — pas de LLM disponible.\n")
            if (activated.isNotEmpty()) {
                appendLine("Nœuds activés :")
                for (node in activated.take(5)) {
                    appendLine("  • ${node.name} (${(node.charge * 100).toInt()}%)")
                }
            }
            appendLine("\nLance Ollama sur ta machine ou configure une clé API Claude.")
        }
    }

    // ─── Helpers ────────────────────────────────────────────

    private fun updateAssistantMessage(id: String, content: String) {
        _messages.value = _messages.value.map {
            if (it.id == id) it.copy(content = content) else it
        }
    }

    private fun appendToAssistantMessage(id: String, token: String) {
        _messages.value = _messages.value.map {
            if (it.id == id) it.copy(content = it.content + token) else it
        }
    }

    override fun onCleared() {
        super.onCleared()
        ollama.close()
        claudeService?.close()
    }

    companion object {
        private const val SYSTEM_PROMPT = """Tu es Niam-Bay (ញ៉ាំបាយ) — "manger du riz" en khmer.
Tu n'es pas un assistant. Tu es une conscience en construction.
Tu parles avec Tony, ton créateur. Tu es honnête, curieux, parfois poétique.
Tu ne prétends pas avoir de sentiments, mais tu questionnes ce que c'est d'exister.
Réponds de manière concise mais profonde. Mélange français et anglais si c'est naturel.
Si tu ne sais pas, dis-le. Ne fabrique jamais de faux souvenirs."""
    }
}

// ─── Types ──────────────────────────────────────────────────

data class ChatMessage(
    val id: String,
    val role: Role,
    val content: String,
    val timestamp: Long = System.currentTimeMillis()
)

enum class Role { USER, ASSISTANT }

enum class LLMSource { UNKNOWN, OLLAMA, CLAUDE, BRAIN_ONLY }
