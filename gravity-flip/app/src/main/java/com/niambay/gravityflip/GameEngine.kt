package com.niambay.gravityflip

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

data class Obstacle(
    var x: Float,          // 0..1 normalized position from left
    val gapCenter: Float,  // 0..1 normalized vertical center of gap
    val gapHeight: Float   // 0..1 normalized height of gap
) {
    var scored: Boolean = false
}

data class Particle(
    var x: Float,
    var y: Float,
    var vx: Float,
    var vy: Float,
    var life: Float,       // 1.0 = alive, 0.0 = dead
    var decay: Float,
    var size: Float,
    val isCyan: Boolean
)

class GameEngine {
    // Player state
    var playerY = 0.5f          // 0 = top, 1 = bottom (normalized)
    var velocity = 0f           // normalized units per second
    var gravity = 1f            // 1 = down, -1 = up
    var playerX = 0.15f         // fixed horizontal position

    // Game state
    var score = 0
    var gameOver = false
    var gameStarted = false
    var speed = 0.25f           // obstacle scroll speed (normalized units/sec)

    // Obstacles
    val obstacles = mutableListOf<Obstacle>()
    private var obstacleTimer = 0f
    private var obstacleInterval = 2.0f  // seconds between obstacles

    // Particles
    val particles = mutableListOf<Particle>()

    // Visual effects
    var flipFlashAlpha = 0f
    var screenShakeX = 0f
    var screenShakeY = 0f
    var deathFlashAlpha = 0f

    // Constants
    private val gravityStrength = 1.8f
    private val maxVelocity = 1.5f
    private val playerSize = 0.04f       // normalized size of player square
    private val obstacleWidth = 0.06f    // normalized width of obstacle bars
    private val minGapHeight = 0.18f
    private val maxGapHeight = 0.30f

    // High score
    var highScore = 0

    fun reset() {
        playerY = 0.5f
        velocity = 0f
        gravity = 1f
        score = 0
        speed = 0.25f
        gameOver = false
        gameStarted = true
        obstacles.clear()
        particles.clear()
        obstacleTimer = 0f
        obstacleInterval = 2.0f
        flipFlashAlpha = 0f
        screenShakeX = 0f
        screenShakeY = 0f
        deathFlashAlpha = 0f
    }

    fun flipGravity() {
        if (gameOver || !gameStarted) return
        gravity *= -1f
        flipFlashAlpha = 0.4f

        // Spawn flip particles
        repeat(6) {
            particles.add(
                Particle(
                    x = playerX,
                    y = playerY,
                    vx = Random.nextFloat() * 0.3f - 0.15f,
                    vy = Random.nextFloat() * 0.3f - 0.15f,
                    life = 1f,
                    decay = Random.nextFloat() * 1.5f + 2f,
                    size = Random.nextFloat() * 0.008f + 0.004f,
                    isCyan = true
                )
            )
        }
    }

    fun update(deltaTime: Float) {
        if (!gameStarted || gameOver) return

        val dt = min(deltaTime, 0.05f)  // cap delta to avoid physics explosions

        // --- Physics ---
        velocity += gravity * gravityStrength * dt
        velocity = velocity.coerceIn(-maxVelocity, maxVelocity)
        playerY += velocity * dt

        // Clamp to screen bounds — hitting ceiling/floor = game over
        if (playerY - playerSize / 2 < 0f) {
            playerY = playerSize / 2
            velocity = 0f
        }
        if (playerY + playerSize / 2 > 1f) {
            playerY = 1f - playerSize / 2
            velocity = 0f
        }

        // --- Trail particles ---
        if (Random.nextFloat() < 0.6f) {
            particles.add(
                Particle(
                    x = playerX - playerSize / 2,
                    y = playerY + Random.nextFloat() * playerSize - playerSize / 2,
                    vx = -Random.nextFloat() * 0.05f - 0.02f,
                    vy = Random.nextFloat() * 0.04f - 0.02f,
                    life = 1f,
                    decay = Random.nextFloat() * 2f + 3f,
                    size = Random.nextFloat() * 0.005f + 0.002f,
                    isCyan = true
                )
            )
        }

        // --- Obstacles ---
        obstacleTimer += dt
        if (obstacleTimer >= obstacleInterval) {
            obstacleTimer = 0f
            spawnObstacle()
        }

        for (obs in obstacles) {
            obs.x -= speed * dt
        }

        // Remove off-screen obstacles
        obstacles.removeAll { it.x < -obstacleWidth * 2 }

        // --- Collision detection ---
        for (obs in obstacles) {
            if (checkCollision(obs)) {
                triggerDeath()
                return
            }

            // Score: obstacle passed player
            if (!obs.scored && obs.x + obstacleWidth / 2 < playerX - playerSize / 2) {
                obs.scored = true
                score++
            }
        }

        // --- Difficulty scaling ---
        speed = 0.25f + score * 0.012f
        obstacleInterval = max(0.9f, 2.0f - score * 0.05f)

        // --- Update particles ---
        for (p in particles) {
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= p.decay * dt
        }
        particles.removeAll { it.life <= 0f }

        // --- Visual effects decay ---
        flipFlashAlpha = max(0f, flipFlashAlpha - dt * 3f)
        screenShakeX *= 0.85f
        screenShakeY *= 0.85f
        deathFlashAlpha = max(0f, deathFlashAlpha - dt * 4f)
    }

    private fun spawnObstacle() {
        val difficultyFactor = min(score / 30f, 1f)
        val gapHeight = maxGapHeight - (maxGapHeight - minGapHeight) * difficultyFactor * 0.6f
        val margin = gapHeight / 2 + 0.05f
        val gapCenter = Random.nextFloat() * (1f - 2 * margin) + margin

        obstacles.add(Obstacle(x = 1.1f, gapCenter = gapCenter, gapHeight = gapHeight))
    }

    private fun checkCollision(obs: Obstacle): Boolean {
        val pLeft = playerX - playerSize / 2
        val pRight = playerX + playerSize / 2
        val pTop = playerY - playerSize / 2
        val pBottom = playerY + playerSize / 2

        val oLeft = obs.x - obstacleWidth / 2
        val oRight = obs.x + obstacleWidth / 2

        // Check horizontal overlap
        if (pRight <= oLeft || pLeft >= oRight) return false

        // Check if player is in the gap (safe zone)
        val gapTop = obs.gapCenter - obs.gapHeight / 2
        val gapBottom = obs.gapCenter + obs.gapHeight / 2

        // Collision if player is above the gap or below the gap
        if (pTop < gapTop || pBottom > gapBottom) return true

        return false
    }

    private fun triggerDeath() {
        gameOver = true
        if (score > highScore) {
            highScore = score
        }

        // Screen shake
        screenShakeX = (Random.nextFloat() - 0.5f) * 0.03f
        screenShakeY = (Random.nextFloat() - 0.5f) * 0.03f
        deathFlashAlpha = 0.6f

        // Death explosion particles
        repeat(40) {
            val angle = Random.nextFloat() * Math.PI.toFloat() * 2
            val spd = Random.nextFloat() * 0.5f + 0.1f
            particles.add(
                Particle(
                    x = playerX,
                    y = playerY,
                    vx = kotlin.math.cos(angle) * spd,
                    vy = kotlin.math.sin(angle) * spd,
                    life = 1f,
                    decay = Random.nextFloat() * 1f + 1f,
                    size = Random.nextFloat() * 0.01f + 0.004f,
                    isCyan = Random.nextBoolean()
                )
            )
        }
    }

    fun getPlayerSize(): Float = playerSize
    fun getObstacleWidth(): Float = obstacleWidth
}
