"use strict";
/*
 * AanyaAvatar — a stylised 3D AI companion (Three.js), voice-reactive.
 * Exposes window.AanyaAvatar.setState('idle'|'listening'|'thinking'|'speaking').
 * Degrades to a CSS orb if WebGL/Three.js is unavailable.
 */
(function () {
  const canvas = document.getElementById("avatarCanvas");
  const fallback = document.getElementById("avatarFallback");

  function useFallback() {
    if (canvas) canvas.hidden = true;
    if (fallback) fallback.hidden = false;
    window.AanyaAvatar = { ready: false, setState() {} };
  }

  if (!window.THREE || !canvas) return useFallback();

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  } catch (e) {
    return useFallback();
  }

  const state = { name: "idle", pointer: { x: 0, y: 0 }, blinkAt: 0, blink: 0 };
  const TEAL = 0x22e3c8;
  const MAGENTA = 0xff5cc8;
  const VIOLET = 0xa472ff;

  const size = () => Math.min(canvas.clientWidth || 440, canvas.clientHeight || 440) || 440;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(canvas.clientWidth || 440, canvas.clientHeight || 440, false);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0, 6);

  // Lighting — futuristic rim light.
  scene.add(new THREE.AmbientLight(0x4a5a80, 0.9));
  const key = new THREE.PointLight(TEAL, 2.2, 50);
  key.position.set(3, 2.5, 4);
  scene.add(key);
  const fill = new THREE.PointLight(VIOLET, 1.8, 50);
  fill.position.set(-3.5, -1.5, 3);
  scene.add(fill);
  const top = new THREE.DirectionalLight(0xffffff, 0.5);
  top.position.set(0, 4, 2);
  scene.add(top);

  const bot = new THREE.Group();
  scene.add(bot);

  // Head
  const headMat = new THREE.MeshStandardMaterial({
    color: 0x0e1730,
    metalness: 0.7,
    roughness: 0.32,
    emissive: 0x0a1a30,
    emissiveIntensity: 0.35,
  });
  const head = new THREE.Mesh(new THREE.SphereGeometry(1.15, 64, 64), headMat);
  head.scale.set(1, 1.02, 0.96);
  bot.add(head);

  // Faceplate (darker, glossy)
  const plate = new THREE.Mesh(
    new THREE.SphereGeometry(1.02, 48, 48),
    new THREE.MeshStandardMaterial({ color: 0x05080f, metalness: 0.95, roughness: 0.12 })
  );
  plate.position.z = 0.34;
  plate.scale.set(0.92, 0.8, 0.6);
  bot.add(plate);

  // Eyes
  const eyeMat = new THREE.MeshStandardMaterial({
    color: 0x041014,
    emissive: TEAL,
    emissiveIntensity: 1.8,
  });
  function makeEye(x) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.17, 32, 32), eyeMat);
    eye.position.set(x, 0.16, 0.95);
    eye.scale.set(1.5, 1, 0.6);
    bot.add(eye);
    return eye;
  }
  const eyes = [makeEye(-0.38), makeEye(0.38)];

  // Mouth equaliser bars
  const mouthMat = new THREE.MeshStandardMaterial({
    color: 0x04141a,
    emissive: TEAL,
    emissiveIntensity: 1.4,
  });
  const mouth = [];
  for (let i = 0; i < 5; i++) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.22, 0.06), mouthMat);
    bar.position.set(-0.28 + i * 0.14, -0.42, 1.0);
    bot.add(bar);
    mouth.push(bar);
  }

  // Antenna
  const antenna = new THREE.Mesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.5, 12),
    new THREE.MeshStandardMaterial({ color: 0x1a2540, metalness: 0.8, roughness: 0.3 })
  );
  antenna.position.set(0, 1.4, 0);
  bot.add(antenna);
  const tip = new THREE.Mesh(
    new THREE.SphereGeometry(0.1, 20, 20),
    new THREE.MeshStandardMaterial({ color: 0x100018, emissive: MAGENTA, emissiveIntensity: 2 })
  );
  tip.position.set(0, 1.68, 0);
  bot.add(tip);

  // Side pods (ears)
  function makePod(x) {
    const pod = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.16, 24),
      new THREE.MeshStandardMaterial({ color: 0x0c1426, metalness: 0.8, roughness: 0.3, emissive: 0x0a2030, emissiveIntensity: 0.6 })
    );
    pod.rotation.z = Math.PI / 2;
    pod.position.set(x, 0, 0);
    bot.add(pod);
  }
  makePod(-1.12);
  makePod(1.12);

  // Halo rings
  const haloMat = new THREE.MeshStandardMaterial({ color: 0x06201e, emissive: TEAL, emissiveIntensity: 1.3 });
  const halo = new THREE.Mesh(new THREE.TorusGeometry(1.75, 0.022, 16, 120), haloMat);
  halo.rotation.x = 1.25;
  bot.add(halo);
  const halo2 = new THREE.Mesh(
    new THREE.TorusGeometry(2.05, 0.012, 16, 120),
    new THREE.MeshStandardMaterial({ color: 0x140a26, emissive: VIOLET, emissiveIntensity: 1 })
  );
  halo2.rotation.x = -1.0;
  halo2.rotation.y = 0.5;
  bot.add(halo2);

  // Particle field
  const pCount = 260;
  const pPos = new Float32Array(pCount * 3);
  for (let i = 0; i < pCount; i++) {
    const r = 2.3 + Math.random() * 1.6;
    const t = Math.random() * Math.PI * 2;
    const p = Math.acos(2 * Math.random() - 1);
    pPos[i * 3] = r * Math.sin(p) * Math.cos(t);
    pPos[i * 3 + 1] = r * Math.sin(p) * Math.sin(t);
    pPos[i * 3 + 2] = r * Math.cos(p);
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
  const particles = new THREE.Points(
    pGeo,
    new THREE.PointsMaterial({ color: TEAL, size: 0.03, transparent: true, opacity: 0.6 })
  );
  scene.add(particles);

  // Pointer parallax
  window.addEventListener("pointermove", (e) => {
    state.pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    state.pointer.y = (e.clientY / window.innerHeight) * 2 - 1;
  });

  function onResize() {
    const w = canvas.clientWidth || 440;
    const h = canvas.clientHeight || 440;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", onResize);
  onResize();

  const clock = new THREE.Clock();
  let lerp = (a, b, t) => a + (b - a) * t;

  function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    const speaking = state.name === "speaking";
    const listening = state.name === "listening";
    const thinking = state.name === "thinking";

    // Idle bob + pointer-follow.
    bot.position.y = Math.sin(t * 1.4) * 0.05;
    const targetY = state.pointer.x * 0.5 + Math.sin(t * 0.5) * 0.12;
    const targetX = state.pointer.y * 0.3;
    bot.rotation.y = lerp(bot.rotation.y, targetY, 0.05);
    bot.rotation.x = lerp(bot.rotation.x, targetX, 0.05);

    // Halo motion.
    const haloSpeed = listening ? 2.4 : speaking ? 1.4 : 0.6;
    halo.rotation.z += 0.01 * haloSpeed;
    halo2.rotation.z -= 0.008 * haloSpeed;
    haloMat.emissive.setHex(listening ? MAGENTA : TEAL);
    haloMat.emissiveIntensity = lerp(haloMat.emissiveIntensity, listening || speaking ? 1.8 : 1.1, 0.1);

    // Particles drift.
    particles.rotation.y += 0.0009;
    particles.rotation.x += 0.0004;

    // Blink.
    if (t > state.blinkAt) {
      state.blink = 1;
      state.blinkAt = t + 2 + Math.random() * 3;
    }
    state.blink = Math.max(0, state.blink - 0.12);
    const blinkScale = 1 - state.blink * 0.92;

    // Eyes.
    const eyeBright = thinking ? 0.8 + Math.abs(Math.sin(t * 4)) * 0.8 : speaking || listening ? 2.4 : 1.7;
    eyes.forEach((eye, i) => {
      eye.scale.y = lerp(eye.scale.y, blinkScale * (listening ? 1.15 : 1), 0.4);
      eye.material.emissiveIntensity = eyeBright;
      eye.material.emissive.setHex(listening ? MAGENTA : TEAL);
      eye.position.x = (i === 0 ? -0.38 : 0.38) + state.pointer.x * 0.03;
    });

    // Mouth equaliser.
    mouth.forEach((bar, i) => {
      let target = 0.18;
      if (speaking) {
        const amp = Math.abs(Math.sin(t * 8 + i)) * Math.abs(Math.sin(t * 5.3 + i * 1.7));
        target = 0.25 + amp * 1.25;
      } else if (thinking) {
        target = 0.14 + Math.abs(Math.sin(t * 3 + i)) * 0.1;
      }
      bar.scale.y = lerp(bar.scale.y, target, 0.35);
      bar.material.emissiveIntensity = speaking ? 2.0 : 1.3;
    });

    // Antenna tip pulse.
    tip.material.emissiveIntensity = 1.5 + Math.abs(Math.sin(t * 3)) * (listening ? 1.5 : 0.6);

    renderer.render(scene, camera);
  }
  animate();

  window.AanyaAvatar = {
    ready: true,
    setState(name) {
      state.name = name || "idle";
    },
  };
})();
