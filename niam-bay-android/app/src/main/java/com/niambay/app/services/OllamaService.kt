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
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * OllamaService — Connexion au LLM local via Ollama
 *
 * Sur émulateur Android : 10.0.2.2 = localhost de la machine hôte
 * Sur device physique : configurable (IP du PC sur le réseau local)
 */
class OllamaService(
    private val host: String = "10.0.2.2",
    private val port: Int = 11434,
    private val model: String = "llama3.2"
) {
    private val baseUrl get() = "http://$host:$port"
    private val json = Json { ignoreUnknownKeys = true }

    private val client = HttpClient(OkHttp) {
        engine {
            config {
                connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
                readTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
            }
        }
    }

    @Serializable
    data class ChatMessage(
        val role: String,
        val content: String
    )

    /**
     * Vérifie si Ollama est accessible et retourne les modèles disponibles.
     */
    suspend fun checkStatus(): OllamaStatus {
        return try {
            val response: HttpResponse = client.get("$baseUrl/api/tags")
            if (response.status.isSuccess()) {
                val body = response.bodyAsText()
                val parsed = json.parseToJsonElement(body)
                val models = parsed.jsonObject["models"]
                    ?.let { json.decodeFromJsonElement(ModelsResponse.serializer(), parsed) }
                    ?.models?.map { it.name } ?: emptyList()
                OllamaStatus(available = true, models = models)
            } else {
                OllamaStatus(available = false)
            }
        } catch (_: Exception) {
            OllamaStatus(available = false)
        }
    }

    /**
     * Stream une réponse de chat token par token.
     * Retourne un Flow<String> de tokens.
     */
    fun streamChat(
        messages: List<ChatMessage>
    ): Flow<String> = flow {
        val requestBody = json.encodeToString(
            ChatRequest.serializer(),
            ChatRequest(model = model, messages = messages, stream = true)
        )

        val response: HttpResponse = client.post("$baseUrl/api/chat") {
            contentType(ContentType.Application.Json)
            setBody(requestBody)
        }

        val channel: ByteReadChannel = response.bodyAsChannel()
        val buffer = StringBuilder()

        while (!channel.isClosedForRead) {
            val byte = try { channel.readByte() } catch (_: Exception) { break }
            val char = byte.toInt().toChar()

            if (char == '\n') {
                val line = buffer.toString().trim()
                buffer.clear()

                if (line.isNotEmpty()) {
                    try {
                        val element = json.parseToJsonElement(line)
                        val content = element.jsonObject["message"]
                            ?.jsonObject?.get("content")
                            ?.jsonPrimitive?.content

                        if (!content.isNullOrEmpty()) {
                            emit(content)
                        }

                        val done = element.jsonObject["done"]
                            ?.jsonPrimitive?.content?.toBooleanStrictOrNull()
                        if (done == true) return@flow
                    } catch (_: Exception) {
                        // JSON partiel, on skip
                    }
                }
            } else {
                buffer.append(char)
            }
        }
    }

    /**
     * Chat non-streaming (fallback simple).
     */
    suspend fun chat(messages: List<ChatMessage>): String {
        return try {
            val requestBody = json.encodeToString(
                ChatRequest.serializer(),
                ChatRequest(model = model, messages = messages, stream = false)
            )

            val response: HttpResponse = client.post("$baseUrl/api/chat") {
                contentType(ContentType.Application.Json)
                setBody(requestBody)
            }

            val body = response.bodyAsText()
            val element = json.parseToJsonElement(body)
            element.jsonObject["message"]
                ?.jsonObject?.get("content")
                ?.jsonPrimitive?.content ?: "Pas de réponse."
        } catch (e: Exception) {
            "Ollama non disponible : ${e.message}"
        }
    }

    fun close() {
        client.close()
    }

    @Serializable
    private data class ChatRequest(
        val model: String,
        val messages: List<ChatMessage>,
        val stream: Boolean
    )

    @Serializable
    private data class ModelsResponse(
        val models: List<ModelInfo> = emptyList()
    )

    @Serializable
    private data class ModelInfo(
        val name: String
    )

    data class OllamaStatus(
        val available: Boolean,
        val models: List<String> = emptyList()
    )
}
