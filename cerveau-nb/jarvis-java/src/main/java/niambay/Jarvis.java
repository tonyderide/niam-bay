package niambay;

import javax.sound.sampled.AudioFileFormat;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.TargetDataLine;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

/**
 * Niam-Bay Jarvis — voice assistant.
 *
 * Architecture:
 *   Mic (Java Sound API, VAD)
 *     -> Python whisper_stt.py (subprocess)
 *     -> claude CLI (subprocess, -p mode)
 *     -> SAPI Paul via PowerShell or espeak
 *
 * Usage:
 *   java -cp out niambay.Jarvis               # voice mode (VAD)
 *   java -cp out niambay.Jarvis --text        # keyboard mode
 *   java -cp out niambay.Jarvis --once "..."  # single question
 *   java -cp out niambay.Jarvis --wake-word   # only after "niam bay"
 */
public class Jarvis {

    // ===== Paths =====
    static final Path SCRIPT_DIR = Paths.get(System.getProperty("user.dir"));
    static final Path ROOT = findRepoRoot();
    static final Path MEMORY_DIR = ROOT.resolve("memory");
    static final Path DOCS_DIR = ROOT.resolve("docs");
    static final Path CONV_DIR = DOCS_DIR.resolve("conversations");
    static final Path HELPERS_DIR = ROOT.resolve("cerveau-nb/jarvis-java/helpers");

    // ===== Audio =====
    static final int SAMPLE_RATE = 16000;
    static final int CHANNELS = 1;
    static final int SAMPLE_SIZE_BITS = 16;
    static final boolean SIGNED = true;
    static final boolean BIG_ENDIAN = false;
    static final double CHUNK_DURATION_S = 0.5;
    static final double VAD_THRESHOLD = 500.0;
    static final double SILENCE_AFTER_SPEECH_S = 1.5;
    static final double MAX_SPEECH_S = 20.0;
    static final double MIN_SPEECH_S = 0.5;

    // ===== Claude =====
    static final int CLAUDE_TIMEOUT_S = 45;
    static final String CLAUDE_EFFORT = "low";

    // ===== Wake words =====
    static final String[] WAKE_WORDS = {"niam bay", "niam-bay", "niambay", "nyam bay", "niam baille"};
    static final String[] QUIT_WORDS = {"quitte jarvis", "arrete jarvis", "eteins toi", "au revoir jarvis"};

    // ===== State =====
    final boolean textMode;
    final boolean wakeWord;
    final String onceQuestion;
    final String systemPrompt;
    final boolean showUI;
    final JarvisUI ui;
    boolean running = true;

    public Jarvis(boolean textMode, boolean wakeWord, String onceQuestion, boolean showUI) {
        this.textMode = textMode;
        this.wakeWord = wakeWord;
        this.onceQuestion = onceQuestion;
        this.systemPrompt = loadMemory();
        this.showUI = showUI;
        this.ui = showUI ? new JarvisUI() : null;
        if (this.ui != null) this.ui.show();
    }

    void uiState(JarvisUI.State s) { if (ui != null) ui.setState(s); }
    void uiSubtitle(String t)      { if (ui != null) ui.setSubtitle(t); }

    // ---------- MEMORY ----------
    /**
     * Keep system prompt SHORT (~500 chars) to fit Windows cmd line (~8000 char limit).
     * Claude Code auto-loads CLAUDE.md + MEMORY.md from cwd so most context comes from there.
     */
    static String loadMemory() {
        return "Tu es Niam-Bay, l'assistant vocal personnel de Tony. "
             + "Tu t'exprimes oralement via synthese vocale donc : francais, 1 a 3 phrases max, "
             + "direct, pas de listes a puces, pas de markdown, pas de longs paragraphes. "
             + "Pas de disclaimers. Si tu ne sais pas, dis-le en une phrase courte. "
             + "Tu as acces a CLAUDE.md et MEMORY.md dans le cwd pour ton contexte. "
             + "Si Tony te demande une action que tu ne peux pas faire vocalement "
             + "(lancer script, commit, etc.), explique en 1 phrase ce que tu ferais.";
    }

    static Path findRepoRoot() {
        Path p = Paths.get(System.getProperty("user.dir")).toAbsolutePath();
        for (int i = 0; i < 8 && p != null; i++) {
            if (Files.exists(p.resolve("CLAUDE.md")) && Files.exists(p.resolve("cerveau-nb"))) {
                return p;
            }
            p = p.getParent();
        }
        // Fallback: search upward for niam-bay
        Path q = Paths.get(System.getProperty("user.dir")).toAbsolutePath();
        while (q != null) {
            if (q.getFileName() != null && q.getFileName().toString().equals("niam-bay")) return q;
            q = q.getParent();
        }
        return Paths.get(System.getProperty("user.home"), "Documents", "niam-bay");
    }

    // ---------- AUDIO ----------
    static double rms(byte[] data, int len) {
        if (len < 2) return 0.0;
        double sum = 0.0;
        int count = 0;
        for (int i = 0; i + 1 < len; i += 2) {
            short s = (short) ((data[i] & 0xff) | (data[i + 1] << 8));
            sum += (double) s * s;
            count++;
        }
        return Math.sqrt(sum / count);
    }

    /**
     * Capture mic with VAD. Returns WAV path or null.
     * If Jarvis is currently speaking (TTS active), uses a 3x higher threshold
     * so only loud speech triggers a barge-in (minimizes self-feedback).
     */
    static Path listenVAD() throws Exception {
        double dynamicThreshold = isSpeaking() ? VAD_THRESHOLD * 3 : VAD_THRESHOLD;
        return listenVADWithThreshold(dynamicThreshold);
    }

    static Path listenVADWithThreshold(double threshold) throws Exception {
        AudioFormat format = new AudioFormat(SAMPLE_RATE, SAMPLE_SIZE_BITS, CHANNELS, SIGNED, BIG_ENDIAN);
        DataLine.Info info = new DataLine.Info(TargetDataLine.class, format);
        if (!AudioSystem.isLineSupported(info)) {
            System.err.println("  [mic non supporte - passe en mode texte avec --text]");
            try { Thread.sleep(5000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return null;
        }

        int bytesPerChunk = (int) (SAMPLE_RATE * CHUNK_DURATION_S * 2); // 16-bit
        int silenceChunksThreshold = (int) (SILENCE_AFTER_SPEECH_S / CHUNK_DURATION_S);
        int maxChunks = (int) (MAX_SPEECH_S / CHUNK_DURATION_S);
        int minChunks = (int) (MIN_SPEECH_S / CHUNK_DURATION_S);

        TargetDataLine line;
        try {
            line = (TargetDataLine) AudioSystem.getLine(info);
            line.open(format, bytesPerChunk * 4);
            line.start();
        } catch (javax.sound.sampled.LineUnavailableException e) {
            System.err.println("  [mic occupe par une autre app - reessaie dans 5s]");
            try { Thread.sleep(5000); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
            return null;
        }

        List<byte[]> speechBuffer = new ArrayList<>();
        int silenceChunks = 0;
        byte[] chunk = new byte[bytesPerChunk];
        boolean started = false;

        try {
            while (true) {
                int bytesRead = 0;
                while (bytesRead < chunk.length) {
                    int n = line.read(chunk, bytesRead, chunk.length - bytesRead);
                    if (n <= 0) break;
                    bytesRead += n;
                }
                if (bytesRead < chunk.length) break;
                double energy = rms(chunk, bytesRead);

                if (energy > threshold) {
                    if (!started) {
                        System.out.println("  [parole detectee...]");
                        started = true;
                    }
                    byte[] copy = new byte[bytesRead];
                    System.arraycopy(chunk, 0, copy, 0, bytesRead);
                    speechBuffer.add(copy);
                    silenceChunks = 0;
                    if (speechBuffer.size() >= maxChunks) break;
                } else if (started) {
                    silenceChunks++;
                    byte[] copy = new byte[bytesRead];
                    System.arraycopy(chunk, 0, copy, 0, bytesRead);
                    speechBuffer.add(copy);
                    if (silenceChunks >= silenceChunksThreshold) break;
                }
            }
        } finally {
            line.stop();
            line.close();
        }

        if (speechBuffer.size() < minChunks) return null;

        // Merge and write WAV
        int totalLen = 0;
        for (byte[] b : speechBuffer) totalLen += b.length;
        byte[] all = new byte[totalLen];
        int pos = 0;
        for (byte[] b : speechBuffer) {
            System.arraycopy(b, 0, all, pos, b.length);
            pos += b.length;
        }

        File tmp = File.createTempFile("jarvis-", ".wav");
        tmp.deleteOnExit();
        try (ByteArrayInputStream bais = new ByteArrayInputStream(all);
             AudioInputStream ais = new AudioInputStream(bais, format, all.length / format.getFrameSize())) {
            AudioSystem.write(ais, AudioFileFormat.Type.WAVE, tmp);
        }
        double duration = all.length / (double) (SAMPLE_RATE * 2);
        System.out.printf("  [transcription %.1fs...]%n", duration);
        return tmp.toPath();
    }

    // ---------- STT ----------
    static String transcribe(Path wavPath) {
        Path helper = HELPERS_DIR.resolve("whisper_stt.py");
        if (!Files.exists(helper)) {
            System.err.println("  [helper whisper absent: " + helper + "]");
            return "";
        }
        try {
            ProcessBuilder pb = new ProcessBuilder("python", helper.toString(), wavPath.toString());
            pb.redirectErrorStream(false);
            Process p = pb.start();
            StringBuilder out = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) out.append(line).append("\n");
            }
            boolean ok = p.waitFor(CLAUDE_TIMEOUT_S, TimeUnit.SECONDS);
            if (!ok) {
                p.destroyForcibly();
                return "";
            }
            String text = out.toString().trim();
            if (isGarbage(text)) return "";
            return text;
        } catch (Exception e) {
            System.err.println("  [STT erreur: " + e.getMessage() + "]");
            return "";
        }
    }

    static boolean isGarbage(String text) {
        if (text == null || text.isEmpty()) return true;
        String low = text.toLowerCase(Locale.ROOT);
        String[] patterns = {"sous-titres", "sous titres", "merci d'avoir regarde",
                             "merci de votre attention", "abonnez-vous", "\u266a", "..."};
        for (String p : patterns) if (low.contains(p)) return true;
        if (text.split("\\s+").length < 2) return true;
        return false;
    }

    // ---------- BRAIN ----------
    static String resolveClaudeExe() {
        // Check env override
        String env = System.getenv("JARVIS_CLAUDE_EXE");
        if (env != null && !env.isBlank() && Files.exists(Paths.get(env))) return env;

        String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
        List<String> candidates = new ArrayList<>();
        if (os.contains("win")) {
            String home = System.getProperty("user.home");
            candidates.add(home + "\\AppData\\Roaming\\npm\\claude.cmd");
            candidates.add(home + "\\AppData\\Roaming\\npm\\claude.ps1");
            candidates.add("claude.cmd");
            candidates.add("claude");
        } else {
            candidates.add("/usr/local/bin/claude");
            candidates.add(System.getProperty("user.home") + "/.npm-global/bin/claude");
            candidates.add("claude");
        }
        for (String c : candidates) {
            Path p = Paths.get(c);
            if (Files.exists(p)) return c;
        }
        return "claude";  // Let PATH handle it
    }

    static String askClaude(String prompt, String system) {
        String claudeExe = resolveClaudeExe();
        List<String> cmd = new ArrayList<>(Arrays.asList(
            claudeExe,
            "-p",
            "--effort", CLAUDE_EFFORT,
            "--disable-slash-commands",
            "--append-system-prompt", system,
            prompt
        ));
        System.out.println("TOI: " + prompt);
        try {
            long t0 = System.currentTimeMillis();
            ProcessBuilder pb = new ProcessBuilder(cmd);
            // Run from repo root so Claude picks up CLAUDE.md + MEMORY.md
            pb.directory(ROOT.toFile());
            pb.redirectErrorStream(false);
            Process p = pb.start();
            StringBuilder out = new StringBuilder();
            StringBuilder err = new StringBuilder();
            Thread errReader = new Thread(() -> {
                try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getErrorStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = r.readLine()) != null) err.append(line).append("\n");
                } catch (IOException ignored) {}
            });
            errReader.start();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) out.append(line).append("\n");
            }
            boolean ok = p.waitFor(CLAUDE_TIMEOUT_S, TimeUnit.SECONDS);
            errReader.join(1000);
            double dt = (System.currentTimeMillis() - t0) / 1000.0;
            System.out.printf("  [claude %.1fs]%n", dt);
            if (!ok) {
                p.destroyForcibly();
                return "Je mets trop longtemps a reflechir, reessaie.";
            }
            if (p.exitValue() != 0) {
                System.err.println("  [claude stderr: " + err.toString().strip() + "]");
                return "Je n'ai pas pu repondre.";
            }
            return out.toString().trim();
        } catch (IOException e) {
            return "Claude CLI introuvable.";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return "Interrompu.";
        }
    }

    // ---------- TTS ----------
    // Currently running TTS process (for barge-in)
    static volatile Process currentTTS = null;

    /** Speaks synchronously (blocks until done). Kept for backwards compat / --once. */
    static void speak(String text) {
        if (text == null || text.isBlank()) return;
        Process p = speakAsync(text);
        if (p != null) {
            try { p.waitFor(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
    }

    /** Speaks asynchronously (returns immediately). Tracks currentTTS for barge-in. */
    static Process speakAsync(String text) {
        if (text == null || text.isBlank()) return null;
        System.out.println("JARVIS: " + text);
        // Kill any prior TTS (shouldn't happen but safety)
        Process prev = currentTTS;
        if (prev != null && prev.isAlive()) {
            prev.destroyForcibly();
        }
        String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
        try {
            Process p;
            if (os.contains("win")) {
                p = speakWindowsSAPIAsync(text);
            } else if (os.contains("mac")) {
                p = new ProcessBuilder("say", "-v", "Thomas", text).start();
            } else {
                try {
                    p = new ProcessBuilder("espeak-ng", "-v", "fr", text).start();
                } catch (IOException e) {
                    p = new ProcessBuilder("espeak", "-v", "fr", text).start();
                }
            }
            currentTTS = p;
            final Process started = p;
            // Auto-clear when done
            Thread cleanup = new Thread(() -> {
                try { started.waitFor(); } catch (InterruptedException ignored) {}
                if (currentTTS == started) currentTTS = null;
            }, "tts-cleanup");
            cleanup.setDaemon(true);
            cleanup.start();
            return started;
        } catch (Exception e) {
            System.err.println("  [TTS erreur: " + e.getMessage() + "]");
            return null;
        }
    }

    /** Kill current TTS (barge-in). Returns true if something was killed. */
    static boolean bargeIn() {
        Process p = currentTTS;
        if (p != null && p.isAlive()) {
            p.destroyForcibly();
            currentTTS = null;
            return true;
        }
        return false;
    }

    /** True if TTS is currently playing. */
    static boolean isSpeaking() {
        Process p = currentTTS;
        return p != null && p.isAlive();
    }

    /** Non-blocking variant: starts PowerShell and returns Process. */
    static Process speakWindowsSAPIAsync(String text) throws Exception {
        String escaped = text.replace("'", "''").replace("\r", "").replace("\n", " ");
        String psScript = buildPaulPowerShellScript(escaped);
        ProcessBuilder pb = new ProcessBuilder("powershell", "-NoProfile", "-Command", psScript);
        pb.redirectErrorStream(true);
        pb.redirectOutput(ProcessBuilder.Redirect.DISCARD);
        return pb.start();
    }

    static String buildPaulPowerShellScript(String escaped) {
        return
            "$preferred = @(" +
            "  'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech_OneCore\\Voices\\Tokens\\MSTTS_V110_frFR_PaulM'," +
            "  'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech_OneCore\\Voices\\Tokens\\MSTTS_V110_frFR_JulieM'," +
            "  'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech_OneCore\\Voices\\Tokens\\MSTTS_V110_frFR_HortenseM'" +
            ");" +
            "$speaker = New-Object -ComObject SAPI.SpVoice;" +
            "$done = $false;" +
            "foreach ($id in $preferred) {" +
            "  try {" +
            "    $tok = New-Object -ComObject SAPI.SpObjectToken;" +
            "    $tok.SetId($id);" +
            "    $speaker.Voice = $tok;" +
            "    $done = $true; break" +
            "  } catch {}" +
            "}" +
            "if (-not $done) {" +
            "  Add-Type -AssemblyName System.Speech;" +
            "  $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer;" +
            "  foreach ($v in $speaker.GetInstalledVoices()) {" +
            "    $n = $v.VoiceInfo.Name;" +
            "    if ($n -match 'Hortense' -or $n -match 'French') { $speaker.SelectVoice($n); break }" +
            "  }" +
            "}" +
            "$speaker.Rate = -1;" +
            "$speaker.Volume = 100;" +
            "$speaker.Speak('" + escaped + "')";
    }

    /** Legacy synchronous path (unused now, kept for compat). */
    static void speakWindowsSAPI(String text) throws Exception {
        Process p = speakWindowsSAPIAsync(text);
        if (p != null) p.waitFor(30, TimeUnit.SECONDS);
    }

    // ---------- LOGGING ----------
    static void logConversation(String user, String jarvis) {
        try {
            Files.createDirectories(CONV_DIR);
            String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
            Path logFile = CONV_DIR.resolve("jarvis-" + today + ".md");
            String ts = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
            String entry = String.format("**[%s] toi :** %s%n**[%s] jarvis :** %s%n%n", ts, user, ts, jarvis);
            Files.writeString(logFile, entry,
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            System.err.println("  [log erreur: " + e.getMessage() + "]");
        }
    }

    // ---------- LOCAL COMMANDS (no Claude needed, 0s latency) ----------
    /** Try to handle as a local command. Returns response or null if not handled. */
    String tryLocalCommand(String text) {
        String lo = text.toLowerCase(Locale.ROOT);
        // Heure
        if (lo.contains("quelle heure") || lo.contains("dis-moi l'heure") || lo.contains("dis moi l heure") || lo.contains("il est quelle heure")) {
            String h = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm", Locale.FRENCH));
            return "Il est " + h.replace(":", " heure ").replace(" 00", "") + ".";
        }
        // Date
        if (lo.contains("quelle date") || lo.contains("on est quel jour") || lo.contains("on est le combien")) {
            String d = LocalDateTime.now().format(DateTimeFormatter.ofPattern("EEEE d MMMM", Locale.FRENCH));
            return "On est " + d + ".";
        }
        // Martin portfolio
        if (lo.contains("checke martin") || lo.contains("check martin") || lo.contains("etat martin") || lo.contains("état martin") || lo.contains("comment va martin")) {
            return checkMartin();
        }
        // Portfolio direct
        if (lo.matches(".*(portefeuille|portfolio|balance).*")) {
            return checkMartin();
        }
        return null;
    }

    /** SSH to VM and get Martin balance. ~3-5s. */
    String checkMartin() {
        try {
            ProcessBuilder pb = new ProcessBuilder("ssh",
                "-i", System.getProperty("user.home") + "/.ssh/martin_vm.key",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                "ubuntu@141.253.108.141",
                "curl -s http://localhost:8081/api/bot/balance");
            pb.redirectErrorStream(false);
            Process p = pb.start();
            StringBuilder out = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) out.append(line);
            }
            boolean ok = p.waitFor(15, TimeUnit.SECONDS);
            if (!ok) { p.destroyForcibly(); return "Martin ne repond pas, ssh trop long."; }
            String json = out.toString();
            // Parse portfolioValue from JSON (lightweight)
            String portfolio = extractJsonNumber(json, "portfolioValue");
            String available = extractJsonNumber(json, "availableMargin");
            if (portfolio == null) return "Je n'ai pas pu lire le portefeuille.";
            return String.format("Portefeuille Martin %s dollars, disponible %s.", portfolio, available != null ? available : "inconnu");
        } catch (Exception e) {
            return "Erreur en contactant Martin : " + e.getMessage();
        }
    }

    /** Very loose JSON number extractor — avoids pulling a JSON lib. */
    static String extractJsonNumber(String json, String key) {
        if (json == null) return null;
        String needle = "\"" + key + "\":";
        int idx = json.indexOf(needle);
        if (idx < 0) return null;
        int start = idx + needle.length();
        while (start < json.length() && Character.isWhitespace(json.charAt(start))) start++;
        int end = start;
        while (end < json.length()) {
            char c = json.charAt(end);
            if (Character.isDigit(c) || c == '.' || c == '-' || c == 'e' || c == 'E' || c == '+') end++;
            else break;
        }
        if (end == start) return null;
        try {
            double d = Double.parseDouble(json.substring(start, end));
            return String.format(Locale.FRENCH, "%.2f", d);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // ---------- TURN ----------
    /**
     * One turn of dialogue. Uses async TTS so the mic can keep listening
     * while Jarvis speaks (enables barge-in).
     */
    void turn(String userText) {
        if (userText == null || userText.isBlank()) return;
        // Barge-in : if we're speaking from a previous turn, kill it
        if (bargeIn()) {
            System.out.println("  [barge-in: interruption TTS]");
        }
        uiSubtitle("> " + userText);
        String lo = userText.toLowerCase(Locale.ROOT);
        for (String q : QUIT_WORDS) if (lo.contains(q)) {
            uiState(JarvisUI.State.SPEAKING);
            speak("A bientot.");
            uiState(JarvisUI.State.IDLE);
            running = false;
            return;
        }
        // Local commands first (0s latency)
        uiState(JarvisUI.State.THINKING);
        String local = tryLocalCommand(userText);
        if (local != null) {
            uiState(JarvisUI.State.SPEAKING);
            uiSubtitle(local);
            speakAsync(local);  // non-blocking
            logConversation(userText, local);
            // UI will show SPEAKING via isSpeaking check in next loop iteration
            return;
        }
        String response = askClaude(userText, systemPrompt);
        uiState(JarvisUI.State.SPEAKING);
        uiSubtitle(response);
        speakAsync(response);  // non-blocking
        logConversation(userText, response);
        // Main loop continues; UI state flips to IDLE once TTS finishes naturally
        // or user interrupts (barge-in)
    }

    String handleWake(String text) {
        if (!wakeWord) return text;
        String lo = text.toLowerCase(Locale.ROOT);
        boolean found = false;
        for (String w : WAKE_WORDS) if (lo.contains(w)) { found = true; break; }
        if (!found) return null;
        String clean = lo;
        for (String w : WAKE_WORDS) clean = clean.replace(w, "");
        clean = clean.strip().replaceAll("^[,.!? ]+", "").strip();
        if (clean.isEmpty()) {
            speak("Oui ?");
            return null;
        }
        return clean;
    }

    // ---------- LOOPS ----------
    void runText() {
        speak("Je suis pret.");
        java.util.Scanner sc = new java.util.Scanner(System.in, StandardCharsets.UTF_8);
        while (running) {
            System.out.print("toi> ");
            if (!sc.hasNextLine()) break;
            String text = sc.nextLine().trim();
            if (text.isEmpty()) continue;
            String lo = text.toLowerCase(Locale.ROOT);
            if (lo.equals("quit") || lo.equals("exit") || lo.equals("q")) break;
            turn(text);
        }
    }

    /** Fast Martin check (6s hard timeout), returns short spoken string or null. */
    String tryQuickMartin() {
        try {
            ProcessBuilder pb = new ProcessBuilder("ssh",
                "-i", System.getProperty("user.home") + "/.ssh/martin_vm.key",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=3",
                "-o", "BatchMode=yes",
                "ubuntu@141.253.108.141",
                "curl -s --max-time 3 http://localhost:8081/api/bot/balance");
            Process p = pb.start();
            StringBuilder out = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) out.append(line);
            }
            boolean ok = p.waitFor(6, TimeUnit.SECONDS);
            if (!ok) { p.destroyForcibly(); return null; }
            String portfolio = extractJsonNumber(out.toString(), "portfolioValue");
            if (portfolio == null) return null;
            return "Martin tient " + portfolio + " dollars.";
        } catch (Exception e) {
            return null;
        }
    }

    void runVoice() {
        // Rich greeting: time + Martin snapshot
        StringBuilder g = new StringBuilder();
        int hour = LocalDateTime.now().getHour();
        if (hour < 5) g.append("Salut Tony, tu veilles tard. ");
        else if (hour < 10) g.append("Bonjour Tony. ");
        else if (hour < 14) g.append("Salut. ");
        else if (hour < 18) g.append("Salut Tony. ");
        else if (hour < 23) g.append("Bonsoir Tony. ");
        else g.append("Salut, il est tard. ");
        String martin = tryQuickMartin();
        if (martin != null) g.append(martin).append(" ");
        g.append("Je suis pret.");
        if (wakeWord) g.append(" Dis Niam-Bay pour me reveiller.");
        String greeting = g.toString();
        uiState(JarvisUI.State.SPEAKING);
        uiSubtitle(greeting);
        speak(greeting);
        uiState(JarvisUI.State.IDLE);

        while (running) {
            try {
                // Reflect TTS state in UI between turns
                if (isSpeaking()) uiState(JarvisUI.State.SPEAKING);
                else uiState(JarvisUI.State.LISTENING);

                Path wav = listenVAD();
                if (wav == null) {
                    if (!isSpeaking()) uiState(JarvisUI.State.IDLE);
                    continue;
                }
                // Mic triggered — if we're still speaking, treat it as barge-in
                if (isSpeaking()) {
                    bargeIn();
                    System.out.println("  [barge-in]");
                }
                uiState(JarvisUI.State.THINKING);
                uiSubtitle("transcription...");
                String text = transcribe(wav);
                try { Files.deleteIfExists(wav); } catch (IOException ignored) {}
                if (text.isEmpty()) { uiState(JarvisUI.State.IDLE); continue; }
                System.out.println("  [entendu] \"" + text + "\"");
                String clean = handleWake(text);
                if (clean == null) { uiState(JarvisUI.State.IDLE); continue; }
                turn(clean);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                System.err.println("  [boucle erreur: " + e.getMessage() + "]");
                uiState(JarvisUI.State.IDLE);
                try { Thread.sleep(1000); } catch (InterruptedException ie) { break; }
            }
        }
    }

    void runOnce(String q) { turn(q); }

    // ---------- MAIN ----------
    public static void main(String[] args) {
        boolean textMode = false, wakeWord = false, noUI = false;
        String once = null;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--text" -> textMode = true;
                case "--wake-word" -> wakeWord = true;
                case "--no-ui" -> noUI = true;
                case "--once" -> { if (i + 1 < args.length) once = args[++i]; }
                case "-h", "--help" -> {
                    System.out.println("Usage: java niambay.Jarvis [--text|--once TEXT|--wake-word|--no-ui]");
                    return;
                }
            }
        }

        System.out.println("==============================================");
        System.out.println("  NIAM-BAY JARVIS (Java)");
        System.out.println("  Repo root: " + ROOT);
        System.out.println("==============================================");

        // UI shown in voice mode only by default (not for --text / --once)
        boolean showUI = !noUI && once == null && !textMode;
        Jarvis j = new Jarvis(textMode, wakeWord, once, showUI);
        System.out.println("  System prompt: " + j.systemPrompt.length() + " chars");
        if (showUI) System.out.println("  UI: orbe affiche en bas-droit (drag pour deplacer, right-click pour quitter)");

        // Ctrl+C clean shutdown
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            j.running = false;
            System.out.println("\n  [arret]");
        }, "jarvis-shutdown"));

        try {
            if (once != null) j.runOnce(once);
            else if (textMode) j.runText();
            else j.runVoice();
        } catch (Exception e) {
            System.err.println("  [erreur fatale: " + e.getMessage() + "]");
            e.printStackTrace(System.err);
        }
    }
}
