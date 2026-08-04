"""Three.js 3D bina görselleştirmesi (st.components.v1.html ile gömülür)."""

from __future__ import annotations

import json

from .config import BinaConfig

_TEMPLATE = r"""
<div id="wrap" style="width:100%;height:__H__px;background:#0d1117;border:1px solid #30363d;border-radius:10px;overflow:hidden;position:relative;">
<div id="hud" style="position:absolute;top:10px;left:12px;color:#e6edf3;font-family:sans-serif;font-size:13px;z-index:2;background:rgba(22,27,34,.75);padding:6px 10px;border-radius:6px;"></div>
<div id="alarm" style="display:none;position:absolute;top:10px;right:12px;color:#fff;font-family:sans-serif;font-weight:700;z-index:2;background:#da3633;padding:6px 12px;border-radius:6px;animation:blink 0.8s infinite alternate;">⚠ KESİNTİ</div>
<style>@keyframes blink{from{opacity:1}to{opacity:.35}}</style>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const CFG = __CFG__;
const wrap = document.getElementById('wrap');
const W = wrap.clientWidth, H = wrap.clientHeight;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W/H, 0.1, 400);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
wrap.appendChild(renderer.domElement);

// ── Gece/gündüz ──────────────────────────────────────────────
const hour = CFG.hour;
const dayFactor = Math.max(0, Math.sin((hour - 6) / 12 * Math.PI)); // 0 gece, 1 öğle
const skyNight = new THREE.Color(0x0a0e1a), skyDay = new THREE.Color(0x87b5d8);
scene.background = skyNight.clone().lerp(skyDay, dayFactor);
scene.fog = new THREE.Fog(scene.background, 60, 200);

const amb = new THREE.AmbientLight(0xffffff, 0.25 + 0.45 * dayFactor);
scene.add(amb);

// Güneş
const sunAngle = (hour - 6) / 12 * Math.PI; // 6→doğu, 18→batı
const sunR = 40;
const sun = new THREE.Mesh(new THREE.SphereGeometry(1.6, 16, 16),
  new THREE.MeshBasicMaterial({color: 0xffd75e}));
sun.position.set(Math.cos(sunAngle) * sunR, Math.sin(sunAngle) * sunR, -18);
sun.visible = dayFactor > 0.01;
scene.add(sun);
const sunLight = new THREE.DirectionalLight(0xfff2cc, 0.9 * dayFactor);
sunLight.position.copy(sun.position);
sunLight.castShadow = true;
scene.add(sunLight);
// Ay ışığı geceleri
if (dayFactor < 0.1) {
  const moon = new THREE.DirectionalLight(0x8899ff, 0.25);
  moon.position.set(-20, 30, 10); scene.add(moon);
}

// ── Zemin ────────────────────────────────────────────────────
const ground = new THREE.Mesh(new THREE.PlaneGeometry(300, 300),
  new THREE.MeshLambertMaterial({color: new THREE.Color(0x1e2a1e).lerp(new THREE.Color(0x3a5a3a), dayFactor)}));
ground.rotation.x = -Math.PI/2; ground.receiveShadow = true;
scene.add(ground);

// ── Bina ─────────────────────────────────────────────────────
const FLOOR_H = 1.5, DEPTH = 5.0;
const unitW = 2.2;
const bWidth = Math.max(CFG.units_per_floor * unitW + 0.8, 4);
const bHeight = CFG.floors * FLOOR_H;
const group = new THREE.Group();

// Yarı şeffaf gövde
const body = new THREE.Mesh(
  new THREE.BoxGeometry(bWidth, bHeight, DEPTH),
  new THREE.MeshPhysicalMaterial({color: 0x4a5568, transparent: true, opacity: 0.42, roughness: 0.4}));
body.position.y = bHeight/2; body.castShadow = true;
group.add(body);

// Kat çizgileri
for (let f = 1; f < CFG.floors; f++) {
  const line = new THREE.Mesh(new THREE.BoxGeometry(bWidth + 0.06, 0.06, DEPTH + 0.06),
    new THREE.MeshBasicMaterial({color: 0x30363d}));
  line.position.y = f * FLOOR_H;
  group.add(line);
}

// Pencereler + iç ışıklar
const lightsOn = (hour >= 17 || hour < 7);
let unitIdx = 0;
for (let f = 0; f < CFG.floors; f++) {
  for (let u = 0; u < CFG.units_per_floor; u++) {
    const active = unitIdx < CFG.active_units;
    const lit = active && lightsOn && !CFG.outage;
    const winMat = new THREE.MeshBasicMaterial({
      color: lit ? 0xffd75e : (active ? 0x2c3648 : 0x11151c)});
    for (const z of [DEPTH/2 + 0.02, -DEPTH/2 - 0.02]) {
      const win = new THREE.Mesh(new THREE.PlaneGeometry(unitW * 0.62, FLOOR_H * 0.55), winMat);
      win.position.set(-bWidth/2 + (u + 0.5) * (bWidth / CFG.units_per_floor),
                       f * FLOOR_H + FLOOR_H * 0.52, z);
      if (z < 0) win.rotation.y = Math.PI;
      group.add(win);
      // İç ışık noktası (yarı şeffaf duvardan görünür)
      if (lit && z > 0) {
        const glow = new THREE.PointLight(0xffc94d, 0.25, 4);
        glow.position.set(win.position.x, win.position.y, 0);
        group.add(glow);
      }
    }
    unitIdx++;
  }
}

// ── Çatı panelleri ───────────────────────────────────────────
const nP = Math.min(CFG.panels, 40);
const cols = Math.ceil(Math.sqrt(nP * bWidth / DEPTH));
const rows = Math.ceil(nP / cols);
const pw = bWidth * 0.85 / cols, pd = DEPTH * 0.8 / rows;
let placed = 0;
for (let r = 0; r < rows && placed < nP; r++) {
  for (let c = 0; c < cols && placed < nP; c++, placed++) {
    const glow = CFG.solar_norm;
    const mat = new THREE.MeshPhongMaterial({
      color: 0x11294d,
      emissive: new THREE.Color(0xff8c00),
      emissiveIntensity: glow * 0.9,
      shininess: 90});
    const p = new THREE.Mesh(new THREE.BoxGeometry(pw * 0.9, 0.06, pd * 0.85), mat);
    p.position.set(-bWidth * 0.425 + (c + 0.5) * pw, bHeight + 0.18, -DEPTH * 0.4 + (r + 0.5) * pd);
    p.rotation.x = -0.28;
    group.add(p);
  }
}

// ── Batarya ünitesi ──────────────────────────────────────────
const battH = 2.2, battX = bWidth/2 + 2.2;
const shell = new THREE.Mesh(new THREE.BoxGeometry(1.3, battH, 0.9),
  new THREE.MeshLambertMaterial({color: 0x21262d}));
shell.position.set(battX, battH/2, 1.2);
group.add(shell);
const soc = CFG.soc; // 0..1
const fillCol = new THREE.Color(0xd73a49).lerp(new THREE.Color(0x2ea043), soc);
const fill = new THREE.Mesh(new THREE.BoxGeometry(1.1, Math.max(battH * soc - 0.1, 0.05), 0.72),
  new THREE.MeshBasicMaterial({color: fillCol}));
fill.position.set(battX, Math.max(battH * soc - 0.1, 0.05)/2 + 0.06, 1.2);
group.add(fill);

// ── Asansör ──────────────────────────────────────────────────
let cab = null;
if (CFG.elevator) {
  const shaft = new THREE.Mesh(new THREE.BoxGeometry(1.0, bHeight, 1.0),
    new THREE.MeshPhysicalMaterial({color: 0x58a6ff, transparent: true, opacity: 0.22}));
  shaft.position.set(-bWidth/2 - 0.75, bHeight/2, 0);
  group.add(shaft);
  cab = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.0, 0.8),
    new THREE.MeshLambertMaterial({color: 0xc9d1d9}));
  cab.position.set(-bWidth/2 - 0.75, 0.55, 0);
  group.add(cab);
}

// ── EV şarj ──────────────────────────────────────────────────
if (CFG.ev) {
  const car = new THREE.Group();
  const govde = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.55, 1.1),
    new THREE.MeshPhongMaterial({color: 0x1f6feb, shininess: 80}));
  govde.position.y = 0.45; car.add(govde);
  const kabin = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.42, 1.0),
    new THREE.MeshPhongMaterial({color: 0x0d419d}));
  kabin.position.set(-0.1, 0.9, 0); car.add(kabin);
  for (const dx of [-0.75, 0.75]) for (const dz of [-0.55, 0.55]) {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.18, 16),
      new THREE.MeshLambertMaterial({color: 0x161b22}));
    t.rotation.x = Math.PI/2; t.position.set(dx, 0.22, dz); car.add(t);
  }
  car.position.set(battX + 0.4, 0, 4.6);
  group.add(car);
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.22, 1.1, 0.22),
    new THREE.MeshLambertMaterial({color: 0x2ea043}));
  post.position.set(battX - 1.1, 0.55, 4.6); group.add(post);
  const evCharging = (hour >= 22 || hour < 6) && !CFG.outage;
  if (evCharging) {
    const lamp = new THREE.PointLight(0x3fb950, 0.9, 6);
    lamp.position.set(battX - 1.1, 1.4, 4.6); group.add(lamp);
  }
}

// ── Kesinti uyarısı ──────────────────────────────────────────
let alarmLight = null;
if (CFG.outage) {
  document.getElementById('alarm').style.display = 'block';
  alarmLight = new THREE.PointLight(0xff2d20, 1.6, 30);
  alarmLight.position.set(0, bHeight + 2.5, 0);
  scene.add(alarmLight);
}

scene.add(group);

// ── Kamera + kontrol ─────────────────────────────────────────
const R0 = Math.max(bHeight * 1.9, bWidth * 2.2, 14);
let theta = 0.7, phi = 0.42, radius = R0, auto = true;
function updateCam(){
  camera.position.set(radius * Math.cos(phi) * Math.sin(theta),
                      Math.max(radius * Math.sin(phi), 1.5),
                      radius * Math.cos(phi) * Math.cos(theta));
  camera.lookAt(0, bHeight/2, 0);
}
let drag = false, px = 0, py = 0;
renderer.domElement.addEventListener('mousedown', e => {drag = true; auto = false; px = e.clientX; py = e.clientY;});
window.addEventListener('mouseup', () => drag = false);
window.addEventListener('mousemove', e => {
  if (!drag) return;
  theta -= (e.clientX - px) * 0.008; phi = Math.min(1.35, Math.max(0.08, phi + (e.clientY - py) * 0.006));
  px = e.clientX; py = e.clientY;
});
renderer.domElement.addEventListener('wheel', e => {
  e.preventDefault(); radius = Math.min(R0 * 2.5, Math.max(6, radius + e.deltaY * 0.03));
}, {passive: false});

document.getElementById('hud').innerHTML =
  `🕐 ${String(hour).padStart(2,'0')}:00 &nbsp; 🔋 %${Math.round(soc*100)} &nbsp; ☀️ ${CFG.solar_kw.toFixed(1)} kW &nbsp; 🏠 ${CFG.active_units}/${CFG.total_units} daire`;

let t0 = 0;
function animate(ts){
  requestAnimationFrame(animate);
  const dt = (ts - t0) / 1000; t0 = ts;
  if (auto) theta += 0.15 * dt;
  if (cab) cab.position.y = 0.55 + (bHeight - 1.2) * (0.5 + 0.5 * Math.sin(ts / 2600));
  if (alarmLight) alarmLight.intensity = 1.0 + Math.sin(ts / 130) * 0.9;
  updateCam();
  renderer.render(scene, camera);
}
updateCam();
requestAnimationFrame(animate);
</script>
"""


def building_html(cfg: BinaConfig, hour: int, soc: float,
                  solar_kw: float, outage: bool = False, height: int = 520) -> str:
    solar_max = max(cfg.panel_kw * 0.80, 0.1)
    params = dict(
        floors=int(cfg.kat),
        units_per_floor=int(cfg.daire_per_kat),
        active_units=int(min(cfg.aktif_daire, cfg.toplam_daire)),
        total_units=int(cfg.toplam_daire),
        panels=int(cfg.panel_sayisi),
        hour=int(hour),
        soc=float(round(soc, 3)),
        solar_kw=float(round(solar_kw, 2)),
        solar_norm=float(round(min(solar_kw / solar_max, 1.0), 3)),
        elevator=bool(cfg.asansor),
        ev=bool(cfg.ev_sarj),
        outage=bool(outage),
    )
    return _TEMPLATE.replace("__CFG__", json.dumps(params)).replace("__H__", str(height))
