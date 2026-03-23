package com.niambay.gravityflip

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun GameOverScreen(
    score: Int,
    highScore: Int,
    isNewHighScore: Boolean,
    onRestart: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "gameOver")

    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "restartPulse"
    )

    // Entrance animation
    val enterAlpha by animateFloatAsState(
        targetValue = 1f,
        animationSpec = tween(600, easing = EaseOutCubic),
        label = "enterAlpha"
    )

    val scoreScale by animateFloatAsState(
        targetValue = 1f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "scoreScale"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.7f * enterAlpha))
            .pointerInput(Unit) {
                detectTapGestures { onRestart() }
            },
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier
                .alpha(enterAlpha)
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // GAME OVER title
            Text(
                text = "GAME OVER",
                style = TextStyle(
                    color = GravityColors.DeathFlash,
                    fontSize = 42.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 6.sp,
                    shadow = Shadow(
                        color = GravityColors.DeathFlash.copy(alpha = 0.5f),
                        offset = Offset(0f, 0f),
                        blurRadius = 20f
                    )
                )
            )

            Spacer(modifier = Modifier.height(40.dp))

            // Score
            Text(
                text = "SCORE",
                style = TextStyle(
                    color = GravityColors.MenuSubtext,
                    fontSize = 16.sp,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 4.sp
                )
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "$score",
                style = TextStyle(
                    color = GravityColors.Player,
                    fontSize = (72 * scoreScale).sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    shadow = Shadow(
                        color = GravityColors.Player.copy(alpha = 0.5f),
                        offset = Offset(0f, 0f),
                        blurRadius = 25f
                    )
                )
            )

            Spacer(modifier = Modifier.height(16.dp))

            // New high score badge
            if (isNewHighScore && score > 0) {
                Text(
                    text = "NEW BEST!",
                    style = TextStyle(
                        color = Color(0xFFFFD700),
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 3.sp,
                        shadow = Shadow(
                            color = Color(0xFFFFD700).copy(alpha = 0.5f),
                            offset = Offset(0f, 0f),
                            blurRadius = 15f
                        )
                    )
                )
            } else {
                Text(
                    text = "BEST: $highScore",
                    style = TextStyle(
                        color = GravityColors.MenuSubtext,
                        fontSize = 18.sp,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 2.sp
                    )
                )
            }

            Spacer(modifier = Modifier.height(50.dp))

            // Tap to restart
            Text(
                text = "TAP TO RESTART",
                modifier = Modifier.alpha(pulseAlpha),
                style = TextStyle(
                    color = Color.White,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 3.sp
                )
            )
        }
    }
}
