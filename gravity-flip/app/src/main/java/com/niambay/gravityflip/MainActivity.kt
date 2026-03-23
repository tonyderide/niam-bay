package com.niambay.gravityflip

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier

class MainActivity : ComponentActivity() {

    private val engine = GameEngine()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Keep screen on during gameplay
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        enableEdgeToEdge()

        // Load high score
        val prefs = getSharedPreferences("gravity_flip", MODE_PRIVATE)
        engine.highScore = prefs.getInt("high_score", 0)

        setContent {
            GravityFlipApp(
                engine = engine,
                onHighScoreChanged = { newScore ->
                    prefs.edit().putInt("high_score", newScore).apply()
                }
            )
        }
    }
}

enum class GameState {
    MENU, PLAYING, GAME_OVER
}

@Composable
fun GravityFlipApp(
    engine: GameEngine,
    onHighScoreChanged: (Int) -> Unit
) {
    var gameState by remember { mutableStateOf(GameState.MENU) }
    var previousHighScore by remember { mutableIntStateOf(engine.highScore) }

    Box(modifier = Modifier.fillMaxSize()) {
        when (gameState) {
            GameState.MENU -> {
                MenuScreen(
                    highScore = engine.highScore,
                    onStartGame = {
                        engine.reset()
                        gameState = GameState.PLAYING
                    }
                )
            }

            GameState.PLAYING -> {
                GameScreen(
                    engine = engine,
                    onGameOver = {
                        if (engine.score > previousHighScore) {
                            onHighScoreChanged(engine.highScore)
                        }
                        gameState = GameState.GAME_OVER
                    }
                )
            }

            GameState.GAME_OVER -> {
                // Keep the game canvas visible behind the overlay
                GameScreen(
                    engine = engine,
                    onGameOver = {}
                )
                GameOverScreen(
                    score = engine.score,
                    highScore = engine.highScore,
                    isNewHighScore = engine.score > previousHighScore,
                    onRestart = {
                        previousHighScore = engine.highScore
                        engine.reset()
                        gameState = GameState.PLAYING
                    }
                )
            }
        }
    }
}
