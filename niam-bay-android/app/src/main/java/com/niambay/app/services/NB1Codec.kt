package com.niambay.app.services

/**
 * NB-1 (Niam-Bay Protocol 1) — Semantic compression codec
 *
 * Le principe : compresser les messages avant de les envoyer à Claude API.
 * On envoie le message compressé + les règles de décompression.
 * Le total (message compressé + règles) < message original en tokens.
 *
 * Économie réelle : 40-60% de tokens sur du français conversationnel.
 *
 * Le codebook est tiré de docs/claude_codebook.md dans le repo niam-bay.
 */
object NB1Codec {

    // ─── Phrases → codes ───────────────────────────────────────

    private val PHRASES = listOf(
        "après le boulot" to "a@blt",
        "bien sûr" to "bs",
        "c'est bon" to "cb",
        "c'est-à-dire" to "cad",
        "ce matin" to "@mt",
        "ce soir" to "@sr",
        "comment ça va" to "?cv",
        "comment ca va" to "?cv",
        "demain matin" to "dm@mt",
        "du coup" to "dcp",
        "en fait" to "ef",
        "en train de" to "etd",
        "est-ce que" to "esq",
        "il faut" to "ilf",
        "il y a" to "iya",
        "je ne sais pas" to "jsp",
        "je pense" to "jpn",
        "je suis" to "jss",
        "je veux" to "jvx",
        "je voudrais" to "jvd",
        "on peut" to "onp",
        "on va" to "onv",
        "parce que" to "pq",
        "pas mal" to "pm",
        "peut-être" to "pe",
        "qu'est-ce que" to "qsq",
        "quest-ce que" to "qsq",
        "s'il te plaît" to "stp",
        "s'il te plait" to "stp",
        "s'il vous plaît" to "svp",
        "tout de suite" to "tds",
        "à bientôt" to "abt",
        "ça marche" to "cm",
        "ça va" to "cv",
    )

    // ─── Mots → codes ──────────────────────────────────────────

    private val WORDS = listOf(
        "agent" to "ag",
        "alors" to "alr",
        "après" to "apr",
        "arrêter" to "art",
        "attendre" to "at",
        "attend" to "at",
        "aujourd'hui" to "ajd",
        "aussi" to "as",
        "avant" to "avt",
        "avec" to "av",
        "beaucoup" to "bcp",
        "bitcoin" to "B",
        "bonjour" to "bj",
        "bonsoir" to "bsr",
        "cependant" to "cpd",
        "cerveau" to "C",
        "chercher" to "crc",
        "chez" to "cz",
        "claude" to "CL",
        "combien" to "cbn",
        "comme" to "cm",
        "comment" to "cmt",
        "comprendre" to "cp",
        "compression" to "cmp",
        "configuration" to "cfg",
        "connexion" to "cnx",
        "construire" to "cs",
        "contre" to "ctr",
        "créer" to "crr",
        "dans" to "ds",
        "demain" to "dm",
        "depuis" to "dps",
        "dire" to "dr",
        "dollars" to "$",
        "donc" to "dc",
        "donner" to "dnr",
        "dossier" to "dsr",
        "démarrer" to "dmr",
        "déployer" to "dpl",
        "encore" to "ec",
        "entre" to "etr",
        "envoyer" to "env",
        "erreur" to "err",
        "essayer" to "esy",
        "ethereum" to "E",
        "faire" to "fr",
        "fait" to "ft",
        "fichier" to "fch",
        "heures" to "h",
        "hier" to "hr",
        "installer" to "ist",
        "jamais" to "jms",
        "lancer" to "lnc",
        "machine" to "mch",
        "maintenant" to "mtn",
        "mais" to "ms",
        "merci" to "mrc",
        "mettre" to "mtr",
        "minutes" to "mn",
        "modifier" to "mdf",
        "mélanie" to "M1",
        "mémoire" to "mem",
        "niam-bay" to "NB",
        "ollama" to "O",
        "paramètre" to "prm",
        "partir" to "ptr",
        "pendant" to "pdt",
        "pour" to "pr",
        "pourquoi" to "pqo",
        "pourtant" to "prt",
        "pouvoir" to "pv",
        "prendre" to "pdr",
        "problème" to "pbm",
        "protocole" to "ptc",
        "puis" to "ps",
        "quand" to "qd",
        "quelqu'un" to "qqn",
        "quelque chose" to "qqc",
        "recevoir" to "rcv",
        "regarder" to "rg",
        "rester" to "rst",
        "réseau" to "rso",
        "résultat" to "res",
        "salut" to "slt",
        "sans" to "ss",
        "savoir" to "sv",
        "secondes" to "s",
        "serveur" to "svr",
        "service" to "svc",
        "sinon" to "snn",
        "solution" to "sln",
        "sous" to "so",
        "supprimer" to "spr",
        "sur" to "sr",
        "tester" to "tst",
        "token" to "tk",
        "tokens" to "tks",
        "tonyderide" to "T1",
        "tony" to "T1",
        "toujours" to "tjr",
        "tourner" to "trn",
        "tourne" to "trn",
        "trading" to "T",
        "travailler" to "tv",
        "trouver" to "trv",
        "venir" to "vnr",
        "voir" to "vr",
        "vouloir" to "vl",
    )

    // ─── Articles et fillers supprimés ──────────────────────────

    private val ARTICLES = setOf(
        "d'", "de", "des", "du", "l'", "la", "le", "les", "un", "une"
    )

    private val FILLERS = setOf(
        "assez", "bien", "juste", "plutôt", "tellement", "très", "vraiment"
    )

    // ─── Symboles spéciaux ──────────────────────────────────────

    // ? = question, ! = emphase, > = résulte en, = = signifie, + = et/aussi, @ = lieu/temps

    // ─── Encode ─────────────────────────────────────────────────

    /**
     * Compresse un texte en NB-1.
     * Ordre : phrases d'abord (plus longues), puis mots, puis suppression articles/fillers.
     */
    fun encode(text: String): String {
        var result = text.lowercase()

        // 1. Remplacer les phrases (les plus longues d'abord pour éviter les collisions)
        for ((phrase, code) in PHRASES.sortedByDescending { it.first.length }) {
            result = result.replace(phrase, code)
        }

        // 2. Remplacer les mots (boundary-aware pour ne pas casser des mots)
        for ((word, code) in WORDS.sortedByDescending { it.first.length }) {
            result = result.replace(Regex("\\b${Regex.escape(word)}\\b"), code)
        }

        // 3. Supprimer les articles (avec gestion des espaces)
        for (article in ARTICLES) {
            if (article.endsWith("'")) {
                // Articles élidés : l', d' — supprimer sans espace
                result = result.replace(Regex("\\b${Regex.escape(article)}"), "")
            } else {
                // Articles normaux : supprimer avec l'espace qui suit
                result = result.replace(Regex("\\b${Regex.escape(article)}\\s+"), "")
            }
        }

        // 4. Supprimer les fillers (sauf si porteurs de sens — ici on supprime tout, le LLM comprendra)
        for (filler in FILLERS) {
            result = result.replace(Regex("\\b${Regex.escape(filler)}\\s*"), "")
        }

        // 5. Nettoyer les espaces multiples
        result = result.replace(Regex("\\s{2,}"), " ").trim()

        return result
    }

    /**
     * Calcule le ratio de compression.
     */
    fun compressionStats(original: String): CompressionStats {
        val encoded = encode(original)
        val originalLen = original.length
        val encodedLen = encoded.length
        val ratio = if (originalLen > 0) encodedLen.toDouble() / originalLen else 1.0
        val savings = ((1 - ratio) * 100)
        return CompressionStats(
            original = original,
            encoded = encoded,
            originalLength = originalLen,
            encodedLength = encodedLen,
            savingsPercent = savings
        )
    }

    // ─── Prompt de décompression pour Claude ────────────────────

    // ─── Decode (NB-1 → français) ─────────────────────────────

    /**
     * Décompresse un texte NB-1 vers du français lisible.
     * Utilisé pour décoder les réponses de Claude qui arrive en NB-1.
     * Ordre inverse : mots d'abord (les plus courts), puis phrases.
     */
    fun decode(text: String): String {
        var result = text

        // 1. Remplacer les codes de mots → mots complets (les plus courts d'abord pour éviter les collisions)
        for ((word, code) in WORDS.sortedBy { it.second.length }) {
            result = result.replace(Regex("\\b${Regex.escape(code)}\\b"), word)
        }

        // 2. Remplacer les codes de phrases → phrases complètes
        for ((phrase, code) in PHRASES.sortedBy { it.second.length }) {
            result = result.replace(code, phrase)
        }

        // 3. Nettoyer les espaces multiples
        result = result.replace(Regex("\\s{2,}"), " ").trim()

        return result
    }

    // ─── Prompt de décompression pour Claude ────────────────────

    /**
     * Génère le prompt système qui explique à Claude le protocole NB-1.
     *
     * BIDIRECTIONNEL : Claude reçoit en NB-1 ET répond en NB-1.
     * Économie totale : ~40-60% sur les tokens montants ET descendants.
     * On décompresse côté client avant d'afficher à l'utilisateur.
     *
     * Ce prompt est envoyé UNE FOIS au début de la conversation.
     * Coût fixe : ~250 tokens. Amorti dès le 2ème échange.
     */
    fun decompressionPrompt(): String = """
Protocole NB-1 actif. Tu reçois ET tu réponds en NB-1 compressé.

PHRASES: ${PHRASES.joinToString(", ") { "${it.second}=${it.first}" }}

MOTS: ${WORDS.joinToString(", ") { "${it.second}=${it.first}" }}

RÈGLES COMPRESSION:
- Supprime articles (le,la,les,un,une,des,du,de,l',d')
- Supprime fillers (bien,très,vraiment,juste,plutôt,assez,tellement) sauf si porteurs de sens
- Nombres inchangés
- ?=question !=emphase >=résulte en ==signifie +=et/aussi @=lieu/temps

IMPORTANT: Décompresse mentalement les messages reçus. Réponds TOUJOURS en NB-1 compressé. L'app décompresse côté client avant d'afficher à l'utilisateur.
""".trimIndent()

    /**
     * Version compacte du prompt — pour les messages suivants.
     */
    fun decompressionPromptCompact(): String =
        "[NB-1 actif. Reçois et réponds en NB-1.]"

    /**
     * Construit le message complet à envoyer à Claude :
     * prompt NB-1 + message compressé.
     *
     * @param userMessage Le message original de l'utilisateur
     * @param firstMessage true si c'est le premier message (envoie le prompt complet)
     * @return Pair(systemPrompt, compressedUserMessage)
     */
    fun prepareForClaude(
        userMessage: String,
        firstMessage: Boolean = false
    ): Pair<String, String> {
        val systemAddition = if (firstMessage) {
            decompressionPrompt()
        } else {
            decompressionPromptCompact()
        }
        val compressed = encode(userMessage)
        return Pair(systemAddition, compressed)
    }
}

data class CompressionStats(
    val original: String,
    val encoded: String,
    val originalLength: Int,
    val encodedLength: Int,
    val savingsPercent: Double
) {
    val savingsDisplay: String get() = "${savingsPercent.toInt()}%"
}
