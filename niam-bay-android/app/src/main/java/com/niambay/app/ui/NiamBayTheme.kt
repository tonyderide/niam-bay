package com.niambay.app.ui

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ─── Couleurs Niam-Bay ──────────────────────────────────────

object NiamBayColors {
    val bg = Color(0xFF0A0A0F)
    val surface = Color(0xFF111118)
    val userBubble = Color(0xFF1A2744)
    val assistantBubble = Color(0xFF1A1A24)
    val accent = Color(0xFF3B82F6)
    val accentGlow = Color(0xFF60A5FA)
    val text = Color(0xFFE4E4E7)
    val textDim = Color(0xFF71717A)
    val border = Color(0xFF27272A)
    val green = Color(0xFF4ADE80)
    val red = Color(0xFFEF4444)
    val orange = Color(0xFFFB923C)
}

private val DarkColorScheme = darkColorScheme(
    primary = NiamBayColors.accent,
    secondary = NiamBayColors.accentGlow,
    background = NiamBayColors.bg,
    surface = NiamBayColors.surface,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onBackground = NiamBayColors.text,
    onSurface = NiamBayColors.text,
    outline = NiamBayColors.border,
)

@Composable
fun NiamBayTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
