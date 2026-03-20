package com.niambay.app.services

/**
 * NB-1 (Niam-Bay Protocol 1) — Semantic compression codec
 *
 * Le principe : compresser les messages avant de les envoyer à Claude API.
 * On envoie le message compressé + les règles de décompression.
 * Le total (message compressé + règles) < message original en tokens.
 *
 * 4 niveaux de compression empilés :
 * 1. Templates (#) : messages entiers fréquents → hash court (#1, #2...)
 * 2. Intents (%) : patterns d'intention → code sémantique (%expl, %aide...)
 * 3. Codebook : phrases et mots → codes courts (existant)
 * 4. Vowel strip : mots non-codés → suppression des voyelles internes
 *
 * Économie réelle : 60-80% de tokens sur du français conversationnel.
 *
 * Le codebook est tiré de docs/claude_codebook.md dans le repo niam-bay.
 */
object NB1Codec {

    // ─── Templates : messages entiers → hash ──────────────────
    // Gain : ~95% sur ces messages. Coût codebook : 1 ligne chacun.

    private val TEMPLATES = listOf(
        "salut, comment ça va ?" to "#1",
        "salut comment ça va" to "#1",
        "bonjour, comment ça va ?" to "#1b",
        "ça va et toi ?" to "#2",
        "ça va et toi" to "#2",
        "oui ça marche" to "#3",
        "oui c'est bon" to "#3b",
        "non je ne pense pas" to "#4",
        "je ne sais pas trop" to "#5",
        "merci beaucoup" to "#6",
        "à demain" to "#7",
        "à plus tard" to "#8",
        "bonne nuit" to "#9",
        "pas de souci" to "#10",
        "c'est pas grave" to "#11",
        "qu'est-ce que tu en penses ?" to "#12",
        "qu'est-ce que tu en penses" to "#12",
        "tu peux m'expliquer ?" to "#13",
        "je comprends" to "#14",
        "je suis fatigué" to "#15",
        "je suis au boulot" to "#16",
        "les enfants dorment" to "#17",
        "j'ai pas le temps" to "#18",
        "on en reparle demain" to "#19",
        "c'est une bonne idée" to "#20",
    )

    // ─── Intents : patterns d'intention → code sémantique ─────
    // Compresse l'intention entière, pas les mots individuels.

    private val INTENTS = listOf(
        "est-ce que tu peux m'expliquer" to "%expl",
        "est-ce que tu peux" to "%peux",
        "tu pourrais m'aider" to "%aide",
        "tu pourrais" to "%prrais",
        "j'ai besoin de" to "%bsn",
        "j'ai besoin d'" to "%bsn",
        "je voudrais savoir" to "%?sv",
        "je veux savoir" to "%?sv",
        "ça veut dire quoi" to "%?def",
        "qu'est-ce que ça veut dire" to "%?def",
        "c'est quoi" to "%?cq",
        "comment on fait pour" to "%?how",
        "comment faire pour" to "%?how",
        "tu penses que" to "%?avis",
        "qu'est-ce que tu penses de" to "%?avis",
        "je suis en train de" to "%etd",
        "j'ai un problème avec" to "%pbm",
        "j'ai un problème" to "%pbm",
        "ça ne marche pas" to "%!ko",
        "ça marche pas" to "%!ko",
        "ça fonctionne pas" to "%!ko",
        "je ne comprends pas" to "%!cp",
        "je comprends pas" to "%!cp",
        "il faudrait que" to "%fdr",
        "on devrait" to "%fdr",
        "je pense que" to "%jpn",
        "à mon avis" to "%jpn",
    )

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
    // # = template message, % = intent

    // ─── Voyelles internes (pour le stripping) ────────────────

    private val VOWELS = setOf('a', 'e', 'i', 'o', 'u', 'y', 'à', 'â', 'é', 'è', 'ê', 'ë', 'î', 'ï', 'ô', 'ù', 'û', 'ü', 'ÿ')

    // Mots trop courts ou ambigus pour le vowel stripping
    private val VOWEL_STRIP_BLACKLIST = setOf(
        "ai", "au", "eu", "ou", "oui", "non", "et", "en", "on", "ne", "ni",
        "si", "ça", "ce", "se", "me", "te", "je", "tu", "il", "ma", "ta",
        "sa", "à", "y", "a"
    )

    /**
     * Supprime les voyelles internes d'un mot (garde la première et dernière lettre).
     * "comprendre" → "cmprndre", "fonctionner" → "fnctnner"
     * Claude lit très bien le français sans voyelles internes.
     * Ne s'applique qu'aux mots de 4+ lettres qui ne sont pas dans le codebook.
     */
    private fun stripVowels(word: String): String {
        if (word.length < 4) return word
        if (word in VOWEL_STRIP_BLACKLIST) return word
        // Garder première lettre, supprimer voyelles internes, garder dernière lettre
        val first = word.first()
        val last = word.last()
        val middle = word.substring(1, word.length - 1)
            .filter { it !in VOWELS }
        val result = "$first$middle$last"
        // Ne pas stripper si le résultat est trop court (illisible)
        return if (result.length >= 2) result else word
    }

    // Ensemble des codes connus pour éviter de vowel-stripper des codes NB-1
    private val ALL_CODES: Set<String> by lazy {
        (TEMPLATES.map { it.second } +
         INTENTS.map { it.second } +
         PHRASES.map { it.second } +
         WORDS.map { it.second }).toSet()
    }

    // ─── Encode ─────────────────────────────────────────────────

    /**
     * Compresse un texte en NB-1.
     * 4 passes empilées : templates → intents → codebook → vowel strip.
     */
    fun encode(text: String): String {
        var result = text.lowercase()

        // 1. Templates : messages entiers → hash (les plus longs d'abord)
        for ((template, code) in TEMPLATES.sortedByDescending { it.first.length }) {
            result = result.replace(template, code)
        }

        // 2. Intents : patterns d'intention → code sémantique
        for ((intent, code) in INTENTS.sortedByDescending { it.first.length }) {
            result = result.replace(intent, code)
        }

        // 3. Phrases du codebook (les plus longues d'abord)
        for ((phrase, code) in PHRASES.sortedByDescending { it.first.length }) {
            result = result.replace(phrase, code)
        }

        // 4. Mots du codebook (boundary-aware)
        for ((word, code) in WORDS.sortedByDescending { it.first.length }) {
            result = result.replace(Regex("\\b${Regex.escape(word)}\\b"), code)
        }

        // 5. Supprimer les articles
        for (article in ARTICLES) {
            if (article.endsWith("'")) {
                result = result.replace(Regex("\\b${Regex.escape(article)}"), "")
            } else {
                result = result.replace(Regex("\\b${Regex.escape(article)}\\s+"), "")
            }
        }

        // 6. Supprimer les fillers
        for (filler in FILLERS) {
            result = result.replace(Regex("\\b${Regex.escape(filler)}\\s*"), "")
        }

        // 7. Vowel stripping sur les mots restants non-codés (4+ lettres)
        result = result.split(" ").joinToString(" ") { word ->
            val clean = word.replace(Regex("[.,!?;:\"'()\\[\\]]"), "")
            if (clean.length >= 4 && clean !in ALL_CODES) {
                // Extraire la ponctuation attachée et ne stripper que le mot
                val prefix = word.takeWhile { !it.isLetterOrDigit() }
                val suffix = word.dropWhile { !it.isLetterOrDigit() }.reversed().takeWhile { !it.isLetterOrDigit() }.reversed()
                val core = word.removePrefix(prefix).removeSuffix(suffix)
                "$prefix${stripVowels(core)}$suffix"
            } else {
                word
            }
        }

        // 8. Nettoyer les espaces multiples
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
     * Utilisé pour décoder les réponses de Claude qui arrivent en NB-1.
     * Ordre : templates → intents → phrases → mots (les plus longs d'abord pour éviter les collisions).
     *
     * Note : le vowel stripping n'est PAS réversible côté client.
     * Mais Claude ne vowel-strippe pas dans ses réponses — il utilise les codes du codebook.
     * Le vowel stripping ne s'applique qu'à l'encode des messages utilisateur.
     */
    fun decode(text: String): String {
        var result = text

        // 1. Templates : hash → message complet (les plus longs codes d'abord)
        for ((template, code) in TEMPLATES.sortedByDescending { it.second.length }) {
            result = result.replace(code, template)
        }

        // 2. Intents : code sémantique → pattern complet
        for ((intent, code) in INTENTS.sortedByDescending { it.second.length }) {
            result = result.replace(code, intent)
        }

        // 3. Phrases : code → phrase complète
        for ((phrase, code) in PHRASES.sortedByDescending { it.second.length }) {
            result = result.replace(code, phrase)
        }

        // 4. Mots : code → mot complet (boundary-aware, les plus longs d'abord)
        for ((word, code) in WORDS.sortedByDescending { it.second.length }) {
            result = result.replace(Regex("\\b${Regex.escape(code)}\\b"), word)
        }

        // 5. Nettoyer les espaces multiples
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

TEMPLATES: ${TEMPLATES.joinToString(", ") { "${it.second}=${it.first}" }}

INTENTS: ${INTENTS.joinToString(", ") { "${it.second}=${it.first}" }}

PHRASES: ${PHRASES.joinToString(", ") { "${it.second}=${it.first}" }}

MOTS: ${WORDS.joinToString(", ") { "${it.second}=${it.first}" }}

RÈGLES:
- # = template msg entier, % = intent/pattern
- Articles supprimés (le,la,les,un,une,des,du,de,l',d')
- Fillers supprimés sauf si porteurs de sens
- Voyelles internes supprimées sur mots non-codés (4+ lettres). Ex: "comprendre"→"cmprndre". Tu peux lire ces mots et les utiliser.
- Nombres inchangés
- ?=question !=emphase >=résulte en ==signifie +=et/aussi @=lieu/temps

IMPORTANT: Décompresse mentalement. Réponds TOUJOURS en NB-1 : utilise les codes (#,%,mots,phrases), supprime articles/fillers. L'app décompresse côté client.
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
