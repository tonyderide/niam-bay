package com.niambay.gravityflip

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.random.Random

@Composable
fun MenuScreen(
    highScore: Int,
    onStartGame: () -> Unit
) {
    // Pulsing animation for "TAP TO START"
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    // Title glow animation
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glowAlpha"
    )

    // Background floating particles
    val bgParticles = remember {
        List(20) {
            BgParticle(
                x = Random.nextFloat(),
                y = Random.nextFloat(),
                speed = Random.nextFloat() * 0.02f + 0.005f,
                size = Random.nextFloat() * 4f + 2f,
                isCyan = Random.nextBoolean()
            )
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(GravityColors.Background)
            .pointerInput(Unit) {
                detectTapGestures { onStartGame() }
            }
    ) {
        // Animated background particles
        var tick by remember { mutableLongStateOf(0L) }
        LaunchedEffect(Unit) {
            while (true) {
                withFrameNanos { tick = it }
            }
        }

        @Suppress("UNUSED_VARIABLE")
        val currentTick = tick
        Canvas(modifier = Modifier.fillMaxSize()) {
            for (p in bgParticles) {
                p.y -= p.speed * 0.016f
                if (p.y < -0.02f) {
                    p.y = 1.02f
                    p.x = Random.nextFloat()
                }
                drawCircle(
                    color = if (p.isCyan) GravityColors.Player.copy(alpha = 0.3f)
                    else GravityColors.Obstacle.copy(alpha = 0.2f),
                    radius = p.size,
                    center = Offset(p.x * size.width, p.y * size.height)
                )
            }
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Spacer(modifier = Modifier.weight(1f))

            // Title
            Text(
                text = "GRAVITY",
                style = TextStyle(
                    color = GravityColors.Player.copy(alpha = glowAlpha),
                    fontSize = 56.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 12.sp,
                    shadow = Shadow(
                        color = GravityColors.Player.copy(alpha = 0.6f),
                        offset = Offset(0f, 0f),
                        blurRadius = 30f
                    )
                )
            )
            Text(
                text = "FLIP",
                style = TextStyle(
                    color = GravityColors.Obstacle.copy(alpha = glowAlpha),
                    fontSize = 56.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 20.sp,
                    shadow = Shadow(
                        color = GravityColors.Obstacle.copy(alpha = 0.6f),
                        offset = Offset(0f, 0f),
                        blurRadius = 30f
                    )
                )
            )

            Spacer(modifier = Modifier.height(60.dp))

            // Tap to start
            Text(
                text = "TAP TO START",
                modifier = Modifier.alpha(pulseAlpha),
                style = TextStyle(
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Medium,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 4.sp
                )
            )

            Spacer(modifier = Modifier.height(40.dp))

            // High score
            if (highScore > 0) {
                Text(
                    text = "BEST: $highScore",
                    style = TextStyle(
                        color = GravityColors.MenuSubtext,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Normal,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 2.sp
                    )
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Credit
            Text(
                text = "NIAM-BAY",
                style = TextStyle(
                    color = GravityColors.MenuSubtext.copy(alpha = 0.4f),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Light,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 6.sp,
                    textAlign = TextAlign.Center
                )
            )

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

private class BgParticle(
    var x: Float,
    var y: Float,
    val speed: Float,
    val size: Float,
    val isCyan: Boolean
)
