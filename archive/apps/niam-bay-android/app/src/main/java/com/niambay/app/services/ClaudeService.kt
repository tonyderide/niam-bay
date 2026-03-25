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
 * NB-1 BIDIRECTIONNEL :
 * - Montant : l'utilisateur tape en français → encode NB-1 → envoi compressé à Claude
 * - Descendant : Claude répond en NB-1 → on reçoit compressé → decode côté client → affichage français
 *
 * Économie totale : ~40-60% sur les tokens montants ET descendants.
 * Le codebook est envoyé une fois au début. Amorti dès le 2ème échange.
 *
 * Flow :
 * 1. L'utilisateur tape un message en français
 * 2. NB1Codec.encode() compresse le message
 * 3. On envoie à Claude : system prompt + codebook NB-1 + message compressé
 * 4. Claude répond EN NB-1 (tokens descendants compressés)
 * 5. On accumule la réponse NB-1 complète
 * 6. NB1Codec.decode() décompresse → français lisible pour l'utilisateur
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

        // Construire les messages — tout l'historique est compressé en NB-1
        val messages = buildJsonArray {
            for (msg in conversationHistory.takeLast(10)) {
                addJsonObject {
                    put("role", msg.role)
                    // Compresser l'historique aussi — économie sur le contexte
                    put("content", NB1Codec.encode(msg.content))
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

        // Parse SSE stream — accumule le NB-1 et décode par segments
        val channel: ByteReadChannel = response.bodyAsChannel()
        val sseBuffer = StringBuilder()
        val nb1Buffer = StringBuilder()    // Accumule la réponse NB-1 brute
        var decodedSoFar = 0               // Combien de caractères décodés on a déjà émis

        while (!channel.isClosedForRead) {
            val byte = try { channel.readByte() } catch (_: Exception) { break }
            val char = byte.toInt().toChar()

            if (char == '\n') {
                val line = sseBuffer.toString()
                sseBuffer.clear()

                if (line.startsWith("data: ")) {
                    val data = line.removePrefix("data: ").trim()
                    if (data == "[DONE]") {
                        // Flush final : décoder tout ce qui reste dans le buffer NB-1
                        val fullDecoded = NB1Codec.decode(nb1Buffer.toString())
                        if (fullDecoded.length > decodedSoFar) {
                            emit(fullDecoded.substring(decodedSoFar))
                        }
                        return@flow
                    }

                    try {
                        val event = json.parseToJsonElement(data).jsonObject
                        val type = event["type"]?.jsonPrimitive?.content

                        if (type == "content_block_delta") {
                            val delta = event["delta"]?.jsonObject
                            val text = delta?.get("text")?.jsonPrimitive?.content
                            if (!text.isNullOrEmpty()) {
                                nb1Buffer.append(text)

                                // Décode par segment à chaque phrase complète (ponctuation ou saut de ligne)
                                // pour garder un effet streaming côté UI
                                val raw = nb1Buffer.toString()
                                val lastBreak = maxOf(
                                    raw.lastIndexOf('.'),
                                    raw.lastIndexOf('\n'),
                                    raw.lastIndexOf('!'),
                                    raw.lastIndexOf('?')
                                )
                                if (lastBreak > 0) {
                                    val fullDecoded = NB1Codec.decode(raw)
                                    if (fullDecoded.length > decodedSoFar) {
                                        emit(fullDecoded.substring(decodedSoFar))
                                        decodedSoFar = fullDecoded.length
                                    }
                                }
                            }
                        }
                    } catch (_: Exception) {
                        // Event SSE non parsable, on skip
                    }
                }
            } else {
                sseBuffer.append(char)
            }
        }

        // Flush final si le stream se ferme sans [DONE]
        val fullDecoded = NB1Codec.decode(nb1Buffer.toString())
        if (fullDecoded.length > decodedSoFar) {
            emit(fullDecoded.substring(decodedSoFar))
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
