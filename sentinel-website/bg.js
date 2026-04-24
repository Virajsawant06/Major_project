const W = () => window.innerWidth;
const canvas = document.getElementById('hero-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(W(), window.innerHeight);
renderer.setClearColor(0x080B10, 1);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x080B10, 0.035);

const camera = new THREE.PerspectiveCamera(60, W() / window.innerHeight, 0.1, 200);
camera.position.set(0, 6, 18);
camera.lookAt(0, 0, 0);

// --- HEX GRID FLOOR ---
const hexGeo = new THREE.CylinderGeometry(0.96, 0.96, 0.12, 6, 1);
const hexMat = new THREE.MeshStandardMaterial({
  color: 0x0a101a,
  emissive: 0x001a33,
  emissiveIntensity: 0.3,
  metalness: 0.7,
  roughness: 0.4,
});
// Changed to Electric Blue #00A8FF
const edgeMat = new THREE.LineBasicMaterial({ color: 0x00D1FF, transparent: true, opacity: 0.25 });

const COLS = 30, ROWS = 25; // slightly larger grid to cover the full width
const hexGroup = new THREE.Group();

function hexPos(col, row) {
  const x = col * 1.73 + ((row % 2) * 0.865) - COLS * 0.865;
  const z = row * 1.5 - ROWS * 0.75;
  return [x, z];
}

const hexMeshes = [];
for (let r = 0; r < ROWS; r++) {
  for (let c = 0; c < COLS; c++) {
    const [x, z] = hexPos(c, r);
    const mesh = new THREE.Mesh(hexGeo, hexMat.clone());
    mesh.position.set(x, -0.5, z);
    mesh.userData = { baseY: -0.5, phase: Math.random() * Math.PI * 2, speed: 0.3 + Math.random() * 0.5, amp: 0.08 + Math.random() * 0.18 };
    hexMeshes.push(mesh);
    hexGroup.add(mesh);

    // Edge outline
    const edges = new THREE.EdgesGeometry(hexGeo);
    const line = new THREE.LineSegments(edges, edgeMat.clone());
    line.position.copy(mesh.position);
    hexGroup.add(line);
  }
}
scene.add(hexGroup);

// --- FLOATING HEX PARTICLES ---
const particleGroup = new THREE.Group();
const smallHex = new THREE.CylinderGeometry(0.25, 0.25, 0.06, 6, 1);
const pMat = new THREE.MeshStandardMaterial({ color: 0x00D1FF, emissive: 0x00D1FF, emissiveIntensity: 0.8, metalness: 0.5, roughness: 0.3, transparent: true, opacity: 0.7 });

const particles = [];
for (let i = 0; i < 35; i++) {
  const m = new THREE.Mesh(smallHex, pMat.clone());
  const angle = Math.random() * Math.PI * 2;
  const rad = 3 + Math.random() * 15;
  m.position.set(Math.cos(angle) * rad, 1.5 + Math.random() * 5, Math.sin(angle) * rad - 2);
  m.rotation.y = Math.random() * Math.PI;
  m.userData = { floatPhase: Math.random() * Math.PI * 2, floatSpeed: 0.4 + Math.random() * 0.6, rotSpeed: (Math.random() - 0.5) * 0.02 };
  particles.push(m);
  particleGroup.add(m);
}
scene.add(particleGroup);

// --- SCAN BEAM ---
const beamGeo = new THREE.PlaneGeometry(80, 0.06);
const beamMat = new THREE.MeshBasicMaterial({ color: 0x00D1FF, transparent: true, opacity: 0.18, side: THREE.DoubleSide });
const beam = new THREE.Mesh(beamGeo, beamMat);
beam.rotation.x = -Math.PI / 2;
beam.position.y = 0.1;
scene.add(beam);

// --- VERTICAL SCAN LINE ---
const vBeamGeo = new THREE.PlaneGeometry(0.05, 80);
const vBeamMat = new THREE.MeshBasicMaterial({ color: 0x0085FF, transparent: true, opacity: 0.12, side: THREE.DoubleSide });
const vBeam = new THREE.Mesh(vBeamGeo, vBeamMat);
vBeam.rotation.y = Math.PI / 2;
vBeam.position.y = 0.1;
scene.add(vBeam);

// --- WIREFRAME SPHERE ---
const sphereGeo = new THREE.IcosahedronGeometry(2.8, 2);
const sphereEdges = new THREE.EdgesGeometry(sphereGeo);
const sphereMat = new THREE.LineBasicMaterial({ color: 0x00D1FF, transparent: true, opacity: 0.15 });
const sphere = new THREE.LineSegments(sphereEdges, sphereMat);
sphere.position.set(0, 2, -2);
scene.add(sphere);

// --- LIGHTING ---
const ambient = new THREE.AmbientLight(0x0a101a, 2);
scene.add(ambient);

const mainLight = new THREE.PointLight(0x00D1FF, 3, 25);
mainLight.position.set(0, 8, 0);
scene.add(mainLight);

const secondaryLight = new THREE.PointLight(0x0085FF, 2, 20);
secondaryLight.position.set(-8, 4, -5);
scene.add(secondaryLight);

const rimLight = new THREE.PointLight(0x00D1FF, 1.5, 15);
rimLight.position.set(8, 2, 5);
scene.add(rimLight);

// --- MOUSE PARALLAX ---
let mouseX = 0, mouseY = 0;
document.addEventListener('mousemove', e => {
  mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
  mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
});

// --- ANIMATE ---
let t = 0;
function animate() {
  requestAnimationFrame(animate);
  t += 0.012;

  // Camera parallax
  camera.position.x += (mouseX * 2 - camera.position.x) * 0.04;
  camera.position.y += (6 - mouseY * 1.5 - camera.position.y) * 0.04;
  camera.lookAt(0, 0, 0);

  // Hex tile pulse
  hexMeshes.forEach(h => {
    const { baseY, phase, speed, amp } = h.userData;
    h.position.y = baseY + Math.sin(t * speed + phase) * amp;
    const d = Math.sqrt(h.position.x ** 2 + h.position.z ** 2);
    const wave = Math.max(0, 0.5 - d * 0.04) * Math.sin(t * 2 - d * 0.5 + phase);
    h.material.emissiveIntensity = 0.15 + wave * 0.6;
    h.material.emissive.setHex(wave > 0.1 ? 0x00D1FF : 0x001a33);
  });

  // Scan beam sweep
  beam.position.z = Math.sin(t * 0.4) * 12;
  vBeam.position.x = Math.sin(t * 0.3 + 1) * 10;

  // Floating particles
  particles.forEach(p => {
    const { floatPhase, floatSpeed, rotSpeed } = p.userData;
    p.position.y += Math.sin(t * floatSpeed + floatPhase) * 0.005;
    p.rotation.y += rotSpeed;
    p.material.opacity = 0.4 + 0.3 * Math.sin(t + floatPhase);
  });

  // Sphere rotate
  sphere.rotation.y = t * 0.15;
  sphere.rotation.x = t * 0.08;

  // Pulsing lights
  mainLight.intensity = 2.5 + Math.sin(t * 1.2) * 0.8;
  secondaryLight.position.x = -8 + Math.sin(t * 0.5) * 4;

  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  renderer.setSize(W(), window.innerHeight);
  camera.aspect = W() / window.innerHeight;
  camera.updateProjectionMatrix();
});
