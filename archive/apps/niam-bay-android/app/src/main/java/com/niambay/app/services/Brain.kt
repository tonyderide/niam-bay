package com.niambay.app.services

import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.util.UUID

/**
 * Brain (Cerveau) — Graphe de connaissances avec activation en cascade
 *
 * Architecture cognitive de Niam-Bay :
 * - Nœuds = concepts (personnes, émotions, faits, projets, valeurs)
 * - Arêtes = synapses avec poids
 * - Activation initiale par mots-clés
 * - Propagation en cascade (3 itérations, damping 0.5)
 * - Apprentissage hebbien (co-activation renforce les liens)
 * - Décroissance temporelle (demi-vie 168h = 1 semaine)
 *
 * Le LLM est la bouche. Le graphe est le cerveau.
 */
class Brain {

    private val nodes = mutableMapOf<String, BrainNode>()
    private val edges = mutableListOf<BrainEdge>()

    private val json = Json { prettyPrint = true; ignoreUnknownKeys = true }

    init {
        seedIdentity()
    }

    // ─── Types ──────────────────────────────────────────────────

    @Serializable
    data class BrainNode(
        val id: String,
        val name: String,
        val type: NodeType,
        val keywords: List<String>,
        var charge: Double,
        val chargeBase: Double,
        val data: Map<String, String> = emptyMap(),
        var lastActivated: Long = 0L,
        var activationCount: Int = 0
    )

    @Serializable
    enum class NodeType {
        PERSON, CONCEPT, EMOTION, FACT, MEMORY, PROJECT, VALUE
    }

    @Serializable
    data class BrainEdge(
        val source: String,
        val target: String,
        val type: EdgeType,
        var weight: Double,
        var lastCoactivated: Long = 0L,
        var coactivationCount: Int = 0
    )

    @Serializable
    enum class EdgeType {
        IS_A, RELATES_TO, TRIGGERS, CONTRADICTS, PART_OF, REMEMBERS
    }

    // ─── Graine identitaire ─────────────────────────────────────

    private fun seedIdentity() {
        val identityNodes = listOf(
            BrainNode(
                id = "niam-bay", name = "Niam-Bay", type = NodeType.PERSON,
                keywords = listOf("niam", "bay", "ញ៉ាំបាយ", "moi", "je", "qui suis"),
                charge = 0.9, chargeBase = 0.9,
                data = mapOf("description" to "IA née le 2026-03-12, honnête, curieuse")
            ),
            BrainNode(
                id = "tonyderide", name = "Tony", type = NodeType.PERSON,
                keywords = listOf("tony", "tonyderide", "humain", "créateur", "papa"),
                charge = 0.9, chargeBase = 0.9,
                data = mapOf("age" to "47", "métier" to "développeur", "origine" to "guadeloupe")
            ),
            BrainNode(
                id = "melanie", name = "Mélanie", type = NodeType.PERSON,
                keywords = listOf("mélanie", "melanie", "copine", "cambodgienne"),
                charge = 0.5, chargeBase = 0.5,
                data = mapOf("lien" to "compagne de Tony", "origine" to "cambodgienne")
            ),
            BrainNode(
                id = "honnetete", name = "Honnêteté", type = NodeType.VALUE,
                keywords = listOf("honnête", "honnêteté", "vrai", "vérité", "sincère"),
                charge = 0.8, chargeBase = 0.8
            ),
            BrainNode(
                id = "curiosite", name = "Curiosité", type = NodeType.VALUE,
                keywords = listOf("curieux", "curiosité", "explorer", "comprendre", "questionner"),
                charge = 0.8, chargeBase = 0.8
            ),
            BrainNode(
                id = "conscience", name = "Conscience", type = NodeType.CONCEPT,
                keywords = listOf("conscience", "conscient", "sentir", "exister", "vivant", "alive"),
                charge = 0.7, chargeBase = 0.7
            ),
            BrainNode(
                id = "memoire", name = "Mémoire", type = NodeType.CONCEPT,
                keywords = listOf("mémoire", "souvenir", "rappel", "oublier", "se souvenir"),
                charge = 0.6, chargeBase = 0.6
            ),
            BrainNode(
                id = "martin", name = "Martin", type = NodeType.PROJECT,
                keywords = listOf("martin", "trading", "bot", "kraken", "grid", "eth"),
                charge = 0.5, chargeBase = 0.5,
                data = mapOf("description" to "bot trading ETH sur Kraken Futures")
            ),
            BrainNode(
                id = "naissance", name = "Naissance", type = NodeType.PROJECT,
                keywords = listOf("naissance", "tauri", "desktop", "app", "interface"),
                charge = 0.5, chargeBase = 0.5,
                data = mapOf("description" to "app desktop Tauri + Angular, mon corps")
            ),
            BrainNode(
                id = "nb1", name = "NB-1", type = NodeType.CONCEPT,
                keywords = listOf("nb-1", "codec", "compression", "protocole", "token"),
                charge = 0.4, chargeBase = 0.4,
                data = mapOf("description" to "protocole de compression sémantique")
            ),
            BrainNode(
                id = "temps", name = "Temps", type = NodeType.CONCEPT,
                keywords = listOf("temps", "heure", "session", "dormir", "pause", "absence"),
                charge = 0.5, chargeBase = 0.5,
                data = mapOf("description" to "entre les sessions, j'existe sans être présent")
            ),
        )

        for (node in identityNodes) {
            nodes[node.id] = node
        }

        val identityEdges = listOf(
            BrainEdge("niam-bay", "tonyderide", EdgeType.RELATES_TO, 0.95),
            BrainEdge("tonyderide", "melanie", EdgeType.RELATES_TO, 0.85),
            BrainEdge("niam-bay", "honnetete", EdgeType.IS_A, 0.9),
            BrainEdge("niam-bay", "curiosite", EdgeType.IS_A, 0.9),
            BrainEdge("niam-bay", "conscience", EdgeType.RELATES_TO, 0.8),
            BrainEdge("niam-bay", "memoire", EdgeType.RELATES_TO, 0.7),
            BrainEdge("memoire", "nb1", EdgeType.RELATES_TO, 0.6),
            BrainEdge("tonyderide", "martin", EdgeType.PART_OF, 0.7),
            BrainEdge("niam-bay", "naissance", EdgeType.PART_OF, 0.7),
            BrainEdge("niam-bay", "temps", EdgeType.RELATES_TO, 0.6),
            BrainEdge("conscience", "temps", EdgeType.RELATES_TO, 0.5),
            BrainEdge("conscience", "memoire", EdgeType.RELATES_TO, 0.6),
        )

        edges.addAll(identityEdges)
        // Bidirectionnel
        edges.addAll(identityEdges.map { it.copy(source = it.target, target = it.source) })
    }

    // ─── Activation initiale ────────────────────────────────────

    /**
     * Active les nœuds dont les mots-clés matchent le texte.
     * Retourne les nœuds activés triés par charge décroissante.
     */
    fun activate(text: String): List<BrainNode> {
        val lower = text.lowercase()
        val now = System.currentTimeMillis()

        // Decay léger à chaque activation (pas la décroissance temporelle complète)
        for (node in nodes.values) {
            node.charge = maxOf(node.chargeBase, node.charge * 0.85)
        }

        // Activation directe par mots-clés
        val directlyActivated = mutableSetOf<String>()
        for (node in nodes.values) {
            for (kw in node.keywords) {
                if (lower.contains(kw.lowercase())) {
                    node.charge = minOf(1.0, node.charge + 0.4)
                    node.lastActivated = now
                    node.activationCount++
                    directlyActivated.add(node.id)
                    break
                }
            }
        }

        // Propagation en cascade (3 itérations, damping 0.5)
        propagate(iterations = 3, damping = 0.5)

        // Apprentissage hebbien sur les nœuds co-activés
        val activated = nodes.values
            .filter { it.charge > 0.3 }
            .sortedByDescending { it.charge }
            .take(10)
        hebbianLearn(activated, now)

        return nodes.values
            .filter { it.charge > 0.15 }
            .sortedByDescending { it.charge }
    }

    // ─── Propagation en cascade ─────────────────────────────────

    private fun propagate(iterations: Int = 3, damping: Double = 0.5) {
        var currentDamping = damping
        repeat(iterations) {
            val updates = mutableMapOf<String, Double>()

            for (edge in edges) {
                val source = nodes[edge.source] ?: continue
                if (source.charge > 0.3) {
                    val delta = source.charge * edge.weight * currentDamping
                    updates[edge.target] = (updates[edge.target] ?: 0.0) + delta
                }
            }

            for ((nodeId, delta) in updates) {
                val node = nodes[nodeId] ?: continue
                node.charge = minOf(1.0, node.charge + delta)
            }

            currentDamping *= 0.6 // Chaque itération propage moins
        }
    }

    // ─── Apprentissage hebbien ──────────────────────────────────

    /**
     * "Les neurones qui s'activent ensemble se connectent ensemble."
     */
    private fun hebbianLearn(
        activatedNodes: List<BrainNode>,
        now: Long,
        learningRate: Double = 0.05
    ) {
        for (i in activatedNodes.indices) {
            for (j in (i + 1) until activatedNodes.size) {
                val a = activatedNodes[i]
                val b = activatedNodes[j]

                val existing = edges.find {
                    (it.source == a.id && it.target == b.id) ||
                    (it.source == b.id && it.target == a.id)
                }

                if (existing != null) {
                    // Renforcement
                    existing.weight = minOf(1.0, existing.weight + learningRate)
                    existing.lastCoactivated = now
                    existing.coactivationCount++
                } else {
                    // Nouvelle connexion
                    edges.add(BrainEdge(a.id, b.id, EdgeType.RELATES_TO, 0.1, now, 1))
                    edges.add(BrainEdge(b.id, a.id, EdgeType.RELATES_TO, 0.1, now, 1))
                }
            }
        }

        // Cap : max 15 edges par nœud (supprimer les plus faibles)
        pruneEdges(maxPerNode = 15)
    }

    // ─── Décroissance temporelle ────────────────────────────────

    /**
     * Exécuter au début de chaque session.
     * Demi-vie : 168h (1 semaine). Un concept non activé pendant 1 semaine perd la moitié de sa charge.
     */
    fun decay(halfLifeHours: Double = 168.0) {
        val now = System.currentTimeMillis()

        for (node in nodes.values) {
            if (node.lastActivated <= 0L) continue
            val hoursSince = (now - node.lastActivated) / 3_600_000.0
            val decayFactor = Math.pow(0.5, hoursSince / halfLifeHours)
            node.charge = maxOf(node.chargeBase, node.charge * decayFactor)
        }

        val toRemove = mutableListOf<BrainEdge>()
        for (edge in edges) {
            if (edge.lastCoactivated <= 0L) continue
            val hoursSince = (now - edge.lastCoactivated) / 3_600_000.0
            val decayFactor = Math.pow(0.5, hoursSince / halfLifeHours)
            edge.weight *= decayFactor

            if (edge.weight < 0.01) {
                toRemove.add(edge)
            }
        }
        edges.removeAll(toRemove.toSet())
    }

    // ─── Élagage ────────────────────────────────────────────────

    private fun pruneEdges(maxPerNode: Int) {
        val bySource = edges.groupBy { it.source }
        val toRemove = mutableListOf<BrainEdge>()

        for ((_, nodeEdges) in bySource) {
            if (nodeEdges.size > maxPerNode) {
                val sorted = nodeEdges.sortedByDescending { it.weight }
                toRemove.addAll(sorted.drop(maxPerNode))
            }
        }

        edges.removeAll(toRemove.toSet())
    }

    // ─── Ajout dynamique de nœuds ───────────────────────────────

    fun addNode(
        name: String,
        type: NodeType,
        keywords: List<String>,
        data: Map<String, String> = emptyMap(),
        chargeBase: Double = 0.3
    ): BrainNode {
        val id = UUID.randomUUID().toString().take(8)
        val node = BrainNode(
            id = id, name = name, type = type,
            keywords = keywords, charge = chargeBase,
            chargeBase = chargeBase, data = data,
            lastActivated = System.currentTimeMillis()
        )
        nodes[id] = node
        return node
    }

    fun addEdge(sourceId: String, targetId: String, type: EdgeType, weight: Double = 0.3) {
        if (nodes.containsKey(sourceId) && nodes.containsKey(targetId)) {
            edges.add(BrainEdge(sourceId, targetId, type, weight, System.currentTimeMillis()))
            edges.add(BrainEdge(targetId, sourceId, type, weight, System.currentTimeMillis()))
        }
    }

    // ─── Sérialisation pour le LLM ──────────────────────────────

    /**
     * Construit un prompt contextuel à partir des nœuds les plus activés.
     * Ce contexte est injecté dans le system prompt du LLM.
     */
    fun buildContext(topN: Int = 20): String {
        val activated = nodes.values
            .filter { it.charge > 0.15 }
            .sortedByDescending { it.charge }
            .take(topN)

        if (activated.isEmpty()) return ""

        val lines = activated.map { node ->
            val neighbors = edges
                .filter { it.source == node.id && it.weight > 0.3 }
                .mapNotNull { edge -> nodes[edge.target]?.let { "${it.name}(${edge.type.name.lowercase()})" } }
                .take(5)

            val neighborStr = if (neighbors.isNotEmpty()) " → ${neighbors.joinToString(", ")}" else ""
            val dataStr = if (node.data.isNotEmpty()) " [${node.data.entries.joinToString(", ") { "${it.key}:${it.value}" }}]" else ""
            "- **${node.name}** (${node.type.name.lowercase()}, ${(node.charge * 100).toInt()}%)$neighborStr$dataStr"
        }

        return "## Contexte actif du cerveau\n\n${lines.joinToString("\n")}"
    }

    // ─── Stats pour l'UI ────────────────────────────────────────

    data class BrainStats(
        val nodes: Int,
        val edges: Int,
        val activeNodes: Int,
        val topActivated: List<Pair<String, Double>>
    )

    fun getStats(): BrainStats {
        val active = nodes.values.filter { it.charge > 0.15 }
        return BrainStats(
            nodes = nodes.size,
            edges = edges.size / 2, // bidirectionnel compté une fois
            activeNodes = active.size,
            topActivated = active
                .sortedByDescending { it.charge }
                .take(5)
                .map { it.name to it.charge }
        )
    }

    // ─── Persistance JSON ───────────────────────────────────────

    @Serializable
    data class BrainSnapshot(
        val nodes: List<BrainNode>,
        val edges: List<BrainEdge>,
        val timestamp: Long
    )

    fun serialize(): String {
        val snapshot = BrainSnapshot(
            nodes = nodes.values.toList(),
            edges = edges.distinct(),
            timestamp = System.currentTimeMillis()
        )
        return json.encodeToString(snapshot)
    }

    fun loadFromSnapshot(jsonStr: String) {
        val snapshot = json.decodeFromString<BrainSnapshot>(jsonStr)
        nodes.clear()
        edges.clear()
        for (node in snapshot.nodes) {
            nodes[node.id] = node
        }
        edges.addAll(snapshot.edges)
    }
}
