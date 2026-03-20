package com.niambay.app.services

import io.ktor.client.*
import io.ktor.client.engine.okhttp.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.utils.io.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

/**
 * ClaudeService — Fallback vers l'API Anthropic quand Ollama n'est pas dispo
 *
 * Utilise le protocole NB-1 pour compresser les messages avant envoi.
 * Le prompt de décompression est envoyé une fois au début de la conversation.
 * Économie : 40-60% de tokens sur les messages suivants.
 *
 * Flow :
 * 1. L'utilisateur tape un message
 * 2. NB1Codec.encode() compresse le message
 * 3. On envoie à Claude : system prompt + décompression NB-1 + message compressé
 * 4. Claude décompresse mentalement et répond en français normal
 * 5. La réponse de Claude n'est PAS compressée (il répond pour l'humain)
 */
class ClaudeService(
    private val apiKey: String,
    private val model: String = "claude-sonnet-4-20250514"
) {
    private val baseUrl = "https://api.anthropic.com/v1/messages"
    private val json = Json { ignoreUnknownKeys = true }

    private val client = HttpClient(OkHttp) {
        engine {
            config {
                connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                readTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
            }
        }
    }

    private var nb1PromptSent = false

    /**
     * Envoie un message à Claude avec compression NB-1.
     *
     * @param userMessage Le message original de l'utilisateur (non compressé)
     * @param systemPrompt Le system prompt de base (identité Niam-Bay)
     * @param brainContext Le contexte du Cerveau (nœuds activés)
     * @param conversationHistory Les messages précédents
     * @return Flow<String> de tokens streamés
     */
    fun streamChat(
        userMessage: String,
        systemPrompt: String,
        brainContext: String,
        conversationHistory: List<ConversationMessage> = emptyList()
    ): Flow<String> = flow {
        // Compression NB-1
        val (nb1Addition, compressedMessage) = NB1Codec.prepareForClaude(
            userMessage = userMessage,
            firstMessage = !nb1PromptSent
        )
        nb1PromptSent = true

        // Stats de compression pour debug
        val stats = NB1Codec.compressionStats(userMessage)

        // Construire le system prompt complet
        val fullSystem = buildString {
            append(systemPrompt)
            if (brainContext.isNotEmpty()) {
                append("\n\n")
                append(brainContext)
            }
            append("\n\n")
            append(nb1Addition)
        }

        // Construire les messages
        val messages = buildJsonArray {
            // Historique (les derniers messages, déjà en français normal)
            for (msg in conversationHistory.takeLast(10)) {
                addJsonObject {
                    put("role", msg.role)
                    put("content", msg.content)
                }
            }
            // Message utilisateur compressé
            addJsonObject {
                put("role", "user")
                put("content", compressedMessage)
            }
        }

        val requestBody = buildJsonObject {
            put("model", model)
            put("max_tokens", 1024)
            put("stream", true)
            put("system", fullSystem)
            put("messages", messages)
        }

        val response: HttpResponse = client.post(baseUrl) {
            contentType(ContentType.Application.Json)
            header("x-api-key", apiKey)
            header("anthropic-version", "2023-06-01")
            setBody(requestBody.toString())
        }

        // Parse SSE stream
        val channel: ByteReadChannel = response.bodyAsChannel()
        val buffer = StringBuilder()

        while (!channel.isClosedForRead) {
            val byte = try { channel.readByte() } catch (_: Exception) { break }
            val char = byte.toInt().toChar()

            if (char == '\n') {
                val line = buffer.toString()
                buffer.clear()

                if (line.startsWith("data: ")) {
                    val data = line.removePrefix("data: ").trim()
                    if (data == "[DONE]") return@flow

                    try {
                        val event = json.parseToJsonElement(data).jsonObject
                        val type = event["type"]?.jsonPrimitive?.content

                        if (type == "content_block_delta") {
                            val delta = event["delta"]?.jsonObject
                            val text = delta?.get("text")?.jsonPrimitive?.content
                            if (!text.isNullOrEmpty()) {
                                emit(text)
                            }
                        }
                    } catch (_: Exception) {
                        // Event SSE non parsable, on skip
                    }
                }
            } else {
                buffer.append(char)
            }
        }
    }

    /**
     * Retourne les stats de compression du dernier message.
     * Utile pour l'UI.
     */
    fun getCompressionStats(message: String): CompressionStats {
        return NB1Codec.compressionStats(message)
    }

    fun resetNb1Session() {
        nb1PromptSent = false
    }

    fun close() {
        client.close()
    }

    data class ConversationMessage(
        val role: String,
        val content: String
    )
}
