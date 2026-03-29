/**
 * NIAM-BAY — Digital Face (Lawnmower Man style)
 * Low-poly metallic face with glowing edges and flat shading
 */
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const STATES = {
  idle: {
    faceColor: 0x0a1828,
    edgeColor: new THREE.Color(0x2288cc),
    emissive: 0x050a12,
    bloom: 0.35,
    dotOpacity: 0.8,
  },
  listening: {
    faceColor: 0x0c1e30,
    edgeColor: new THREE.Color(0x33cccc),
    emissive: 0x081018,
    bloom: 0.45,
    dotOpacity: 0.9,
  },
  thinking: {
    faceColor: 0x140e28,
    edgeColor: new THREE.Color(0x8866ee),
    emissive: 0x0a0818,
    bloom: 0.55,
    dotOpacity: 1.0,
  },
  speaking: {
    faceColor: 0x0a1e1a,
    edgeColor: new THREE.Color(0x22cc88),
    emissive: 0x060f0c,
    bloom: 0.45,
    dotOpacity: 0.9,
  },
  alert: {
    faceColor: 0x280a0a,
    edgeColor: new THREE.Color(0xee4444),
    emissive: 0x180505,
    bloom: 0.65,
    dotOpacity: 1.0,
  },
};

export class Orb {
  constructor(canvas) {
    this.canvas = canvas;
    this.state = 'idle';
    this.target = STATES.idle;

    this._initScene();
    this._loadHead();
    this._initPost();
    this._animate();
  }

  _initScene() {
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setClearColor(0x060a10, 1);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    this.scene = new THREE.Scene();

    // Camera — framed on face
    this.camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 50);
    this.camera.position.set(0, 0.05, 2.6);

    // Lighting — dramatic, cinematic
    this.scene.add(new THREE.AmbientLight(0x111822, 0.8));

    const key = new THREE.DirectionalLight(0x6688bb, 1.5);
    key.position.set(2, 2, 4);
    this.scene.add(key);

    const fill = new THREE.DirectionalLight(0x334466, 0.6);
    fill.position.set(-3, 0, 2);
    this.scene.add(fill);

    const rim = new THREE.DirectionalLight(0x4466aa, 0.8);
    rim.position.set(0, 1, -3);
    this.scene.add(rim);

    const bottom = new THREE.DirectionalLight(0x223344, 0.3);
    bottom.position.set(0, -2, 1);
    this.scene.add(bottom);

    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.composer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  _loadHead() {
    this.headGroup = new THREE.Group();
    this.scene.add(this.headGroup);

    const loader = new GLTFLoader();
    loader.load(
      'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r158/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb',
      (gltf) => this._buildFace(gltf),
      undefined,
      (err) => {
        console.error('Model load failed:', err);
        // Fallback: icosahedron
        this._buildFace(null);
      }
    );
  }

  _buildFace(gltf) {
    let geo;
    if (gltf) {
      geo = gltf.scene.children[0].geometry;
      geo.computeBoundingBox();
      const center = new THREE.Vector3();
      geo.boundingBox.getCenter(center);
      geo.translate(-center.x, -center.y, -center.z);
      const h = geo.boundingBox.max.y - geo.boundingBox.min.y;
      geo.scale(1.5 / h, 1.5 / h, 1.5 / h);
    } else {
      geo = new THREE.IcosahedronGeometry(0.8, 4);
    }

    // Face center (nose area) — fade is relative to this point
    const faceCenter = new THREE.Vector3(0, 0, 0.35);
    const fadeRadius = 0.55; // distance from center where face fully fades

    // ── Fade mask shader: face emerges from black ──
    const fadeVertex = `
      varying vec3 vPos;
      varying vec3 vNormal;
      varying vec3 vWorldNormal;
      varying vec3 vWorldPos;
      void main() {
        vPos = position;
        vNormal = normal;
        vWorldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
        vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    const fadeFrag = `
      uniform vec3 uColor;
      uniform vec3 uEmissive;
      uniform vec3 uFaceCenter;
      uniform float uFadeRadius;
      uniform vec3 uLightDir;
      varying vec3 vPos;
      varying vec3 vNormal;
      varying vec3 vWorldNormal;
      varying vec3 vWorldPos;
      void main() {
        // Distance fade from face center
        float d = distance(vPos, uFaceCenter);
        float fade = 1.0 - smoothstep(uFadeRadius * 0.5, uFadeRadius, d);
        if (fade < 0.01) discard;

        // Simple lighting
        float diff = max(dot(vWorldNormal, normalize(uLightDir)), 0.0);
        float ambient = 0.15;
        vec3 col = uColor * (ambient + diff * 0.85) + uEmissive;

        gl_FragColor = vec4(col, fade);
      }
    `;

    // ── 1. Solid face with fade ──
    this.faceUniforms = {
      uColor: { value: new THREE.Color(0x0e1e30) },
      uEmissive: { value: new THREE.Color(0x050a12) },
      uFaceCenter: { value: faceCenter },
      uFadeRadius: { value: fadeRadius },
      uLightDir: { value: new THREE.Vector3(1, 1.5, 3).normalize() },
    };
    this.faceMat = new THREE.ShaderMaterial({
      vertexShader: fadeVertex,
      fragmentShader: fadeFrag,
      uniforms: this.faceUniforms,
      transparent: true,
      side: THREE.FrontSide,
      flatShading: true,
    });
    // Force flat shading by computing flat normals
    const faceGeo = geo.toNonIndexed();
    faceGeo.computeVertexNormals();
    this.headGroup.add(new THREE.Mesh(faceGeo, this.faceMat));

    // ── 2. Glowing edges with distance fade ──
    const edgeFrag = `
      uniform vec3 uColor;
      uniform vec3 uFaceCenter;
      uniform float uFadeRadius;
      varying vec3 vPos;
      void main() {
        float d = distance(vPos, uFaceCenter);
        float fade = 1.0 - smoothstep(uFadeRadius * 0.5, uFadeRadius, d);
        if (fade < 0.01) discard;
        gl_FragColor = vec4(uColor, fade * 0.7);
      }
    `;
    const edgeVertex = `
      varying vec3 vPos;
      void main() {
        vPos = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    const edges = new THREE.EdgesGeometry(geo, 8);
    this.edgeUniforms = {
      uColor: { value: new THREE.Color(0x2288cc) },
      uFaceCenter: { value: faceCenter },
      uFadeRadius: { value: fadeRadius },
    };
    this.edgeMat = new THREE.ShaderMaterial({
      vertexShader: edgeVertex,
      fragmentShader: edgeFrag,
      uniforms: this.edgeUniforms,
      transparent: true,
    });
    this.headGroup.add(new THREE.LineSegments(edges, this.edgeMat));

    // ── 3. Vertex dots with fade ──
    const pos = geo.attributes.position;
    const seen = new Set();
    const dots = [];
    const dotFades = [];
    const usedVerts = new Set();
    if (geo.index) {
      for (let i = 0; i < geo.index.count; i++) usedVerts.add(geo.index.getX(i));
    } else {
      for (let i = 0; i < pos.count; i++) usedVerts.add(i);
    }
    for (const vi of usedVerts) {
      const x = pos.getX(vi), y = pos.getY(vi), z = pos.getZ(vi);
      const k = `${x.toFixed(3)},${y.toFixed(3)},${z.toFixed(3)}`;
      if (!seen.has(k)) {
        seen.add(k);
        const dist = Math.sqrt((x - faceCenter.x) ** 2 + (y - faceCenter.y) ** 2 + (z - faceCenter.z) ** 2);
        const f = 1.0 - Math.min(1, Math.max(0, (dist - fadeRadius * 0.5) / (fadeRadius * 0.5)));
        if (f > 0.02) {
          dots.push(x, y, z);
          dotFades.push(f);
        }
      }
    }
    const dotGeo = new THREE.BufferGeometry();
    dotGeo.setAttribute('position', new THREE.Float32BufferAttribute(dots, 3));
    this.dotMat = new THREE.PointsMaterial({
      color: 0x44aaee,
      size: 0.006,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true,
    });
    this.headGroup.add(new THREE.Points(dotGeo, this.dotMat));
  }

  _initPost() {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.35, 0.4, 0.85
    );
    this.composer.addPass(this.bloomPass);
  }

  setState(name) {
    if (STATES[name]) { this.state = name; this.target = STATES[name]; }
  }

  _lerp(a, b, t) { return a + (b - a) * t; }

  _animate() {
    const clock = new THREE.Clock();
    const _c = new THREE.Color();

    const tick = () => {
      requestAnimationFrame(tick);
      const el = clock.getElapsedTime();
      const t = 0.03;
      const tgt = this.target;

      // ── Materials ──
      if (this.faceUniforms) {
        _c.set(tgt.faceColor);
        this.faceUniforms.uColor.value.lerp(_c, t);
        _c.set(tgt.emissive);
        this.faceUniforms.uEmissive.value.lerp(_c, t);
      }
      if (this.edgeUniforms) {
        this.edgeUniforms.uColor.value.lerp(tgt.edgeColor, t);
      }
      if (this.dotMat) {
        this.dotMat.color.lerp(tgt.edgeColor, t);
        this.dotMat.opacity = this._lerp(this.dotMat.opacity, tgt.dotOpacity, t);
      }
      this.bloomPass.strength = this._lerp(this.bloomPass.strength, tgt.bloom, t);

      // ── Head: gentle movement ──
      this.headGroup.position.y = Math.sin(el * 0.3) * 0.01;
      this.headGroup.rotation.y = Math.sin(el * 0.15) * 0.08;
      this.headGroup.rotation.x = Math.sin(el * 0.12) * 0.025;
      this.headGroup.rotation.z = Math.sin(el * 0.09) * 0.01;

      // State behavior
      if (this.state === 'speaking') {
        this.headGroup.rotation.x += Math.sin(el * 3) * 0.012;
      } else if (this.state === 'thinking') {
        this.headGroup.rotation.y += Math.sin(el * 0.5) * 0.04;
      } else if (this.state === 'listening') {
        this.headGroup.rotation.x -= 0.015;
      }

      this.composer.render();
    };
    tick();
  }
}
