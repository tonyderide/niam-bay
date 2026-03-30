/**
 * NIAM-BAY — Spreading Activation Orb
 *
 * Architecture visuelle ancrée dans les constantes réelles du cerveau
 * (cerveau-nb/core.py) :
 *
 *   4 anneaux  = MAX_HOPS 1-4
 *   opacités   = DAMPING_FACTOR^i  →  [1.0, 0.60, 0.36, 0.22]
 *   particules = 5 NodeTypes       →  CONCEPT / WORD / MEMORY / EMOTION / PATTERN
 *   firings    = onde hop-par-hop, atténuée DAMPING_FACTOR à chaque anneau
 *   noyau      = nœud "niam-bay" à 0.995 activation — ne s'éteint jamais
 *   watermark  = ញ (N khmer, "manger du riz") — présence, pas décor
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass }     from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

// ─── Constantes du cerveau (cerveau-nb/core.py) ──────────────────────────────
const BRAIN = {
  DAMPING_FACTOR:       0.6,
  MAX_HOPS:             4,
  FIRING_THRESHOLD:     0.8,
  REFRACTORY_PERIOD_S:  0.05,
};

// Opacités de base des anneaux = 0.6^i
const RING_DAMPING = Array.from(
  { length: BRAIN.MAX_HOPS },
  (_, i) => Math.pow(BRAIN.DAMPING_FACTOR, i)
); // [1.0, 0.60, 0.36, 0.216]

// ─── 5 NodeTypes (cerveau-nb/core.py NodeType enum) ─────────────────────────
const PARTICLE_TYPES = [
  { name: 'concept', color: new THREE.Color(0x00ffff), count: 80, speed: 1.0, shell: [0.88, 0.96] },
  { name: 'word',    color: new THREE.Color(0x4499ff), count: 60, speed: 0.7, shell: [0.92, 1.02] },
  { name: 'memory',  color: new THREE.Color(0xaa66ff), count: 50, speed: 0.5, shell: [0.96, 1.08] },
  { name: 'emotion', color: new THREE.Color(0xff8844), count: 40, speed: 1.3, shell: [0.84, 0.94] },
  { name: 'pattern', color: new THREE.Color(0x44ff88), count: 30, speed: 0.9, shell: [1.00, 1.12] },
];

// ─── États ───────────────────────────────────────────────────────────────────
const STATES = {
  idle: {
    ringColor:     new THREE.Color(0x0066cc),
    coreColor:     new THREE.Color(0x00aadd),
    bloom:          0.45,
    rotMult:        1.0,
    pulseFreq:      0.5,
    pulseAmp:       0.04,
    pulseShape:     'sin',
    firingWeights: [5, 1, 1, 1, 2],
    firingRate:     0.4,
    glowOp:         0.03,
    ringOp:         1.0,
  },
  listening: {
    ringColor:     new THREE.Color(0x00bbcc),
    coreColor:     new THREE.Color(0x00ddbb),
    bloom:          0.55,
    rotMult:        1.5,
    pulseFreq:      0.9,
    pulseAmp:       0.07,
    pulseShape:     'compound',
    firingWeights: [2, 2, 2, 5, 1],
    firingRate:     0.8,
    glowOp:         0.04,
    ringOp:         1.0,
  },
  thinking: {
    ringColor:     new THREE.Color(0x6611bb),
    coreColor:     new THREE.Color(0x9933ee),
    bloom:          0.80,
    rotMult:        4.0,
    pulseFreq:      2.5,
    pulseAmp:       0.14,
    pulseShape:     'burst',
    firingWeights: [5, 1, 2, 1, 5],
    firingRate:     4.0,
    glowOp:         0.06,
    ringOp:         1.0,
  },
  speaking: {
    ringColor:     new THREE.Color(0x00aa55),
    coreColor:     new THREE.Color(0x00dd77),
    bloom:          0.60,
    rotMult:        2.0,
    pulseFreq:      3.0,
    pulseAmp:       0.11,
    pulseShape:     'beat',
    firingWeights: [1, 5, 1, 2, 2],
    firingRate:     2.5,
    glowOp:         0.05,
    ringOp:         1.0,
  },
  alert: {
    ringColor:     new THREE.Color(0xcc2200),
    coreColor:     new THREE.Color(0xff2200),
    bloom:          1.0,
    rotMult:        6.0,
    pulseFreq:      6.0,
    pulseAmp:       0.20,
    pulseShape:     'spike',
    firingWeights: [2, 2, 3, 5, 4],
    firingRate:     8.0,
    glowOp:         0.08,
    ringOp:         1.0,
  },
};

// ─── Fresnel rim shaders ─────────────────────────────────────────────────────
const FRESNEL_VERT = `
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    vNormal   = normalize(normalMatrix * normal);
    vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
    vViewDir  = normalize(-mvPos.xyz);
    gl_Position = projectionMatrix * mvPos;
  }
`;
const FRESNEL_FRAG = `
  uniform vec3  uColor;
  uniform float uStrength;
  varying vec3  vNormal;
  varying vec3  vViewDir;
  void main() {
    float fresnel = pow(1.0 - abs(dot(vNormal, vViewDir)), 2.5);
    gl_FragColor  = vec4(uColor * 2.5, fresnel * uStrength);
  }
`;

// ─── Classe Orb ──────────────────────────────────────────────────────────────
export class Orb {
  constructor(canvas) {
    this.canvas = canvas;
    this.state  = 'idle';
    this.target = STATES.idle;

    // Valeurs interpolées
    this._lv = {
      bloom:     STATES.idle.bloom,
      rotMult:   STATES.idle.rotMult,
      pulseFreq: STATES.idle.pulseFreq,
      pulseAmp:  STATES.idle.pulseAmp,
      glowOp:    STATES.idle.glowOp,
      ringOp:    STATES.idle.ringOp,
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
    this._buildWavePool();
    this._buildWatermark();
    this._initFiring();
    this._initPost();
    this._animate();
  }

  // ── API publique ────────────────────────────────────────────────────────────
  setState(name) {
    if (STATES[name]) { this.state = name; this.target = STATES[name]; }
  }

  // ── Scène ───────────────────────────────────────────────────────────────────
  _initScene() {
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setClearColor(0x0a0a0f, 1);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.85;

    this.scene  = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 100);
    this.camera.position.set(0, 0, 4.2);

    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.composer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  // ── Noyau central (nœud "niam-bay" à 0.995 activation) ────────────────────
  _buildCore() {
    // Halo diffus extérieur
    this.glowMat = new THREE.MeshBasicMaterial({
      color: STATES.idle.coreColor.clone(),
      transparent: true, opacity: 0.03,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    this.glowMesh = new THREE.Mesh(new THREE.SphereGeometry(0.75, 32, 32), this.glowMat);
    this.group.add(this.glowMesh);

    // Sphère core (couleur état)
    this.coreMat = new THREE.MeshBasicMaterial({
      color: STATES.idle.coreColor.clone(),
      transparent: true, opacity: 0.88,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    this.coreMesh = new THREE.Mesh(new THREE.SphereGeometry(0.30, 32, 32), this.coreMat);
    this.group.add(this.coreMesh);

    // Centre blanc brûlant — 0.995 activation, jamais plein 1.0
    this.innerMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true, opacity: 0.92, // plafond 0.995 → ~0.92 visible
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    this.innerMesh = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 16), this.innerMat);
    this.group.add(this.innerMesh);

    // Fresnel rim — bord lumineux (Brainstorm Agent 5)
    this.fresnelUniforms = {
      uColor:    { value: STATES.idle.coreColor.clone() },
      uStrength: { value: 0.65 },
    };
    const fresnelMat = new THREE.ShaderMaterial({
      vertexShader:   FRESNEL_VERT,
      fragmentShader: FRESNEL_FRAG,
      uniforms:       this.fresnelUniforms,
      transparent:    true,
      blending:       THREE.AdditiveBlending,
      depthWrite:     false,
      side:           THREE.FrontSide,
    });
    this.fresnelMesh = new THREE.Mesh(new THREE.SphereGeometry(0.32, 32, 32), fresnelMat);
    this.group.add(this.fresnelMesh);
  }

  // ── 4 anneaux (MAX_HOPS, opacité DAMPING_FACTOR^i) ─────────────────────────
  _buildRings() {
    this.rings = [];
    const RING_DEFS = [
      { r: 0.52, tube: 0.018, rx: Math.PI / 2, ry: 0,            rz: 0,           spd:  0.38 },
      { r: 0.74, tube: 0.013, rx: Math.PI / 3, ry: Math.PI / 6,  rz: 0,           spd: -0.55 },
      { r: 0.96, tube: 0.010, rx: 0.20,        ry: Math.PI / 4,  rz: Math.PI / 5, spd:  0.24 },
      { r: 1.18, tube: 0.008, rx: Math.PI / 6, ry: 0,            rz: Math.PI / 3, spd: -0.14 },
    ];
    for (let i = 0; i < RING_DEFS.length; i++) {
      const d   = RING_DEFS[i];
      const mat = new THREE.MeshBasicMaterial({
        color: STATES.idle.ringColor.clone(),
        transparent: true,
        opacity: RING_DAMPING[i] * 0.75, // base = DAMPING_FACTOR^i
        blending: THREE.AdditiveBlending, depthWrite: false,
      });
      const mesh = new THREE.Mesh(new THREE.TorusGeometry(d.r, d.tube, 8, 128), mat);
      mesh.rotation.set(d.rx, d.ry, d.rz);
      mesh.userData.spd    = d.spd;
      mesh.userData.bx     = d.rx;
      mesh.userData.baseOp = RING_DAMPING[i] * 0.75;
      this.rings.push(mesh);
      this.group.add(mesh);
    }
  }

  // ── 5 groupes de particules (1 par NodeType) ────────────────────────────────
  _buildParticles() {
    this.particleGroups = [];
    for (let ti = 0; ti < PARTICLE_TYPES.length; ti++) {
      const pt  = PARTICLE_TYPES[ti];
      const pos = new Float32Array(pt.count * 3);
      for (let i = 0; i < pt.count; i++) {
        const [rMin, rMax] = pt.shell;
        const r     = rMin + Math.random() * (rMax - rMin);
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        pos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
        pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        pos[i * 3 + 2] = r * Math.cos(phi);
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      const mat = new THREE.PointsMaterial({
        color: pt.color.clone(),
        size: 0.022, transparent: true, opacity: 0.55,
        blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
      });
      const points       = new THREE.Points(geo, mat);
      points.userData.speed   = pt.speed;
      points.userData.typeIdx = ti;
      this.particleGroups.push(points);
      this.group.add(points);
    }
  }

  // ── Rayons (spokes) + triangle connecteur ───────────────────────────────────
  _buildSpokes() {
    this.spokeMat = new THREE.LineBasicMaterial({
      color: STATES.idle.ringColor.clone(),
      transparent: true, opacity: 0.28,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });

    // 6 spokes : centre → ring 1
    const sp = [];
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      sp.push(new THREE.Vector3(0, 0, 0));
      sp.push(new THREE.Vector3(Math.cos(a) * 0.50, Math.sin(a) * 0.50, 0));
    }
    // Triangle : ring 2 (hop 2)
    const tr = [];
    for (let i = 0; i < 3; i++) {
      const a1 = (i / 3) * Math.PI * 2;
      const a2 = ((i + 1) / 3) * Math.PI * 2;
      tr.push(new THREE.Vector3(Math.cos(a1) * 0.72, Math.sin(a1) * 0.72, 0));
      tr.push(new THREE.Vector3(Math.cos(a2) * 0.72, Math.sin(a2) * 0.72, 0));
    }

    const spokeLines = new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(sp), this.spokeMat);
    const triLines = new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(tr), this.spokeMat);
    triLines.rotation.x = Math.PI / 3;

    this.spokeGroup = new THREE.Group();
    this.spokeGroup.add(spokeLines, triLines);
    this.group.add(this.spokeGroup);
  }

  // ── Pool d'ondes de propagation (Brainstorm Agent 2 — depth rings) ──────────
  _buildWavePool() {
    this._waves = [];
    for (let i = 0; i < 8; i++) {
      const mat = new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        transparent: true, opacity: 0,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(new THREE.RingGeometry(0.28, 0.32, 64), mat);
      mesh.userData.active    = false;
      mesh.userData.startTime = 0;
      mesh.userData.typeIdx   = 0;
      this.group.add(mesh);
      this._waves.push(mesh);
    }
  }

  // ── Watermark ញ (khmer) — présence à peine visible ──────────────────────────
  _buildWatermark() {
    const size = 512;
    const cvs  = document.createElement('canvas');
    cvs.width = cvs.height = size;
    const ctx = cvs.getContext('2d');
    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = 'rgba(255,255,255,0.20)';
    ctx.font      = `bold ${Math.floor(size * 0.72)}px serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('ញ', size / 2, size / 2 + size * 0.05);

    const tex = new THREE.CanvasTexture(cvs);
    const mat = new THREE.MeshBasicMaterial({
      map: tex, transparent: true, opacity: 0.032,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 3.2), mat);
    mesh.position.z = -1.2; // derrière l'orb, ne suit pas la rotation du groupe
    this.scene.add(mesh);
  }

  // ── Post-processing ─────────────────────────────────────────────────────────
  _initPost() {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.45, 0.25, 0.88   // strength, radius, threshold — threshold haut = moins de saignement
    );
    this.composer.addPass(this.bloomPass);
  }

  // ── Système de firing ───────────────────────────────────────────────────────
  _initFiring() {
    this._firings     = []; // { typeIdx, startTime, amplitude }
    this._lastFire    = 0;
  }

  _triggerFiring(el) {
    const tgt = this.target;
    if (el - this._lastFire < 1 / tgt.firingRate) return;
    this._lastFire = el;

    // Choisir le NodeType selon firingWeights
    const w     = tgt.firingWeights;
    const total = w.reduce((a, b) => a + b, 0);
    let r = Math.random() * total;
    let typeIdx = 0;
    for (let i = 0; i < w.length; i++) { r -= w[i]; if (r <= 0) { typeIdx = i; break; } }

    const amp = BRAIN.FIRING_THRESHOLD + Math.random() * (1 - BRAIN.FIRING_THRESHOLD);
    this._firings.push({ typeIdx, startTime: el, amplitude: amp });
    this._firings = this._firings.filter(f => el - f.startTime < 1.8);

    // Activer une onde de profondeur (depth ring wave)
    const wave = this._waves.find(w => !w.userData.active);
    if (wave) {
      wave.userData.active    = true;
      wave.userData.startTime = el;
      wave.userData.typeIdx   = typeIdx;
      wave.scale.setScalar(1);
      wave.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      );
    }
  }

  _updateFirings(el) {
    // Reset opacités anneaux à leur base
    for (const ring of this.rings) {
      ring.userData.currentOp = ring.userData.baseOp;
    }

    // Appliquer chaque firing actif
    for (const f of this._firings) {
      const elapsed = el - f.startTime;
      for (let i = 0; i < this.rings.length; i++) {
        const hopDelay  = i * 0.12;                          // délai par hop
        const wElapsed  = elapsed - hopDelay;
        if (wElapsed < 0) continue;
        const dampAtten  = Math.pow(BRAIN.DAMPING_FACTOR, i);
        const envelope   = Math.exp(-wElapsed * 4.5);
        const wave       = f.amplitude * dampAtten * envelope;
        this.rings[i].userData.currentOp = Math.min(
          1.0, this.rings[i].userData.currentOp + wave * 0.85
        );
      }
    }

    // Appliquer + colorier
    for (const ring of this.rings) {
      ring.material.opacity = ring.userData.currentOp * this._lv.ringOp;
      ring.material.color.copy(this._lc.ring);
    }

    // Animer depth waves
    for (const wave of this._waves) {
      if (!wave.userData.active) continue;
      const age = el - wave.userData.startTime;
      if (age > 0.9) { wave.userData.active = false; wave.material.opacity = 0; continue; }
      const prog = age / 0.9;
      wave.scale.setScalar(0.3 + prog * 2.0);
      wave.material.opacity  = (1 - prog) * 0.28;
      wave.material.color.copy(PARTICLE_TYPES[wave.userData.typeIdx].color);
    }
  }

  // ── Pulse shape par état (Brainstorm Agent 3) ──────────────────────────────
  _pulse(el, freq, amp, shape) {
    const phase = el * freq * Math.PI * 2;
    switch (shape) {
      case 'burst':   return Math.abs(Math.sin(phase)) * amp;            // rafales neurales
      case 'beat':    return Math.sin(phase) * Math.sin(phase * 0.28) * amp; // phonémique
      case 'compound': return (Math.sin(phase) * 0.6 + Math.sin(phase * 2.1) * 0.4) * amp;
      case 'spike':   { const s = Math.sin(phase); return s * s * s * amp; } // pics aigus
      default:        return Math.sin(phase) * amp;                      // sin doux
    }
  }

  // ── Boucle d'animation ──────────────────────────────────────────────────────
  _animate() {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const clock = new THREE.Clock();
    const T = 0.04;

    const tick = () => {
      requestAnimationFrame(tick);
      if (reducedMotion) { this.composer.render(); return; }

      const el  = clock.getElapsedTime();
      const tgt = this.target;
      const lv  = this._lv;
      const lc  = this._lc;

      // ── Lerp scalaires ──
      lv.bloom     += (tgt.bloom     - lv.bloom)     * T;
      lv.rotMult   += (tgt.rotMult   - lv.rotMult)   * T;
      lv.pulseFreq += (tgt.pulseFreq - lv.pulseFreq) * T;
      lv.pulseAmp  += (tgt.pulseAmp  - lv.pulseAmp)  * T;
      lv.glowOp    += (tgt.glowOp    - lv.glowOp)    * T;
      lv.ringOp    += (tgt.ringOp    - lv.ringOp)    * T;

      // ── Lerp couleurs ──
      lc.core.lerp(tgt.coreColor, T);
      lc.ring.lerp(tgt.ringColor, T);

      // ── Bloom ──
      this.bloomPass.strength = lv.bloom;

      // ── Pulse (shape unique par état) ──
      const pv    = this._pulse(el, lv.pulseFreq, lv.pulseAmp, tgt.pulseShape);
      // Plafond 0.995 : niam-bay brûle mais n'atteint jamais le blanc absolu
      const coreS = Math.min(0.995, 1 + pv);
      this.coreMesh.scale.setScalar(coreS);
      this.innerMesh.scale.setScalar(coreS * 1.1);
      this.glowMesh.scale.setScalar(1 + pv * 0.35);

      // ── Couleurs noyau ──
      this.coreMat.color.copy(lc.core);
      this.glowMat.color.copy(lc.core);
      this.glowMat.opacity = lv.glowOp;
      this.fresnelUniforms.uColor.value.copy(lc.core);
      this.fresnelUniforms.uStrength.value = 0.55 + lv.glowOp * 1.2;

      // ── Spokes ──
      this.spokeMat.color.copy(lc.ring);
      this.spokeMat.opacity = lv.ringOp * 0.28;
      this.spokeGroup.rotation.y = el * 0.16 * lv.rotMult;
      this.spokeGroup.rotation.z = el * 0.07;

      // ── Rotation anneaux (opacité gérée par _updateFirings) ──
      for (const ring of this.rings) {
        ring.rotation.z += ring.userData.spd * lv.rotMult * 0.010;
        ring.rotation.x  = ring.userData.bx + Math.sin(el * 0.27 + ring.userData.spd) * 0.035;
      }

      // ── Firings + depth waves ──
      this._triggerFiring(el);
      this._updateFirings(el);

      // ── Particules ──
      for (const pg of this.particleGroups) {
        pg.rotation.y = el * 0.065 * lv.rotMult * pg.userData.speed;
        pg.rotation.x = el * 0.038 * pg.userData.speed;
        // Pulse propre à chaque type (déphasé)
        const phase = pg.userData.typeIdx * 1.3;
        pg.material.opacity = 0.42 + Math.sin(el * lv.pulseFreq * 0.6 + phase) * 0.15;
      }

      // ── Alert : vibration ──
      if (this.state === 'alert') {
        this.group.position.x = Math.sin(el * 32) * 0.009;
        this.group.position.y = Math.cos(el * 29) * 0.006;
      } else {
        this.group.position.x += (0 - this.group.position.x) * 0.12;
        const floatY = Math.sin(el * 0.42) * 0.055;
        this.group.position.y += (floatY - this.group.position.y) * 0.08;
      }

      // ── Respiration globale ──
      this.group.rotation.y = Math.sin(el * 0.14) * 0.06;
      this.group.rotation.x = Math.sin(el * 0.11) * 0.025;

      this.composer.render();
    };

    tick();
  }
}
