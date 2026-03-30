/**
 * NIAM-BAY — Energy Core (Arc Reactor style)
 * Abstract energy orb: pulsing core, concentric rings, particle cloud
 * No face. Pure energy. Reacts to states.
 */
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

const STATES = {
  idle: {
    coreHex: 0x0066aa,
    ringHex: 0x0088cc,
    particleHex: 0x0099dd,
    bloom: 0.4,
    ringSpeed: 0.3,
    coreScale: 1.0,
    particleOpacity: 0.55,
    ringOpacity: 0.5,
  },
  listening: {
    coreHex: 0x00aabb,
    ringHex: 0x00ccdd,
    particleHex: 0x00eeff,
    bloom: 0.55,
    ringSpeed: 0.5,
    coreScale: 1.12,
    particleOpacity: 0.75,
    ringOpacity: 0.65,
  },
  thinking: {
    coreHex: 0x5522cc,
    ringHex: 0x7744ee,
    particleHex: 0x9966ff,
    bloom: 0.85,
    ringSpeed: 2.2,
    coreScale: 0.88,
    particleOpacity: 1.0,
    ringOpacity: 0.9,
  },
  speaking: {
    coreHex: 0x009944,
    ringHex: 0x00cc66,
    particleHex: 0x00ff88,
    bloom: 0.6,
    ringSpeed: 0.9,
    coreScale: 1.15,
    particleOpacity: 0.85,
    ringOpacity: 0.7,
  },
  alert: {
    coreHex: 0xcc1111,
    ringHex: 0xff2233,
    particleHex: 0xff4455,
    bloom: 1.1,
    ringSpeed: 3.5,
    coreScale: 1.25,
    particleOpacity: 1.0,
    ringOpacity: 1.0,
  },
};

const _tmpColor = new THREE.Color();

export class Orb {
  constructor(canvas) {
    this.canvas = canvas;
    this.state = 'idle';
    this.target = STATES.idle;
    this._cur = {
      ringSpeed: STATES.idle.ringSpeed,
      bloom: STATES.idle.bloom,
      coreScale: STATES.idle.coreScale,
      particleOpacity: STATES.idle.particleOpacity,
      ringOpacity: STATES.idle.ringOpacity,
    };

    this._initScene();
    this._buildOrb();
    this._initPost();
    this._animate();
  }

  _initScene() {
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setClearColor(0x060810, 1);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100);
    this.camera.position.set(0, 0, 3.8);

    this.scene.add(new THREE.AmbientLight(0x111122, 0.4));

    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.composer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  _buildOrb() {
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // ── 1. Core sphere ──
    this.coreMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(0x0066aa),
      emissive: new THREE.Color(0x0066aa),
      emissiveIntensity: 2.5,
      roughness: 0.15,
      metalness: 0.9,
    });
    this.core = new THREE.Mesh(new THREE.SphereGeometry(0.2, 32, 32), this.coreMat);
    this.group.add(this.core);

    // ── 2. Inner soft glow ──
    this.innerMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(0x0066aa),
      transparent: true,
      opacity: 0.12,
      side: THREE.BackSide,
    });
    this.inner = new THREE.Mesh(new THREE.SphereGeometry(0.32, 24, 24), this.innerMat);
    this.group.add(this.inner);

    // ── 3. Concentric rings ──
    this.rings = [];
    const ringDefs = [
      { r: 0.52, tube: 0.007, rx: 0,           ry: 0,            rz: 0 },
      { r: 0.68, tube: 0.006, rx: Math.PI / 3, ry: 0.4,          rz: 0.2 },
      { r: 0.84, tube: 0.005, rx: Math.PI / 5, ry: Math.PI / 4,  rz: -0.3 },
    ];

    for (const d of ringDefs) {
      const mat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(0x0088cc),
        transparent: true,
        opacity: 0.55,
      });
      const mesh = new THREE.Mesh(new THREE.TorusGeometry(d.r, d.tube, 6, 96), mat);
      mesh.rotation.set(d.rx, d.ry, d.rz);
      this.group.add(mesh);
      this.rings.push({ mesh, mat, base: { rx: d.rx, ry: d.ry, rz: d.rz } });
    }

    // ── 4. Particle cloud ──
    const N = 220;
    this._N = N;
    this._pTheta     = new Float32Array(N);
    this._pPhi       = new Float32Array(N);
    this._pR         = new Float32Array(N);
    this._pSpeed     = new Float32Array(N);
    this._pPhiOffset = new Float32Array(N);

    for (let i = 0; i < N; i++) {
      this._pTheta[i]     = Math.random() * Math.PI * 2;
      this._pPhi[i]       = Math.acos(2 * Math.random() - 1);
      this._pR[i]         = 0.58 + Math.random() * 0.52;
      this._pSpeed[i]     = 0.15 + Math.random() * 0.5;
      this._pPhiOffset[i] = Math.random() * Math.PI * 2;
    }

    const pPositions = new Float32Array(N * 3);
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));

    this.particleMat = new THREE.PointsMaterial({
      color: new THREE.Color(0x0099dd),
      size: 0.013,
      transparent: true,
      opacity: 0.55,
      sizeAttenuation: true,
    });
    this.particles = new THREE.Points(pGeo, this.particleMat);
    this.group.add(this.particles);

    // ── 5. Outer haze ──
    this.hazeMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(0x0066aa),
      transparent: true,
      opacity: 0.025,
      side: THREE.BackSide,
    });
    this.haze = new THREE.Mesh(new THREE.SphereGeometry(1.15, 16, 16), this.hazeMat);
    this.group.add(this.haze);
  }

  _initPost() {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.4, 0.3, 0.7
    );
    this.composer.addPass(this.bloomPass);
  }

  setState(name) {
    if (STATES[name]) { this.state = name; this.target = STATES[name]; }
  }

  _lerp(a, b, t) { return a + (b - a) * t; }
  _lerpColor(c, hex, t) { c.lerp(_tmpColor.setHex(hex), t); }

  _animate() {
    const clock = new THREE.Clock();
    const T = 0.045;

    const tick = () => {
      requestAnimationFrame(tick);
      const el  = clock.getElapsedTime();
      const tgt = this.target;
      const cur = this._cur;

      // ── Lerp scalars ──
      cur.ringSpeed       = this._lerp(cur.ringSpeed,       tgt.ringSpeed,       T);
      cur.bloom           = this._lerp(cur.bloom,           tgt.bloom,           T);
      cur.coreScale       = this._lerp(cur.coreScale,       tgt.coreScale,       T);
      cur.particleOpacity = this._lerp(cur.particleOpacity, tgt.particleOpacity, T);
      cur.ringOpacity     = this._lerp(cur.ringOpacity,     tgt.ringOpacity,     T);

      // ── Lerp colors ──
      this._lerpColor(this.coreMat.color,    tgt.coreHex, T);
      this._lerpColor(this.coreMat.emissive, tgt.coreHex, T);
      this._lerpColor(this.innerMat.color,   tgt.coreHex, T);
      this._lerpColor(this.hazeMat.color,    tgt.coreHex, T);
      for (const ring of this.rings) {
        this._lerpColor(ring.mat.color, tgt.ringHex, T);
        ring.mat.opacity = this._lerp(ring.mat.opacity, cur.ringOpacity, T);
      }
      this._lerpColor(this.particleMat.color, tgt.particleHex, T);
      this.particleMat.opacity = cur.particleOpacity;

      // ── Bloom ──
      this.bloomPass.strength = cur.bloom;

      // ── Core pulse ──
      let cs = cur.coreScale + Math.sin(el * 2.2) * 0.035;
      if (this.state === 'speaking') cs *= 1 + Math.abs(Math.sin(el * 5)) * 0.12;
      this.core.scale.setScalar(cs);
      this.inner.scale.setScalar(cs * 1.3 + Math.sin(el * 1.6) * 0.04);
      this.haze.scale.setScalar(cs * 0.95 + Math.sin(el * 0.7) * 0.04);

      // ── Ring rotation ──
      const spd = cur.ringSpeed;
      if (this.rings[0]) {
        this.rings[0].mesh.rotation.y = el * spd * 0.65;
        this.rings[0].mesh.rotation.x = this.rings[0].base.rx + el * spd * 0.25;
      }
      if (this.rings[1]) {
        this.rings[1].mesh.rotation.y = this.rings[1].base.ry + el * spd * -0.45;
        this.rings[1].mesh.rotation.z = this.rings[1].base.rz + el * spd * 0.35;
      }
      if (this.rings[2]) {
        this.rings[2].mesh.rotation.x = this.rings[2].base.rx + el * spd * 0.55;
        this.rings[2].mesh.rotation.z = el * spd * -0.28;
      }

      // ── Listening: rings breathe ──
      if (this.state === 'listening') {
        const breathe = 1 + Math.sin(el * 1.8) * 0.07;
        this.rings.forEach(r => r.mesh.scale.setScalar(breathe));
      } else {
        this.rings.forEach(r => r.mesh.scale.setScalar(1));
      }

      // ── Particle orbital motion ──
      const pPos = this.particles.geometry.attributes.position;
      const pSpeedMul = 0.25 + spd * 0.18;
      for (let i = 0; i < this._N; i++) {
        this._pTheta[i] += pSpeedMul * this._pSpeed[i] * 0.012;
        const r   = this._pR[i] + Math.sin(el * 0.6 + i * 0.3) * 0.04;
        const phi = this._pPhi[i] + Math.sin(el * 0.25 + this._pPhiOffset[i]) * 0.08;
        pPos.setXYZ(
          i,
          r * Math.sin(phi) * Math.cos(this._pTheta[i]),
          r * Math.sin(phi) * Math.sin(this._pTheta[i]),
          r * Math.cos(phi)
        );
      }
      pPos.needsUpdate = true;

      // ── Group gentle float & slow spin ──
      this.group.position.y = Math.sin(el * 0.35) * 0.04;
      this.group.rotation.y = el * 0.04;

      this.composer.render();
    };
    tick();
  }
}

