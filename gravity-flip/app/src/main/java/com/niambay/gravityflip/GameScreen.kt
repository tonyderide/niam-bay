package com.niambay.gravityflip

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.isActive

@Composable
fun GameScreen(
    engine: GameEngine,
    onGameOver: () -> Unit
) {
    val textMeasurer = rememberTextMeasurer()
    var frameTime by remember { mutableLongStateOf(0L) }

    // Game loop
    LaunchedEffect(engine.gameStarted, engine.gameOver) {
        if (!engine.gameStarted || engine.gameOver) return@LaunchedEffect
        var lastTime = withFrameNanos { it }
        while (isActive && engine.gameStarted && !engine.gameOver) {
            val currentTime = withFrameNanos { it }
            val dt = (currentTime - lastTime) / 1_000_000_000f
            lastTime = currentTime
            engine.update(dt)
            frameTime = currentTime  // trigger recomposition
            if (engine.gameOver) {
                onGameOver()
            }
        }
    }

    // Keep recomposing during death animation
    LaunchedEffect(engine.gameOver) {
        if (!engine.gameOver) return@LaunchedEffect
        var lastTime = withFrameNanos { it }
        while (isActive && engine.deathFlashAlpha > 0.01f || engine.particles.isNotEmpty()) {
            val currentTime = withFrameNanos { it }
            val dt = (currentTime - lastTime) / 1_000_000_000f
            lastTime = currentTime
            // Update particles and effects even after death
            for (p in engine.particles) {
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.life -= p.decay * dt
            }
            engine.particles.removeAll { it.life <= 0f }
            engine.deathFlashAlpha = maxOf(0f, engine.deathFlashAlpha - dt * 4f)
            engine.screenShakeX *= 0.85f
            engine.screenShakeY *= 0.85f
            frameTime = currentTime
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(GravityColors.Background)
            .pointerInput(engine.gameStarted, engine.gameOver) {
                detectTapGestures {
                    if (engine.gameStarted && !engine.gameOver) {
                        engine.flipGravity()
                    }
                }
            }
    ) {
        // Use frameTime to ensure recomposition
        @Suppress("UNUSED_VARIABLE")
        val tick = frameTime

        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height
            val shakeX = engine.screenShakeX * w
            val shakeY = engine.screenShakeY * h

            // --- Background grid lines (subtle) ---
            drawBackgroundGrid(w, h)

            // --- Obstacles ---
            for (obs in engine.obstacles) {
                drawObstacle(obs, engine.getObstacleWidth(), w, h, shakeX, shakeY)
            }

            // --- Particles ---
            for (p in engine.particles) {
                if (p.life > 0f) {
                    val alpha = p.life.coerceIn(0f, 1f)
                    val color = if (p.isCyan) GravityColors.Player else GravityColors.Obstacle
                    drawCircle(
                        color = color.copy(alpha = alpha),
                        radius = p.size * w,
                        center = Offset(
                            p.x * w + shakeX,
                            p.y * h + shakeY
                        )
                    )
                }
            }

            // --- Player ---
            if (!engine.gameOver || engine.deathFlashAlpha > 0.1f) {
                drawPlayer(engine, w, h, shakeX, shakeY)
            }

            // --- Flip flash ---
            if (engine.flipFlashAlpha > 0f) {
                drawRect(
                    color = GravityColors.FlashWhite.copy(alpha = engine.flipFlashAlpha),
                    size = size
                )
            }

            // --- Death flash ---
            if (engine.deathFlashAlpha > 0f) {
                drawRect(
                    color = GravityColors.DeathFlash.copy(alpha = engine.deathFlashAlpha),
                    size = size
                )
            }

            // --- Score ---
            val scoreText = engine.score.toString()
            val scoreLayout = textMeasurer.measure(
                scoreText,
                TextStyle(
                    color = GravityColors.ScoreText,
                    fontSize = 48.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            )
            drawText(
                scoreLayout,
                topLeft = Offset(
                    (w - scoreLayout.size.width) / 2,
                    h * 0.06f
                )
            )

            // --- Gravity indicator ---
            drawGravityIndicator(engine, w, h)
        }
    }
}

private fun DrawScope.drawBackgroundGrid(w: Float, h: Float) {
    val gridColor = Color(0x0AFFFFFF)
    val spacing = w / 15f
    var x = 0f
    while (x < w) {
        drawLine(gridColor, Offset(x, 0f), Offset(x, h), strokeWidth = 1f)
        x += spacing
    }
    var y = 0f
    while (y < h) {
        drawLine(gridColor, Offset(0f, y), Offset(w, y), strokeWidth = 1f)
        y += spacing
    }
}

private fun DrawScope.drawObstacle(
    obs: Obstacle, obsWidth: Float, w: Float, h: Float,
    shakeX: Float, shakeY: Float
) {
    val left = obs.x * w - obsWidth * w / 2 + shakeX
    val right = obs.x * w + obsWidth * w / 2 + shakeX
    val gapTop = (obs.gapCenter - obs.gapHeight / 2) * h + shakeY
    val gapBottom = (obs.gapCenter + obs.gapHeight / 2) * h + shakeY
    val barWidth = right - left

    // Glow behind obstacles
    val glowPad = 6f
    drawRect(
        color = GravityColors.ObstacleGlow,
        topLeft = Offset(left - glowPad, 0f + shakeY),
        size = Size(barWidth + glowPad * 2, gapTop - shakeY)
    )
    drawRect(
        color = GravityColors.ObstacleGlow,
        topLeft = Offset(left - glowPad, gapBottom),
        size = Size(barWidth + glowPad * 2, h - gapBottom + shakeY)
    )

    // Top bar
    drawRect(
        color = GravityColors.Obstacle,
        topLeft = Offset(left, 0f + shakeY),
        size = Size(barWidth, gapTop - shakeY)
    )
    // Bottom bar
    drawRect(
        color = GravityColors.Obstacle,
        topLeft = Offset(left, gapBottom),
        size = Size(barWidth, h - gapBottom + shakeY)
    )
}

private fun DrawScope.drawPlayer(
    engine: GameEngine, w: Float, h: Float,
    shakeX: Float, shakeY: Float
) {
    val playerSize = engine.getPlayerSize()
    val px = engine.playerX * w + shakeX
    val py = engine.playerY * h + shakeY
    val halfSize = playerSize * w / 2

    // Outer glow
    drawRect(
        color = GravityColors.PlayerGlow,
        topLeft = Offset(px - halfSize - 8f, py - halfSize - 8f),
        size = Size(halfSize * 2 + 16f, halfSize * 2 + 16f)
    )

    // Main player square
    drawRect(
        color = GravityColors.Player,
        topLeft = Offset(px - halfSize, py - halfSize),
        size = Size(halfSize * 2, halfSize * 2)
    )

    // Inner highlight
    val innerPad = halfSize * 0.3f
    drawRect(
        color = Color.White.copy(alpha = 0.3f),
        topLeft = Offset(px - halfSize + innerPad, py - halfSize + innerPad),
        size = Size((halfSize - innerPad) * 2, (halfSize - innerPad) * 2)
    )
}

private fun DrawScope.drawGravityIndicator(engine: GameEngine, w: Float, h: Float) {
    val arrowX = w * 0.06f
    val arrowY = h * 0.08f
    val arrowLen = 20f
    val color = GravityColors.Player.copy(alpha = 0.5f)

    if (engine.gravity > 0) {
        // Down arrow
        drawLine(color, Offset(arrowX, arrowY - arrowLen / 2), Offset(arrowX, arrowY + arrowLen / 2), 2f)
        drawLine(color, Offset(arrowX - 6f, arrowY + arrowLen / 2 - 8f), Offset(arrowX, arrowY + arrowLen / 2), 2f)
        drawLine(color, Offset(arrowX + 6f, arrowY + arrowLen / 2 - 8f), Offset(arrowX, arrowY + arrowLen / 2), 2f)
    } else {
        // Up arrow
        drawLine(color, Offset(arrowX, arrowY - arrowLen / 2), Offset(arrowX, arrowY + arrowLen / 2), 2f)
        drawLine(color, Offset(arrowX - 6f, arrowY - arrowLen / 2 + 8f), Offset(arrowX, arrowY - arrowLen / 2), 2f)
        drawLine(color, Offset(arrowX + 6f, arrowY - arrowLen / 2 + 8f), Offset(arrowX, arrowY - arrowLen / 2), 2f)
    }
}
