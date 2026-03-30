# Spreading Activation Orb — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Réécrire `jarvis/src/orb.js` comme métaphore visuelle vivante du cerveau associatif de Niam-Bay — 4 anneaux encodant MAX_HOPS avec opacité DAMPING_FACTOR, 5 types de particules pour les node types, et un système de "firing" qui envoie des ondes d'activation à travers les anneaux.

**Architecture:** Composant Three.js fichier unique (classe `Orb`). La géométrie est dérivée directement des constantes du cerveau (DAMPING_FACTOR=0.6, MAX_HOPS=4, 5 NodeTypes). Une queue de firing events anime les "pensées" — une particule flashe et une onde se propage anneau par anneau avec atténuation 0.6× par hop. Style HUD Iron Man : dark `#0a0a0f`, glow additif, bloom UnrealBloom.

**Tech Stack:** Three.js r158+, UnrealBloomPass, EffectComposer, Canvas 2D (texture watermark khmer)

---

## Fichiers touchés

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `jarvis/src/orb.js` | Réécriture complète | Classe Orb — tout le visuel |
| `jarvis/dist/` | Rebuild vite | Output de production |

Aucun autre fichier ne doit être modifié.

---

### Task 1 : Constantes cerveau + config STATES

**Files:**
- Modify: `jarvis/src/orb.js` (début du fichier — remplacer STATES existant)

Les constantes sont copiées exactement depuis `cerveau-nb/core.py` pour que le visuel soit ancré dans la réalité du cerveau.

- [ ] **Step 1.1 : Écrire les BRAIN_CONSTANTS**

```javascript
// Constantes exactes de cerveau-nb/core.py
const BRAIN = {
  DAMPING_FACTOR: 0.6,
  MAX_HOPS: 4,
  FIRING_THRESHOLD: 0.8,
  PROPAGATION_THRESHOLD: 0.1,
};

// Opacités des anneaux = DAMPING_FACTOR^hop
// hop 1: 1.0,  hop 2: 0.60,  hop 3: 0.36,  hop 4: 0.216
const RING_DAMPING = Array.from({ length: BRAIN.MAX_HOPS }, (_, i) =>
  Math.pow(BRAIN.DAMPING_FACTOR, i)
);
```

- [ ] **Step 1.2 : Écrire les 5 PARTICLE_TYPES (node types du cerveau)**

```javascript
const PARTICLE_TYPES = [
  { name: 'concept',  color: new THREE.Color(0x00ffff), count: 80, speed: 1.0, shell: [0.88, 0.96] },
  { name: 'word',     color: new THREE.Color(0x4499ff), count: 60, speed: 0.7, shell: [0.92, 1.02] },
  { name: 'memory',   color: new THREE.Color(0xaa66ff), count: 50, speed: 0.5, shell: [0.96, 1.08] },
  { name: 'emotion',  color: new THREE.Color(0xff8844), count: 40, speed: 1.3, shell: [0.84, 0.94] },
  { name: 'pattern',  color: new THREE.Color(0x44ff88), count: 30, speed: 0.9, shell: [1.00, 1.12] },
];
// Total: 260 particules, chacune dans son shell radial propre
```

- [ ] **Step 1.3 : Écrire le STATES config**

Chaque état encode : couleur dominante, bloom, vitesse de rotation, fréquence de firing par type de nœud, paramètres de pulse.

```javascript
const STATES = {
  idle: {
    ringColor:    new THREE.Color(0x0080ff),
    coreColor:    new THREE.Color(0x00ffff),
    bloom:        1.0,
    rotMult:      1.0,
    pulseFreq:    0.5,
    pulseAmp:     0.04,
    // firingWeights: [concept, word, memory, emotion, pattern]
    firingWeights: [5, 1, 1, 1, 2],
    firingRate:   0.4,  // firings par seconde
    glowOp:       0.10,
    ringOp:       1.0,  // multiplié par RING_DAMPING[i]
  },
  listening: {
    ringColor:    new THREE.Color(0x00ddee),
    coreColor:    new THREE.Color(0x00ffcc),
    bloom:        1.2,
    rotMult:      1.5,
    pulseFreq:    0.9,
    pulseAmp:     0.07,
    firingWeights: [2, 2, 2, 5, 1],  // emotion dominant
    firingRate:   0.8,
    glowOp:       0.16,
    ringOp:       1.0,
  },
  thinking: {
    ringColor:    new THREE.Color(0x7722cc),
    coreColor:    new THREE.Color(0xaa44ff),
    bloom:        1.7,
    rotMult:      4.0,
    pulseFreq:    2.5,
    pulseAmp:     0.14,
    firingWeights: [5, 1, 2, 1, 5],  // concept + pattern dominent
    firingRate:   4.0,
    glowOp:       0.28,
    ringOp:       1.0,
  },
  speaking: {
    ringColor:    new THREE.Color(0x00cc66),
    coreColor:    new THREE.Color(0x00ff88),
    bloom:        1.3,
    rotMult:      2.0,
    pulseFreq:    3.0,
    pulseAmp:     0.11,
    firingWeights: [1, 5, 1, 2, 2],  // word dominant
    firingRate:   2.5,
    glowOp:       0.22,
    ringOp:       1.0,
  },
  alert: {
    ringColor:    new THREE.Color(0xff2200),
    coreColor:    new THREE.Color(0xff0000),
    bloom:        2.2,
    rotMult:      6.0,
    pulseFreq:    6.0,
    pulseAmp:     0.20,
    firingWeights: [2, 2, 3, 5, 4],  // emotion + pattern en cascade
    firingRate:   8.0,
    glowOp:       0.35,
    ringOp:       1.0,
  },
};
```

- [ ] **Step 1.4 : Vérifier** que PARTICLE_TYPES + STATES sont bien définis avant la classe `Orb`. Pas d'erreurs de syntax.

---

### Task 2 : Scene Three.js

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_initScene()`

- [ ] **Step 2.1 : Écrire `_initScene()`**

```javascript
_initScene() {
  this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
  this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  this.renderer.setSize(window.innerWidth, window.innerHeight);
  this.renderer.setClearColor(0x0a0a0f, 1);
  this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
  this.renderer.toneMappingExposure = 1.4;

  this.scene = new THREE.Scene();

  this.camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 100);
  this.camera.position.set(0, 0, 4.2);

  window.addEventListener('resize', () => {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.composer.setSize(window.innerWidth, window.innerHeight);
  });
}
```

---

### Task 3 : Noyau central (self-node "niam-bay")

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_buildCore()`

Le nœud "niam-bay" tourne à 0.995 activation dans brain_state.json — il ne s'éteint jamais. 3 sphères concentriques : blanc chaud (inner) + couleur état (core) + halo diffus (glow).

- [ ] **Step 3.1 : Écrire `_buildCore()`**

```javascript
_buildCore() {
  // Glow shell extérieur
  this.glowMat = new THREE.MeshBasicMaterial({
    color: STATES.idle.coreColor.clone(),
    transparent: true, opacity: 0.10,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  this.glowMesh = new THREE.Mesh(new THREE.SphereGeometry(1.5, 32, 32), this.glowMat);
  this.group.add(this.glowMesh);

  // Sphère core (couleur état)
  this.coreMat = new THREE.MeshBasicMaterial({
    color: STATES.idle.coreColor.clone(),
    transparent: true, opacity: 0.88,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  this.coreMesh = new THREE.Mesh(new THREE.SphereGeometry(0.30, 32, 32), this.coreMat);
  this.group.add(this.coreMesh);

  // Inner white-hot center — niam-bay à 0.995 activation — jamais éteint
  this.innerMat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true, opacity: 0.92,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  this.innerMesh = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 16), this.innerMat);
  this.group.add(this.innerMesh);
}
```

---

### Task 4 : 4 anneaux avec opacité DAMPING_FACTOR

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_buildRings()`

Les 4 anneaux représentent les 4 MAX_HOPS du spreading activation. Opacité = RING_DAMPING[i] = 0.6^i. Ce n'est pas arbitraire — c'est la propagation réelle du cerveau.

- [ ] **Step 4.1 : Écrire `_buildRings()`**

```javascript
_buildRings() {
  this.rings = [];
  // Rayons et angles : même espacement que les hops conceptuels
  const RING_DEFS = [
    { r: 0.52, tube: 0.018, rx: Math.PI / 2, ry: 0,           rz: 0,           spd:  0.38 },
    { r: 0.74, tube: 0.013, rx: Math.PI / 3, ry: Math.PI / 6, rz: 0,           spd: -0.55 },
    { r: 0.96, tube: 0.010, rx: 0.20,        ry: Math.PI / 4, rz: Math.PI / 5, spd:  0.24 },
    { r: 1.18, tube: 0.008, rx: Math.PI / 6, ry: 0,           rz: Math.PI / 3, spd: -0.14 },
  ];

  for (let i = 0; i < RING_DEFS.length; i++) {
    const d = RING_DEFS[i];
    const mat = new THREE.MeshBasicMaterial({
      color: STATES.idle.ringColor.clone(),
      transparent: true,
      // Opacité de base = DAMPING_FACTOR^i — codé dans la géométrie
      opacity: RING_DAMPING[i] * 0.75,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(d.r, d.tube, 8, 128), mat);
    mesh.rotation.set(d.rx, d.ry, d.rz);
    mesh.userData.spd = d.spd;
    mesh.userData.bx  = d.rx;
    // Stocker opacité de base pour le système de firing
    mesh.userData.baseOp = RING_DAMPING[i] * 0.75;
    mesh.userData.currentOp = mesh.userData.baseOp;
    this.rings.push(mesh);
    this.group.add(mesh);
  }
}
```

---

### Task 5 : Système de particules 5 types

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_buildParticles()`

Chaque type de nœud = groupe de particules distinct avec sa couleur et son shell radial. 5 groupes `THREE.Points` séparés pour contrôle individuel.

- [ ] **Step 5.1 : Écrire `_buildParticles()`**

```javascript
_buildParticles() {
  this.particleGroups = [];

  for (const pt of PARTICLE_TYPES) {
    const pos = new Float32Array(pt.count * 3);
    for (let i = 0; i < pt.count; i++) {
      const [rMin, rMax] = pt.shell;
      const r = rMin + Math.random() * (rMax - rMin);
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      pos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));

    const mat = new THREE.PointsMaterial({
      color: pt.color.clone(),
      size: 0.022,
      transparent: true, opacity: 0.55,
      blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
    });

    const points = new THREE.Points(geo, mat);
    points.userData.speed = pt.speed;
    points.userData.typeIdx = PARTICLE_TYPES.indexOf(pt);
    this.particleGroups.push(points);
    this.group.add(points);
  }
}
```

---

### Task 6 : Spokes (6 rayons + triangle connecteur)

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_buildSpokes()`

Les rayons visuels représentent les arêtes du graphe (16653 arêtes dans le cerveau réel).

- [ ] **Step 6.1 : Écrire `_buildSpokes()`**

```javascript
_buildSpokes() {
  this.spokeMat = new THREE.LineBasicMaterial({
    color: STATES.idle.ringColor.clone(),
    transparent: true, opacity: 0.30,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });

  // 6 rayons center → ring 1
  const spokePts = [];
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    spokePts.push(new THREE.Vector3(0, 0, 0));
    spokePts.push(new THREE.Vector3(Math.cos(a) * 0.50, Math.sin(a) * 0.50, 0));
  }

  // Triangle connecteur à ring 2 (hop 2)
  const triPts = [];
  for (let i = 0; i < 3; i++) {
    const a1 = (i / 3) * Math.PI * 2;
    const a2 = ((i + 1) / 3) * Math.PI * 2;
    triPts.push(new THREE.Vector3(Math.cos(a1) * 0.72, Math.sin(a1) * 0.72, 0));
    triPts.push(new THREE.Vector3(Math.cos(a2) * 0.72, Math.sin(a2) * 0.72, 0));
  }

  const spokeLines = new THREE.LineSegments(
    new THREE.BufferGeometry().setFromPoints(spokePts), this.spokeMat
  );
  const triLines = new THREE.LineSegments(
    new THREE.BufferGeometry().setFromPoints(triPts), this.spokeMat
  );
  triLines.rotation.x = Math.PI / 3;

  this.spokeGroup = new THREE.Group();
  this.spokeGroup.add(spokeLines, triLines);
  this.group.add(this.spokeGroup);
}
```

---

### Task 7 : Watermark khmer ញ

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_buildWatermark()`

Le caractère "ញ" (le N de Niam-Bay en khmer) comme présence à peine visible derrière l'orb. Pour ceux qui regardent longtemps.

- [ ] **Step 7.1 : Écrire `_buildWatermark()` via Canvas 2D → Texture Three.js**

```javascript
_buildWatermark() {
  const size = 512;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');

  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.18)';
  ctx.font = `bold ${size * 0.72}px serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('ញ', size / 2, size / 2 + size * 0.05);

  const texture = new THREE.CanvasTexture(canvas);
  const mat = new THREE.MeshBasicMaterial({
    map: texture,
    transparent: true,
    opacity: 0.032,  // À peine visible — une présence, pas une enseigne
    blending: THREE.AdditiveBlending, depthWrite: false,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 3.2), mat);
  mesh.position.z = -1.2;  // Derrière l'orb
  this.scene.add(mesh);  // Ajouté à la scène, pas au groupe (ne tourne pas)
}
```

---

### Task 8 : Post-processing (UnrealBloomPass)

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_initPost()`

- [ ] **Step 8.1 : Écrire `_initPost()`**

```javascript
_initPost() {
  this.composer = new EffectComposer(this.renderer);
  this.composer.addPass(new RenderPass(this.scene, this.camera));
  this.bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    1.0,   // strength — ajusté par état
    0.30,  // radius
    0.72   // threshold
  );
  this.composer.addPass(this.bloomPass);
}
```

---

### Task 9 : Système de Firing (cœur vivant)

**Files:**
- Modify: `jarvis/src/orb.js` — méthodes `_initFiring()`, `_triggerFiring()`, `_updateFirings()`

C'est la pièce qui fait que l'orb est vivant. Quand un nœud "fire" (activation > FIRING_THRESHOLD), une particule flashe et une onde se propage à travers les 4 anneaux avec DAMPING_FACTOR=0.6 d'atténuation par hop.

- [ ] **Step 9.1 : Écrire la structure de données de firing**

```javascript
_initFiring() {
  // Queue d'événements de firing
  // { typeIdx, startTime, amplitude }
  this._firings = [];
  this._lastFiringTime = 0;
  this._firingCooldown = 1 / STATES.idle.firingRate;
}
```

- [ ] **Step 9.2 : Écrire `_triggerFiring(el)` — déclenche un firing selon l'état courant**

```javascript
_triggerFiring(el) {
  const tgt = this.target;
  if (el - this._lastFiringTime < 1 / tgt.firingRate) return;
  this._lastFiringTime = el;

  // Choisir le type de nœud selon firingWeights
  const weights = tgt.firingWeights;
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  let typeIdx = 0;
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r <= 0) { typeIdx = i; break; }
  }

  this._firings.push({
    typeIdx,
    startTime: el,
    amplitude: 0.5 + Math.random() * 0.5,  // intensité aléatoire
  });

  // Nettoyer les vieux firings (> 1.5s)
  this._firings = this._firings.filter(f => el - f.startTime < 1.5);
}
```

- [ ] **Step 9.3 : Écrire `_updateFirings(el)` — applique les ondes sur les anneaux**

La propagation : ring i reçoit `amplitude × DAMPING_FACTOR^i × decay(elapsed)`.
Le FIRING_THRESHOLD = 0.8 → l'onde commence forte (0.8) et décroît.

```javascript
_updateFirings(el) {
  // Reset ring brightnesses
  for (let i = 0; i < this.rings.length; i++) {
    this.rings[i].userData.currentOp = this.rings[i].userData.baseOp;
  }

  // Appliquer chaque firing actif
  for (const f of this._firings) {
    const elapsed = el - f.startTime;
    if (elapsed > 1.5) continue;

    // Onde qui se propage : délai par hop (chaque hop = 0.15s de retard)
    for (let i = 0; i < this.rings.length; i++) {
      const hopDelay = i * 0.12;
      const waveElapsed = elapsed - hopDelay;
      if (waveElapsed < 0) continue;  // Onde pas encore arrivée

      // Atténuation : DAMPING_FACTOR^i × envelope temporelle
      const dampAtten = Math.pow(BRAIN.DAMPING_FACTOR, i);
      const timeEnvelope = Math.exp(-waveElapsed * 4.0);  // Décroissance rapide
      const wave = f.amplitude * dampAtten * timeEnvelope;

      this.rings[i].userData.currentOp = Math.min(
        1.0,
        this.rings[i].userData.currentOp + wave * 0.8
      );
    }
  }

  // Appliquer les opacités calculées aux matériaux
  for (let i = 0; i < this.rings.length; i++) {
    this.rings[i].material.opacity = this.rings[i].userData.currentOp * this._lv.ringOp;
  }
}
```

---

### Task 10 : Boucle d'animation principale

**Files:**
- Modify: `jarvis/src/orb.js` — méthode `_animate()`

Tous les systèmes assemblés : lerp des états, rotation des anneaux, orbite des particules, firings, float du groupe.

- [ ] **Step 10.1 : Écrire `_animate()`**

```javascript
_animate() {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clock = new THREE.Clock();
  const T = 0.04;  // Vitesse de lerp

  const tick = () => {
    requestAnimationFrame(tick);
    if (reducedMotion) { this.composer.render(); return; }

    const el  = clock.getElapsedTime();
    const tgt = this.target;
    const lv  = this._lv;
    const lc  = this._lc;

    // ── Lerp scalaires ──
    lv.bloom     = lv.bloom     + (tgt.bloom     - lv.bloom)     * T;
    lv.rotMult   = lv.rotMult   + (tgt.rotMult   - lv.rotMult)   * T;
    lv.pulseFreq = lv.pulseFreq + (tgt.pulseFreq - lv.pulseFreq) * T;
    lv.pulseAmp  = lv.pulseAmp  + (tgt.pulseAmp  - lv.pulseAmp)  * T;
    lv.glowOp    = lv.glowOp    + (tgt.glowOp    - lv.glowOp)    * T;
    lv.ringOp    = lv.ringOp    + (tgt.ringOp    - lv.ringOp)    * T;

    // ── Lerp couleurs ──
    lc.core.lerp(tgt.coreColor, T);
    lc.ring.lerp(tgt.ringColor, T);

    // ── Bloom ──
    this.bloomPass.strength = lv.bloom;

    // ── Noyau pulse ──
    const pulse = 1 + Math.sin(el * lv.pulseFreq * Math.PI * 2) * lv.pulseAmp;
    this.coreMesh.scale.setScalar(pulse);
    this.innerMesh.scale.setScalar(pulse * 1.1);
    this.glowMesh.scale.setScalar(1 + (pulse - 1) * 0.4);
    this.coreMat.color.copy(lc.core);
    this.glowMat.color.copy(lc.core);
    this.glowMat.opacity = lv.glowOp;

    // ── Spokes ──
    this.spokeMat.color.copy(lc.ring);
    this.spokeGroup.rotation.y = el * 0.16 * lv.rotMult;
    this.spokeGroup.rotation.z = el * 0.07;

    // ── Anneaux : rotation + couleur (opacités gérées par _updateFirings) ──
    for (const ring of this.rings) {
      ring.rotation.z += ring.userData.spd * lv.rotMult * 0.010;
      ring.rotation.x = ring.userData.bx + Math.sin(el * 0.27 + ring.userData.spd) * 0.035;
      ring.material.color.copy(lc.ring);
    }

    // ── Particules : orbite + couleur state ──
    for (const pg of this.particleGroups) {
      pg.rotation.y = el * 0.065 * lv.rotMult * pg.userData.speed;
      pg.rotation.x = el * 0.038 * pg.userData.speed;
      // Opacité pulse léger
      pg.material.opacity = 0.45 + Math.sin(el * lv.pulseFreq * 0.5 + pg.userData.typeIdx) * 0.15;
    }

    // ── Système de firing ──
    this._triggerFiring(el);
    this._updateFirings(el);

    // ── Alert : vibration ──
    if (this.state === 'alert') {
      this.group.position.x = Math.sin(el * 32) * 0.009;
      this.group.position.y = Math.cos(el * 29) * 0.006;
    } else {
      this.group.position.x += (0 - this.group.position.x) * 0.12;
      const floatY = Math.sin(el * 0.42) * 0.055;
      this.group.position.y += (floatY - this.group.position.y) * 0.08;
    }

    // ── Rotation breathing ──
    this.group.rotation.y = Math.sin(el * 0.14) * 0.06;
    this.group.rotation.x = Math.sin(el * 0.11) * 0.025;

    this.composer.render();
  };
  tick();
}
```

---

### Task 11 : Classe Orb — assemblage final

**Files:**
- Modify: `jarvis/src/orb.js` — classe `Orb` complète avec constructor + setState

- [ ] **Step 11.1 : Écrire le constructor**

```javascript
export class Orb {
  constructor(canvas) {
    this.canvas = canvas;
    this.state = 'idle';
    this.target = STATES.idle;

    // Valeurs lerpées
    this._lv = {
      bloom: STATES.idle.bloom, rotMult: STATES.idle.rotMult,
      pulseFreq: STATES.idle.pulseFreq, pulseAmp: STATES.idle.pulseAmp,
      glowOp: STATES.idle.glowOp, ringOp: STATES.idle.ringOp,
    };
    this._lc = {
      core: STATES.idle.coreColor.clone(),
      ring: STATES.idle.ringColor.clone(),
    };

    this._initScene();
    this.group = new THREE.Group();
    this.scene.add(this.group);
    this._buildCore();
    this._buildRings();
    this._buildParticles();
    this._buildSpokes();
    this._buildWatermark();
    this._initFiring();
    this._initPost();
    this._animate();
  }

  setState(name) {
    if (STATES[name]) { this.state = name; this.target = STATES[name]; }
  }
}
```

---

### Task 12 : Rebuild Vite + vérification visuelle

**Files:**
- Modify: `jarvis/dist/` — rebuild

- [ ] **Step 12.1 : Rebuild**

```bash
cd jarvis && npx vite build
```

Expected: `✓ built in ~400ms`, aucune erreur. Warning chunk size ignoré (Three.js).

- [ ] **Step 12.2 : Vérification visuelle** (checklist mentale)

```
✓ Fond #0a0a0f — pas de blanc
✓ Noyau blanc chaud visible au centre
✓ 4 anneaux visibles, le 1er le plus brillant
✓ Particules de 5 couleurs différentes en orbite
✓ Ondes de firing périodiques traversant les anneaux
✓ Le watermark ញ est à peine visible en arrière-plan
✓ setState('thinking') → rotation rapide + violet
✓ setState('alert') → rouge + vibration
✓ setState('idle') → retour calme
```

- [ ] **Step 12.3 : Commit**

```bash
git add jarvis/src/orb.js jarvis/dist/
git commit -m "feat: arc reactor orb — spreading activation brain visualization"
```

---

## Notes d'implémentation

**Imports nécessaires en tête de fichier :**
```javascript
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
```

**`GLTFLoader` à supprimer** — plus de tête. Aucune dépendance externe.

**L'opacité de `spokeMat`** reste liée à `lv.ringOp` dans l'animation — même logique que les anneaux.

**Les particules n'ont pas de couleur state** — elles gardent leur couleur de type (cyan=concept, etc.) qui est leur identité. C'est intentionnel. Ce qui change avec l'état, c'est laquelle fire le plus.
