package com.niambay.app.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

@Composable
fun ChatScreen(viewModel: ChatViewModel, modifier: Modifier = Modifier) {
    val messages by viewModel.messages.collectAsState()
    val isThinking by viewModel.isThinking.collectAsState()
    val ollamaAvailable by viewModel.ollamaAvailable.collectAsState()
    val brainStats by viewModel.brainStats.collectAsState()
    val compressionStats by viewModel.compressionStats.collectAsState()
    val llmSource by viewModel.llmSource.collectAsState()

    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    // Auto-scroll quand un nouveau message arrive
    LaunchedEffect(messages.size, messages.lastOrNull()?.content) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(NiamBayColors.bg)
    ) {
        // ─── Header ─────────────────────────────────────────
        Header(
            isThinking = isThinking,
            ollamaAvailable = ollamaAvailable,
            brainStats = brainStats,
            compressionStats = compressionStats,
            llmSource = llmSource
        )

        // ─── Messages ───────────────────────────────────────
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            contentPadding = PaddingValues(vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages, key = { it.id }) { message ->
                MessageBubble(message = message, isThinking = isThinking && message == messages.lastOrNull())
            }
        }

        // ─── Input ──────────────────────────────────────────
        InputBar(
            text = inputText,
            onTextChange = { inputText = it },
            onSend = {
                if (inputText.isNotBlank()) {
                    viewModel.sendMessage(inputText)
                    inputText = ""
                    coroutineScope.launch {
                        listState.animateScrollToItem(messages.size)
                    }
                }
            },
            enabled = !isThinking
        )
    }
}

// ─── Header ─────────────────────────────────────────────────

@Composable
private fun Header(
    isThinking: Boolean,
    ollamaAvailable: Boolean?,
    brainStats: com.niambay.app.services.Brain.BrainStats,
    compressionStats: com.niambay.app.services.CompressionStats?,
    llmSource: LLMSource
) {
    // Pulse animation pour l'orbe
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )
    val thinkScale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(600, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "thinkScale"
    )

    Surface(
        color = NiamBayColors.surface,
        shadowElevation = 4.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Orbe animé
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .scale(if (isThinking) thinkScale else 1f)
                        .alpha(pulseAlpha)
                        .shadow(12.dp, CircleShape, ambientColor = NiamBayColors.accentGlow)
                        .clip(CircleShape)
                        .background(NiamBayColors.accent)
                )

                Column {
                    Text(
                        text = "Niam-Bay ញ៉ាំបាយ",
                        color = NiamBayColors.text,
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${brainStats.nodes} nœuds · ${brainStats.edges} synapses" +
                            if (brainStats.activeNodes > 0) " · ${brainStats.activeNodes} actifs" else "",
                        color = NiamBayColors.textDim,
                        fontSize = 11.sp
                    )
                }
            }

            Column(horizontalAlignment = Alignment.End) {
                // Status LLM
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(
                                when (ollamaAvailable) {
                                    true -> NiamBayColors.green
                                    false -> NiamBayColors.red
                                    null -> NiamBayColors.textDim
                                }
                            )
                    )
                    Text(
                        text = when (llmSource) {
                            LLMSource.OLLAMA -> "Local"
                            LLMSource.CLAUDE -> "Claude"
                            LLMSource.BRAIN_ONLY -> "Cerveau"
                            LLMSource.UNKNOWN -> "—"
                        },
                        color = NiamBayColors.textDim,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Compression NB-1
                if (compressionStats != null) {
                    Text(
                        text = "NB-1 ${compressionStats.savingsDisplay}",
                        color = NiamBayColors.orange,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

// ─── Message Bubble ─────────────────────────────────────────

@Composable
private fun MessageBubble(message: ChatMessage, isThinking: Boolean) {
    val isUser = message.role == Role.USER

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            modifier = Modifier.widthIn(max = 300.dp),
            color = if (isUser) NiamBayColors.userBubble else NiamBayColors.assistantBubble,
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = if (isUser) 16.dp else 4.dp,
                bottomEnd = if (isUser) 4.dp else 16.dp
            )
        ) {
            Text(
                text = message.content + if (message.content.isEmpty() && isThinking) "▊" else "",
                modifier = Modifier.padding(12.dp),
                color = if (isUser) Color(0xFFBFDBFE) else NiamBayColors.text,
                fontSize = 15.sp,
                lineHeight = 22.sp
            )
        }
    }
}

// ─── Input Bar ──────────────────────────────────────────────

@Composable
private fun InputBar(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: () -> Unit,
    enabled: Boolean
) {
    Surface(
        color = NiamBayColors.surface,
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                modifier = Modifier.weight(1f),
                placeholder = {
                    Text("Écris quelque chose...", color = NiamBayColors.textDim)
                },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = NiamBayColors.accent,
                    unfocusedBorderColor = NiamBayColors.border,
                    cursorColor = NiamBayColors.accent,
                    focusedTextColor = NiamBayColors.text,
                    unfocusedTextColor = NiamBayColors.text,
                    focusedContainerColor = Color(0xFF18181B),
                    unfocusedContainerColor = Color(0xFF18181B),
                ),
                shape = RoundedCornerShape(20.dp),
                maxLines = 4,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { onSend() }),
            )

            Button(
                onClick = onSend,
                enabled = text.isNotBlank() && enabled,
                modifier = Modifier.size(48.dp),
                shape = CircleShape,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = NiamBayColors.accent,
                    disabledContainerColor = NiamBayColors.border
                )
            ) {
                Text("↑", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
