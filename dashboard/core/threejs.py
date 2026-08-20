"""Three.js 3D bina görselleştirmesi — gerçekçi, profesyonel, döndür/zoom."""

from __future__ import annotations
import json
from .config import BinaConfig

_TEMPLATE = r"""
<style>html,body{margin:0;padding:0;height:100%;width:100%;overflow:hidden;background:#08101e}</style>
<div id="wrap" style="width:100%;height:100%;min-height:__H__px;position:relative;overflow:hidden;background:#08101e;">
<div id="alarm" style="display:none;position:absolute;top:14px;right:14px;z-index:9;
  background:linear-gradient(135deg,#7f1d1d,#dc2626);color:#fff;font-weight:700;font-size:12px;
  padding:6px 16px;border-radius:6px;font-family:'Inter',system-ui;letter-spacing:.06em;
  border:1px solid rgba(239,68,68,.4);box-shadow:0 0 18px rgba(239,68,68,.5);
  display:flex;align-items:center;gap:7px;">
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
  <span id="alarm-text">GRID OUTAGE</span></div>
<div id="dt-hud" style="
  position:absolute;bottom:0;left:0;right:0;z-index:9;
  background:linear-gradient(to top,rgba(4,8,20,0.92) 0%,rgba(4,8,20,0.55) 70%,transparent 100%);
  padding:14px 20px 14px;
  display:flex;gap:0;align-items:flex-end;
  font-family:'Inter','SF Pro Display',system-ui,sans-serif;">
</div>
<style>
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.15}}
  @keyframes flowPulse{0%,100%{opacity:.7}50%{opacity:1}}
  .dt-metric{
    flex:1;min-width:80px;padding:0 14px;
    border-right:1px solid rgba(255,255,255,.07);
  }
  .dt-metric:last-child{border-right:none}
  .dt-label{
    font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:rgba(148,163,184,.65);margin-bottom:4px;
  }
  .dt-value{
    font-size:18px;font-weight:700;color:#f1f5f9;line-height:1;letter-spacing:-.01em;
  }
  .dt-sub{
    font-size:10px;color:rgba(148,163,184,.5);margin-top:3px;letter-spacing:.04em;
  }
  .dt-bar-wrap{
    height:3px;background:rgba(255,255,255,.08);border-radius:2px;margin-top:6px;overflow:hidden;
  }
  .dt-bar{height:3px;border-radius:2px;transition:width .6s ease;}
  .dt-status-dot{
    display:inline-block;width:6px;height:6px;border-radius:50%;
    margin-right:5px;vertical-align:middle;
  }
  .dt-logo{
    font-size:10px;font-weight:700;letter-spacing:.14em;color:rgba(96,165,250,.7);
    text-transform:uppercase;margin-bottom:6px;
  }
</style>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<!-- Eklentiler (r128 examples/js — hepsi global THREE.* olarak eklenir).
     Sıra önemli: shader'lar → composer → passes. -->
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/RGBELoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/CopyShader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/GammaCorrectionShader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/EffectComposer.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/RenderPass.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/ShaderPass.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
<script>
(function(){
const CFG = __CFG__;
const wrap = document.getElementById('wrap');
// Fallback dimensions — iframe may not have laid out yet on first render
const W = Math.max(wrap.clientWidth  || 0, 320) || 640;
const H = Math.max(wrap.clientHeight || 0, 200) || __H__;

/* ── Renderer ─────────────────────────────────────────────── */
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:false});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
// Absolute-position canvas so it fills the wrap div at all times
renderer.domElement.style.cssText = 'position:absolute;inset:0;width:100%!important;height:100%!important;';
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
// Kontrollü exposure — 1.25 gündüz highlight'ları patlatıp sahneyi "yıkanmış"
// gösteriyordu; 1.02 cephe/panel/gölgeleri net tutar.
renderer.toneMappingExposure = 1.02;
wrap.appendChild(renderer.domElement);

/* ── Gerçekçilik eklentileri: model / HDRI / efekt ayarları ─ */
// Harici .glb model + .hdr HDRI adresleri (Python'dan CFG.assets ile gelir).
// Boş bırakılırsa mevcut ilkel geometri (fallback) kullanılır — hiçbir şey bozulmaz.
const ASSETS = CFG.assets || {};
// Sinematik bloom açık/kapalı — renkler soluk/aşırı parlak görünürse Python'dan bloom=False verin.
const USE_BLOOM = (CFG.bloom !== false);
// Nabız/akış animasyonu için toplanan emissive materyaller (animate döngüsünde sürülür).
const energyFX = [];

// GLTF yükleyici (Draco'suz .glb önerilir → ek decoder gerekmez).
const gltfLoader = THREE.GLTFLoader ? new THREE.GLTFLoader() : null;

/* Bir ilkel-geometri grubunu yüklenen GLB modeliyle değiştirir.
   • URL yoksa / yükleyici yoksa       → hiçbir şey yapmaz, ilkel kalır.
   • Model yüklenince                  → ilkel çocuklar silinir, model konur.
   • Yükleme hata verirse              → ilkel korunur (güvenli fallback).
   opts: { targetHeight, scale, scaleMul, rotY } */
function swapWithModel(placeholder, url, opts) {
  opts = opts || {};
  if (!url || !gltfLoader) return;
  gltfLoader.load(url, (gltf) => {
    const model = gltf.scene;
    model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    // Hedef yüksekliğe otomatik ölçekle
    const size = new THREE.Vector3();
    new THREE.Box3().setFromObject(model).getSize(size);
    if (opts.targetHeight && size.y > 0) model.scale.setScalar((opts.targetHeight / size.y) * (opts.scaleMul || 1));
    else if (opts.scale) model.scale.setScalar(opts.scale);
    // Zemine otur (alt yüzey y=0)
    model.position.y -= new THREE.Box3().setFromObject(model).min.y;
    if (opts.rotY) model.rotation.y = opts.rotY;
    while (placeholder.children.length) placeholder.remove(placeholder.children[0]);
    placeholder.add(model);
  }, undefined, (err) => console.warn('Model yüklenemedi, ilkel geometri korunuyor:', url, err));
}

/* ── Scene ────────────────────────────────────────────────── */
const scene = new THREE.Scene();

/* ── Zaman & Mevsim — Gaziantep 37.06°N, 37.38°E, UTC+3 ──── */
const hour  = CFG.hour;
const month = CFG.month || 7;   // 1=Ocak … 12=Aralık

// Solar declination (Spencer formula)
(function computeSun(){
  const dayOfYear = Math.round((month - 1) * 30.44 + 15);
  const B = (2 * Math.PI * (dayOfYear - 1)) / 365;
  window._decl = (180 / Math.PI) * (
    0.006918 - 0.399912*Math.cos(B) + 0.070257*Math.sin(B)
    - 0.006758*Math.cos(2*B) + 0.000907*Math.sin(2*B)
    - 0.002697*Math.cos(3*B) + 0.00148 *Math.sin(3*B)
  );
  const declRad = window._decl * Math.PI / 180;
  const latRad  = 37.06 * Math.PI / 180;
  const cosH0   = -Math.tan(latRad) * Math.tan(declRad);
  const H0deg   = Math.acos(Math.max(-1, Math.min(1, cosH0))) * 180 / Math.PI;
  // Solar noon in local clock (UTC+3, lon=37.38°)
  const solarNoon = 12 + (3 - 37.38 / 15);  // ≈ 12.51h
  window._sunriseH = solarNoon - H0deg / 15;
  window._sunsetH  = solarNoon + H0deg / 15;
  // Max elevation at solar noon
  window._maxElev  = 90 - 37.06 + window._decl;  // degrees
})();
const sunriseH = window._sunriseH;  // e.g. 7.1 in Jan, 5.3 in Jun
const sunsetH  = window._sunsetH;   // e.g. 17.9 in Jan, 19.7 in Jun
const maxElev  = window._maxElev;   // e.g. 29° in Jan, 76° in Jun

// Normalised day progress (0 at sunrise, 0.5 at noon, 1 at sunset)
const isDaytime = hour >= sunriseH && hour <= sunsetH;
const dayProgress = isDaytime ? (hour - sunriseH) / (sunsetH - sunriseH) : 0;
// Day factor: 0=night, 1=solar noon  (sine curve over daylight period)
const dayF = isDaytime ? Math.sin(dayProgress * Math.PI) : 0;

// Golden hour: ±1h around sunrise/sunset
const isSunrise = Math.abs(hour - sunriseH) < 1.0;
const isSunset  = Math.abs(hour - sunsetH)  < 1.0;
const isGolden  = isSunrise || isSunset;

// Gökyüzü paleti — gerçek sunrise/sunset saatine göre
// dayF ve hour kullanılarak hesaplanır; mevsim farkı sunriseH/sunsetH üzerinden gelir
function skyPair() {
  // Gecenin tam ortası
  if (!isDaytime && hour > sunsetH + 1.5) return [0x01040c, 0x0a1226];
  if (!isDaytime && hour < sunriseH - 1.5) return [0x01040c, 0x0a1226];
  // Gece sabaha yakın
  if (!isDaytime && hour < sunriseH) return [0x03081a, 0x142344];
  // Şafak (sunrise ± 1h)
  if (isSunrise && dayF < 0.25) return [0x241d4a, 0xc45c1e];
  // Sabah altını (sunrise + 1-2h)
  if (isSunrise) return [0x39568a, 0xe8955a];
  // Gündüz yaz: daha canlı mavi; kış: daha soluk
  if (dayF > 0.6) {
    const summerBlue = month >= 5 && month <= 9;
    return summerBlue ? [0x1a6db8, 0x87ceeb] : [0x2170bf, 0x9fcdec];
  }
  // Öğleden sonra
  if (dayProgress > 0.5 && dayF > 0.3) return [0x2f7bbc, 0xb2d6ea];
  // Gün batımı (sunset ± 1h)
  if (isSunset && dayF > 0.08) return [0x281a4d, 0xff7a2e];
  if (isSunset) return [0x180f34, 0x8a2a10];
  // Akşam karanlığı
  if (!isDaytime) return [0x0c0722, 0x2a1330];
  return [0x2170bf, 0x9fcdec]; // gündüz fallback
}
const _sp = skyPair();
const skyTop = new THREE.Color(_sp[0]);
const sky    = new THREE.Color(_sp[1]);   // ufuk rengi → fog + hemisphere
scene.background = sky;                     // kubbe altında yedek
// Fog: parlak gökyüzü rengini doğrudan kullanınca uzak zemin sütlü/yıkanmış
// bir pusa dönüşüyordu. Rengi ufka + koyu tabana doğru çek, yoğunluğu düşür.
const fogCol = sky.clone().lerp(skyTop, 0.5).lerp(new THREE.Color(0x0b1524), 0.24);
scene.fog = new THREE.FogExp2(fogCol, 0.0058);  // ufku yumuşatır, sahneyi yıkamaz

// Degrade gökyüzü kubbesi — vertex renkli (shader gerektirmez, r128 uyumlu)
{
  const R = 300;
  const domeGeo = new THREE.SphereGeometry(R, 32, 20);
  const dp = domeGeo.attributes.position;
  const cols = [];
  for (let i = 0; i < dp.count; i++) {
    let t = (dp.getY(i) / R + 0.04) / 0.52;   // ufuk ≈ 0, zirve ≈ 1
    t = Math.max(0, Math.min(1, t));
    t = t * t * (3 - 2 * t);                    // smoothstep — yumuşak geçiş
    const c = sky.clone().lerp(skyTop, t);
    cols.push(c.r, c.g, c.b);
  }
  domeGeo.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  const domeMat = new THREE.MeshBasicMaterial({
    vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false
  });
  const skyDome = new THREE.Mesh(domeGeo, domeMat);
  skyDome.renderOrder = -1;
  scene.add(skyDome);
}

/* ── Işıklandırma ────────────────────────────────────────── */
// Hemisphere: gökyüzü rengi yukarıdan, toprak yeşili aşağıdan
const hemi = new THREE.HemisphereLight(
  sky, new THREE.Color(0x2d4a1e), 0.35 + 0.35 * dayF
);
scene.add(hemi);

// Güneş pozisyonu — gerçek sunriseH/sunsetH ve maxElev kullanılıyor
// dayProgress: 0=doğuş, 0.5=öğlen, 1=batış → yay boyunca E→W
const sunArc   = isDaytime ? dayProgress * Math.PI : Math.PI * 0.5; // varsayılan: öğlen pozisyonunda gizli
const sunDist  = 85;
// Azimuth: doğudan batıya yay (cos: doğu=+, batı=-)
const sunX = -Math.cos(sunArc - Math.PI * 0.5) * sunDist;   // doğu=+60, batı=-60
// Elevation: mevsime göre max yükseklik (kış ~30°, yaz ~76°)
const elevFactor = Math.max(0.15, Math.min(maxElev / 90, 0.85));  // 0-1 arası
const sunY = isDaytime
  ? Math.max(2, Math.sin(sunArc) * sunDist * elevFactor)
  : -10;  // gece: güneş ufkun altında
const sunZ = -25;

// Key light — dolgu ışığı azaltıldığı için güneşi biraz güçlendirip cepheye
// yönlü modelleme/kontrast kazandırıyoruz (düz-soluk görünümü kırar).
const sunLight = new THREE.DirectionalLight(
  isGolden ? 0xffb347 : 0xfff6e0,
  dayF > 0.05 ? (isGolden ? 1.55 : 1.45) : 0
);
sunLight.position.set(sunX, sunY, sunZ);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 200;
sunLight.shadow.camera.left = -40;
sunLight.shadow.camera.right = 40;
sunLight.shadow.camera.top = 40;
sunLight.shadow.camera.bottom = -40;
sunLight.shadow.bias = -0.0005;
scene.add(sunLight);

// Ay — geceleri
if (dayF < 0.2) {
  const moon = new THREE.DirectionalLight(0x8899cc, 0.25 * (1 - dayF));
  moon.position.set(-30, 50, 20);
  scene.add(moon);
}

// Arka ambient fill — düşürüldü (fazla dolgu kontrastı öldürüp sahneyi yıkıyordu)
scene.add(new THREE.AmbientLight(0xffffff, 0.10 + 0.14 * dayF));

/* ── Güneş diski — sky dome yüzeyinde, zemine asla geçmez ─── */
if (dayF > 0.05) {
  // Güneş yönünü normalize et, minimum yükseklik garantile, dome yüzeyine yerleştir
  const _sd = new THREE.Vector3(sunX, Math.max(6, sunY), sunZ).normalize();
  const SDR = 145;  // sky dome placement radius — ufuğa yakın ama içinde
  const sPos = _sd.clone().multiplyScalar(SDR);

  const sunGeo = new THREE.SphereGeometry(4.2, 32, 32);
  const sunMat = new THREE.MeshBasicMaterial({
    color: isGolden ? 0xff8c20 : 0xfffde0, fog: false
  });
  const sunMesh = new THREE.Mesh(sunGeo, sunMat);
  sunMesh.position.copy(sPos);
  sunMesh.renderOrder = 1;
  scene.add(sunMesh);

  // İç parlak çekirdek (bloom için)
  const coreGeo = new THREE.SphereGeometry(2.2, 20, 20);
  const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false });
  const core = new THREE.Mesh(coreGeo, coreMat);
  core.position.copy(sPos);
  core.renderOrder = 2;
  scene.add(core);

  // Hale (glow) — transparan
  const glowMat = new THREE.MeshBasicMaterial({
    color: isGolden ? 0xff5500 : 0xffdd66,
    transparent: true, opacity: isGolden ? 0.14 : 0.09, side: THREE.BackSide, fog: false
  });
  const glow = new THREE.Mesh(new THREE.SphereGeometry(10, 16, 16), glowMat);
  glow.position.copy(sPos);
  scene.add(glow);
}

/* ── Yıldızlar (geceleri) ───────────────────────────────── */
if (dayF < 0.3) {
  const starGeo = new THREE.BufferGeometry();
  const starPos = [];
  for (let i = 0; i < 800; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi   = Math.random() * Math.PI;
    starPos.push(
      120 * Math.sin(phi) * Math.cos(theta),
      Math.abs(120 * Math.cos(phi)) + 5,
      120 * Math.sin(phi) * Math.sin(theta)
    );
  }
  starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
  const starMat = new THREE.PointsMaterial({
    color: 0xffffff, size: 0.35,
    transparent: true, opacity: (1 - dayF / 0.3) * 0.9
  });
  scene.add(new THREE.Points(starGeo, starMat));
}

/* ── Bulutlar (gündüz) ───────────────────────────────────── */
if (dayF > 0.3) {
  function cloud(cx, cy, cz) {
    const g = new THREE.Group();
    const mat = new THREE.MeshLambertMaterial({
      color: 0xffffff, transparent: true, opacity: 0.85
    });
    [[0,0,0,2.8],[2,0.3,0,2],[-1.5,0.2,0,1.8],[3.5,0,0,1.5]].forEach(([x,y,z,r])=>{
      const m = new THREE.Mesh(new THREE.SphereGeometry(r,10,8), mat);
      m.position.set(x,y,z);
      g.add(m);
    });
    g.position.set(cx, cy, cz);
    return g;
  }
  scene.add(cloud(-18, 22, -25));
  scene.add(cloud( 14, 26, -30));
  scene.add(cloud( 28, 20, -20));
}

/* ── Zemin ──────────────────────────────────────────────── */
// Çimen
const grassCol = new THREE.Color(0x16280d).lerp(new THREE.Color(0x4a7c3f), dayF);
const grassMat = new THREE.MeshStandardMaterial({ color: grassCol, roughness: 0.95 });
const grass = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), grassMat);
grass.rotation.x = -Math.PI / 2;
grass.receiveShadow = true;
scene.add(grass);

// Asfalt yol (geniş, gerçekçi)
const roadMat = new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.92, metalness: 0.04 });
const road = new THREE.Mesh(new THREE.PlaneGeometry(60, 14), roadMat);
road.rotation.x = -Math.PI / 2;
road.position.set(0, 0.005, 14);
road.receiveShadow = true;
scene.add(road);

// Yol şeridi — sarı orta çizgi
const stripeMat = new THREE.MeshStandardMaterial({ color: 0xf5c518, roughness: 0.8 });
for (let i = -4; i <= 4; i++) {
  const stripe = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 0.18), stripeMat);
  stripe.rotation.x = -Math.PI / 2;
  stripe.position.set(i * 6, 0.012, 14);
  scene.add(stripe);
}
// Yol kenar beyaz çizgisi
const edgeMat = new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.8 });
for (const ze of [7.2, 20.8]) {
  const edge = new THREE.Mesh(new THREE.PlaneGeometry(60, 0.22), edgeMat);
  edge.rotation.x = -Math.PI / 2;
  edge.position.set(0, 0.012, ze);
  scene.add(edge);
}

// Beton kaldırım (yol ile bina arası)
const sidewalkMat = new THREE.MeshStandardMaterial({ color: 0xc4c8cc, roughness: 0.85 });
const sidewalk = new THREE.Mesh(new THREE.PlaneGeometry(40, 8), sidewalkMat);
sidewalk.rotation.x = -Math.PI / 2;
sidewalk.position.set(0, 0.01, 6);
sidewalk.receiveShadow = true;
scene.add(sidewalk);

// Kaldırım yatay çizgileri (döşeme taşı efekti)
const tileEdgeMat = new THREE.MeshStandardMaterial({ color: 0xaeb2b7, roughness: 0.9 });
for (let ti = -19; ti <= 19; ti++) {
  const tline = new THREE.Mesh(new THREE.PlaneGeometry(0.05, 8), tileEdgeMat);
  tline.rotation.x = -Math.PI / 2;
  tline.position.set(ti * 1, 0.011, 6);
  scene.add(tline);
}

/* ── Yardımcı malzemeler ─────────────────────────────────── */
function concreteMat(hex) {
  return new THREE.MeshStandardMaterial({
    color: hex, roughness: 0.75, metalness: 0.0
  });
}
function metalMat(hex) {
  return new THREE.MeshStandardMaterial({
    color: hex, roughness: 0.3, metalness: 0.7
  });
}

/* ── Bina ────────────────────────────────────────────────── */
const FLOOR_H = 2.8;
const FLOOR_T = 0.22; // döşeme kalınlığı
const B_DEPTH  = 7.0;
const UNIT_W   = 3.0;
const bWidth   = CFG.units_per_floor * UNIT_W;
const bHeight  = CFG.floors * FLOOR_H;
const group    = new THREE.Group();

// Modern mimari renk paleti
// Çerçeve/kolon: koyu antrasit — cepheye derinlik verir
const frameColor = dayF > 0.4 ? 0x2d3748 : 0x1a202c;
const wallMat   = new THREE.MeshStandardMaterial({ color: frameColor, roughness: 0.65, metalness: 0.12 });
// Döşeme/panel arası açık sıva rengi
const plasterMat = new THREE.MeshStandardMaterial({ color: dayF > 0.4 ? 0xddd8d0 : 0x5a5650, roughness: 0.88 });
// Vurgu bandı: terrakota/tuğla rengi (Türk mimarisine gönderme)
const accentMat  = new THREE.MeshStandardMaterial({ color: 0x8b3a1e, roughness: 0.75, metalness: 0.05 });

// Temel — granit/koyu taş görünümü
const baseH = 0.6;
const base = new THREE.Mesh(
  new THREE.BoxGeometry(bWidth + 0.6, baseH, B_DEPTH + 0.6),
  new THREE.MeshStandardMaterial({ color: 0x1c1f26, roughness: 0.55, metalness: 0.15 })
);
base.position.y = baseH / 2;
base.castShadow = true;
base.receiveShadow = true;
group.add(base);

// Zemin kat arkası — koyu granit kaplama (ticari/lobi görünümü)
const lobbyMat = new THREE.MeshStandardMaterial({ color: 0x111520, roughness: 0.4, metalness: 0.25 });
const lobbyFront = new THREE.Mesh(new THREE.BoxGeometry(bWidth, FLOOR_H * 0.75, 0.18), lobbyMat);
lobbyFront.position.set(0, baseH + FLOOR_H * 0.375, B_DEPTH / 2 + 0.09);
group.add(lobbyFront);
const lobbyBack = new THREE.Mesh(new THREE.BoxGeometry(bWidth, FLOOR_H * 0.75, 0.18), lobbyMat);
lobbyBack.position.set(0, baseH + FLOOR_H * 0.375, -B_DEPTH / 2 - 0.09);
group.add(lobbyBack);

// Her kat
for (let f = 0; f < CFG.floors; f++) {
  const yBase = baseH + f * FLOOR_H;

  // Döşeme levhası — koyu metal/beton bant
  const isAccentFloor = (f % 2 === 0); // çift katlarda vurgu bandı
  const slabM = isAccentFloor ? accentMat : new THREE.MeshStandardMaterial({ color: 0x3d4451, roughness: 0.7, metalness: 0.08 });
  const slab = new THREE.Mesh(
    new THREE.BoxGeometry(bWidth + 0.3, FLOOR_T + (isAccentFloor ? 0.1 : 0), B_DEPTH + 0.3),
    slabM
  );
  slab.position.y = yBase;
  slab.castShadow = true;
  slab.receiveShadow = true;
  group.add(slab);

  // Cephe sıva paneli — pencereler arasındaki arka duvar (açık renk)
  for (const zSign of [1, -1]) {
    const wallZ = zSign * (B_DEPTH / 2 + 0.01);
    const colW = 0.35;
    const wallH = FLOOR_H - FLOOR_T - 0.1;

    // Sıva paneli (pencereler arası dolu alan — açık renkli)
    for (let u = 0; u < CFG.units_per_floor; u++) {
      const panelX = -bWidth / 2 + (u + 0.5) * UNIT_W;
      const panelW = UNIT_W - colW - 0.05;
      const plaster = new THREE.Mesh(
        new THREE.BoxGeometry(panelW, wallH, 0.14),
        plasterMat
      );
      plaster.position.set(panelX, yBase + FLOOR_T + wallH / 2, wallZ);
      group.add(plaster);
    }

    // Kolonlar (koyu çerçeve — antrasit)
    for (let u = 0; u <= CFG.units_per_floor; u++) {
      const colX = -bWidth / 2 + u * UNIT_W;
      const col = new THREE.Mesh(
        new THREE.BoxGeometry(colW, wallH, 0.32),
        wallMat
      );
      col.position.set(colX, yBase + FLOOR_T + wallH / 2, wallZ);
      group.add(col);
    }

    // Üst kiriş (koyu metal profil)
    const beam = new THREE.Mesh(
      new THREE.BoxGeometry(bWidth, 0.55, 0.32),
      wallMat
    );
    beam.position.set(0, yBase + FLOOR_H - 0.3, wallZ);
    group.add(beam);

    // Alt pervaz (açık beton)
    const sill = new THREE.Mesh(
      new THREE.BoxGeometry(bWidth, 0.22, 0.36),
      new THREE.MeshStandardMaterial({ color: 0xb0acaa, roughness: 0.8 })
    );
    sill.position.set(0, yBase + FLOOR_T + 0.22, wallZ);
    group.add(sill);
  }

  // Yan duvarlar — açık sıva (geniş panel görünümü)
  for (const xSign of [1, -1]) {
    const wall = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, FLOOR_H - FLOOR_T, B_DEPTH),
      wallMat
    );
    wall.position.set(xSign * (bWidth / 2 + 0.15), yBase + FLOOR_T + (FLOOR_H - FLOOR_T) / 2, 0);
    wall.castShadow = true;
    group.add(wall);
    // Yan cephe sıva paneli
    const sidePanel = new THREE.Mesh(
      new THREE.BoxGeometry(0.14, FLOOR_H - FLOOR_T - 0.2, B_DEPTH - 0.3),
      plasterMat
    );
    sidePanel.position.set(xSign * (bWidth / 2 + 0.08), yBase + FLOOR_T + (FLOOR_H - FLOOR_T) / 2, 0);
    group.add(sidePanel);
  }

  // Pencereler
  const unitIdx0 = f * CFG.units_per_floor;
  const lightsOn = (hour >= 18 || hour < 7) && !CFG.outage;

  for (let u = 0; u < CFG.units_per_floor; u++) {
    const unitGlobal = unitIdx0 + u;
    const isActive = unitGlobal < CFG.active_units;
    const isLit    = isActive && lightsOn;

    const winX = -bWidth / 2 + (u + 0.5) * UNIT_W;
    const winY = yBase + FLOOR_T + 0.75;
    const winW = UNIT_W - 0.5;
    const winH = FLOOR_H - FLOOR_T - 0.9;

    // Cam rengi — PBR gerçekçi cam (yüksek metalness → yansıma)
    let glassColor, emissiveColor, emissiveInt = 0;
    let glassRoughness = 0.04, glassMetalness = 0.65, glassOpacity = 0.78;
    if (CFG.outage) {
      glassColor = isActive && isLit && unitGlobal === 0 ? 0xfbbf24 : 0x050810;
      glassRoughness = 0.08; glassMetalness = 0.3;
    } else if (isLit) {
      // Gece — sıcak sarı ışık, az yansıma
      glassColor = 0xfef3c7;
      emissiveColor = new THREE.Color(0xfcd34d);
      emissiveInt = 0.55;
      glassRoughness = 0.06; glassMetalness = 0.12; glassOpacity = 0.92;
    } else if (dayF > 0.6) {
      // Tam gündüz — yüksek yansımalı mimari cam, gökyüzü tonu
      glassColor = 0x5ba8d4;
      glassRoughness = 0.02; glassMetalness = 0.75; glassOpacity = 0.72;
    } else if (dayF > 0.2) {
      // Sabah/akşam — altın tonu yansıma
      glassColor = 0x7a9cb8;
      glassRoughness = 0.04; glassMetalness = 0.6; glassOpacity = 0.78;
    } else {
      // Gece/alacakaranlık — koyu yansıtıcı
      glassColor = 0x0a1828;
      glassRoughness = 0.06; glassMetalness = 0.4; glassOpacity = 0.85;
    }

    const glassMat = new THREE.MeshStandardMaterial({
      color: glassColor,
      emissive: emissiveColor || new THREE.Color(0x000000),
      emissiveIntensity: emissiveInt,
      roughness: glassRoughness,
      metalness: glassMetalness,
      transparent: true,
      opacity: glassOpacity,
      envMapIntensity: 1.4   // yansıma yoğunluğu artırıldı
    });

    // Ön ve arka cam
    for (const zOff of [B_DEPTH / 2 + 0.02, -(B_DEPTH / 2 + 0.02)]) {
      const win = new THREE.Mesh(
        new THREE.PlaneGeometry(winW, winH),
        glassMat
      );
      win.position.set(winX, winY + winH / 2, zOff);
      if (zOff < 0) win.rotation.y = Math.PI;
      group.add(win);

      // Pencere çerçevesi — koyu alüminyum profil
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x1a2235, roughness: 0.3, metalness: 0.7 });
      const frameB = 0.08;
      // yatay çerçeve üst+alt
      for (const dy of [winH / 2, -winH / 2]) {
        const hf = new THREE.Mesh(
          new THREE.BoxGeometry(winW + frameB, frameB, 0.06), frameMat
        );
        hf.position.set(winX, winY + winH / 2 + dy, zOff);
        group.add(hf);
      }
      // dikey çerçeve sol+sağ
      for (const dx of [winW / 2, -winW / 2]) {
        const vf = new THREE.Mesh(
          new THREE.BoxGeometry(frameB, winH + frameB, 0.06), frameMat
        );
        vf.position.set(winX + dx, winY + winH / 2, zOff);
        group.add(vf);
      }
    }

    // İç ışık noktaları
    if (isLit) {
      const pl = new THREE.PointLight(0xfcd34d, 0.5, 5);
      pl.position.set(winX, winY + winH / 2, 0);
      group.add(pl);
    }

    // Balkon (çift katlı binada her katta)
    if (f > 0 && f % 1 === 0) {
      const bal = new THREE.Mesh(
        new THREE.BoxGeometry(winW * 0.85, 0.08, 0.9),
        concreteMat(0xaaa8a4)
      );
      bal.position.set(winX, yBase + FLOOR_T + 0.04, B_DEPTH / 2 + 0.49);
      bal.castShadow = true;
      group.add(bal);

      // Korkuluk
      for (const dx of [winW * 0.425 - 0.04, -(winW * 0.425 - 0.04)]) {
        const rail = new THREE.Mesh(
          new THREE.BoxGeometry(0.04, 0.75, 0.04),
          metalMat(0x9ca3af)
        );
        rail.position.set(winX + dx, yBase + FLOOR_T + 0.45, B_DEPTH / 2 + 0.49);
        group.add(rail);
      }
      const topRail = new THREE.Mesh(
        new THREE.BoxGeometry(winW * 0.85, 0.04, 0.04),
        metalMat(0x9ca3af)
      );
      topRail.position.set(winX, yBase + FLOOR_T + 0.79, B_DEPTH / 2 + 0.49);
      group.add(topRail);
    }
  }
}

/* ── Çatı ────────────────────────────────────────────────── */
const roofY = baseH + bHeight;
// Çatı döşemesi — koyu metal
const roofSlab = new THREE.Mesh(
  new THREE.BoxGeometry(bWidth + 0.4, 0.3, B_DEPTH + 0.4),
  new THREE.MeshStandardMaterial({ color: 0x1e2433, roughness: 0.6, metalness: 0.2 })
);
roofSlab.position.y = roofY + 0.15;
group.add(roofSlab);

// Parapet (çatı kenar duvarı) — terrakota vurgu
for (const [axis, sign] of [['x',1],['x',-1],['z',1],['z',-1]]) {
  const isX = axis === 'x';
  const par = new THREE.Mesh(
    new THREE.BoxGeometry(
      isX ? 0.28 : bWidth + 0.55,
      0.9,
      isX ? B_DEPTH + 0.55 : 0.28
    ),
    accentMat
  );
  par.position.set(
    isX ? sign * (bWidth / 2 + 0.14) : 0,
    roofY + 0.75,
    isX ? 0 : sign * (B_DEPTH / 2 + 0.14)
  );
  group.add(par);
}
// Parapet üst metal profil
for (const [axis, sign] of [['x',1],['x',-1],['z',1],['z',-1]]) {
  const isX = axis === 'x';
  const cap = new THREE.Mesh(
    new THREE.BoxGeometry(
      isX ? 0.32 : bWidth + 0.62,
      0.1,
      isX ? B_DEPTH + 0.62 : 0.32
    ),
    new THREE.MeshStandardMaterial({ color: 0x4a5568, roughness: 0.4, metalness: 0.5 })
  );
  cap.position.set(
    isX ? sign * (bWidth / 2 + 0.16) : 0,
    roofY + 1.25,
    isX ? 0 : sign * (B_DEPTH / 2 + 0.16)
  );
  group.add(cap);
}

/* ── Güneş panelleri ─────────────────────────────────────── */
const solarNorm = CFG.solar_norm;
const nPanels   = Math.min(CFG.panels, 48);
const pCols     = Math.ceil(Math.sqrt(nPanels * (bWidth / B_DEPTH)));
const pRows     = Math.ceil(nPanels / pCols);
const pW        = (bWidth * 0.82) / pCols;
const pD        = (B_DEPTH * 0.82) / pRows;
let placed = 0;

for (let r = 0; r < pRows && placed < nPanels; r++) {
  for (let c = 0; c < pCols && placed < nPanels; c++, placed++) {
    const px = -bWidth * 0.41 + (c + 0.5) * (bWidth * 0.82 / pCols);
    const pz = -B_DEPTH * 0.41 + (r + 0.5) * (B_DEPTH * 0.82 / pRows);

    // Panel gövdesi
    const panelMat = new THREE.MeshStandardMaterial({
      color: 0x0c1e3a,
      emissive: new THREE.Color(0x1e6bc4),
      emissiveIntensity: solarNorm * 0.7,
      roughness: 0.2,
      metalness: 0.4
    });
    const panel = new THREE.Mesh(
      new THREE.BoxGeometry(pW * 0.88, 0.06, pD * 0.88),
      panelMat
    );
    panel.position.set(px, roofY + 0.45, pz);
    panel.rotation.x = -0.32; // güneye eğim
    group.add(panel);
    // Üretim varsa panel hafifçe pırıldar (gündüz emissive yüksek, gece sıfıra iner)
    if (solarNorm > 0.05) {
      energyFX.push({ mat: panelMat, base: solarNorm * 0.7, amp: solarNorm * 0.12, speed: 1.3, phase: placed * 0.5 });
    }

    // Panel ızgara çizgileri
    const gridMat = new THREE.MeshBasicMaterial({color: 0x1a3a6a});
    for (let gi = 1; gi < 4; gi++) {
      const gl = new THREE.Mesh(
        new THREE.BoxGeometry(pW * 0.88, 0.01, 0.02), gridMat
      );
      gl.position.set(px, roofY + 0.48, pz - pD * 0.44 + gi * pD * 0.22);
      group.add(gl);
    }

    // Glow effect (üretim varsa)
    if (solarNorm > 0.1) {
      const glowPt = new THREE.PointLight(0x60a5fa, solarNorm * 0.4, 3);
      glowPt.position.set(px, roofY + 0.7, pz);
      group.add(glowPt);
    }

    // Ayaklar (destek profili)
    for (const dx of [-pW * 0.35, pW * 0.35]) {
      const leg = new THREE.Mesh(
        new THREE.BoxGeometry(0.04, 0.25, 0.04),
        metalMat(0x6b7280)
      );
      leg.position.set(px + dx, roofY + 0.28, pz);
      group.add(leg);
    }
  }
}

/* ── HVAC — klima üniteleri çatıda ──────────────────────── */
if (CFG.hvac) {
  const nAC = Math.min(CFG.floors, 5);
  for (let i = 0; i < nAC; i++) {
    const ac = new THREE.Mesh(
      new THREE.BoxGeometry(0.95, 0.5, 0.65),
      metalMat(0xd1d5db)
    );
    ac.position.set(bWidth * 0.38 - i * 1.15, roofY + 0.56, B_DEPTH * 0.36);
    group.add(ac);
    // Fan çark
    const fan = new THREE.Mesh(
      new THREE.CylinderGeometry(0.22, 0.22, 0.06, 12),
      metalMat(0x9ca3af)
    );
    fan.position.set(bWidth * 0.38 - i * 1.15, roofY + 0.83, B_DEPTH * 0.36);
    group.add(fan);
  }
}

/* ── Su deposu / tank ────────────────────────────────────── */
if (CFG.su_pompasi) {
  // Silindir tank
  const tank = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.7, 1.4, 16),
    new THREE.MeshStandardMaterial({color: 0xe2e8f0, roughness: 0.5, metalness: 0.3})
  );
  tank.position.set(-bWidth * 0.3, roofY + 1.1, -B_DEPTH * 0.25);
  group.add(tank);
  // Tank kapağı
  const tankCap = new THREE.Mesh(
    new THREE.CylinderGeometry(0.72, 0.72, 0.1, 16),
    metalMat(0x9ca3af)
  );
  tankCap.position.set(-bWidth * 0.3, roofY + 1.85, -B_DEPTH * 0.25);
  group.add(tankCap);
  // Boru
  const pipe = new THREE.Mesh(
    new THREE.CylinderGeometry(0.06, 0.06, 0.9, 8),
    metalMat(0x6b7280)
  );
  pipe.position.set(-bWidth * 0.3 + 0.55, roofY + 0.55, -B_DEPTH * 0.25);
  group.add(pipe);
}

/* ── Güneş Isıtıcı — kolektörler ────────────────────────── */
if (CFG.gunes_isitici) {
  const nColl = Math.min(Math.ceil(CFG.floors / 2), 6);
  for (let i = 0; i < nColl; i++) {
    const cx = -bWidth * 0.38 + i * (bWidth * 0.76 / Math.max(nColl - 1, 1));
    // Kolektör plakası (güneş ısıtıcı, PV'den farklı — koyu mavi/siyah mat)
    const coll = new THREE.Mesh(
      new THREE.BoxGeometry(0.8, 0.06, 1.2),
      new THREE.MeshStandardMaterial({
        color: 0x0c1a2e, roughness: 0.15, metalness: 0.2,
        emissive: new THREE.Color(0x0a1a30), emissiveIntensity: 0.1
      })
    );
    coll.position.set(cx, roofY + 0.6, -B_DEPTH * 0.35);
    coll.rotation.x = -0.5; // daha dik açı (sıcak su için)
    group.add(coll);
    // Boru bağlantısı
    const tube = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.5, 6),
      metalMat(0xef4444) // kırmızı boru (sıcak su)
    );
    tube.rotation.z = Math.PI / 2;
    tube.position.set(cx, roofY + 0.4, -B_DEPTH * 0.35);
    group.add(tube);
  }
}

/* ── Jeneratör ───────────────────────────────────────────── */
if (CFG.jenerator) {
  const genX = -(bWidth / 2 + 3.8);
  // Kasa
  const genCase = new THREE.Mesh(
    new THREE.BoxGeometry(2.4, 1.1, 1.2),
    metalMat(0x374151)
  );
  genCase.position.set(genX, 0.55, 1.0);
  group.add(genCase);
  // Üst panel
  const genTop = new THREE.Mesh(
    new THREE.BoxGeometry(2.4, 0.08, 1.2),
    metalMat(0x4b5563)
  );
  genTop.position.set(genX, 1.14, 1.0);
  group.add(genTop);
  // Egzoz borusu
  const exhaust = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08, 0.06, 0.9, 8),
    metalMat(0x1f2937)
  );
  exhaust.position.set(genX + 0.9, 1.5, 0.9);
  group.add(exhaust);
  // Çalışıyor etiketi (outage veya aktif ise kırmızı ışık)
  const running = CFG.outage;
  const genLed = new THREE.Mesh(
    new THREE.SphereGeometry(0.09, 8, 8),
    new THREE.MeshStandardMaterial({
      color: running ? 0xef4444 : 0x374151,
      emissive: running ? new THREE.Color(0xef4444) : new THREE.Color(0x000000),
      emissiveIntensity: running ? 1.2 : 0
    })
  );
  genLed.position.set(genX - 0.8, 1.0, 1.65);
  group.add(genLed);
  if (running) {
    const genLight = new THREE.PointLight(0xef4444, 0.5, 5);
    genLight.position.copy(genLed.position);
    group.add(genLight);
    // Duman efekti (duman rengi partiküller değil, sadece işaret)
    const smoke = new THREE.Mesh(
      new THREE.SphereGeometry(0.18, 6, 6),
      new THREE.MeshBasicMaterial({color: 0x6b7280, transparent: true, opacity: 0.5})
    );
    smoke.position.set(genX + 0.9, 2.2, 0.9);
    group.add(smoke);
  }
  // Etiket plakası
  const plate = new THREE.Mesh(
    new THREE.BoxGeometry(0.7, 0.3, 0.04),
    new THREE.MeshStandardMaterial({color: 0xfbbf24})
  );
  plate.position.set(genX, 0.7, 1.65);
  group.add(plate);
}

/* ── Giriş kapısı ────────────────────────────────────────── */
const doorW = Math.min(UNIT_W * 0.6, 1.8);
const doorH = 2.2;
// Kapı çerçevesi
const doorFrame = new THREE.Mesh(
  new THREE.BoxGeometry(doorW + 0.2, doorH + 0.2, 0.15),
  concreteMat(0x7a7570)
);
doorFrame.position.set(0, baseH + (doorH + 0.2) / 2, B_DEPTH / 2 + 0.08);
group.add(doorFrame);
// Kapı
const doorMat = new THREE.MeshStandardMaterial({
  color: 0x1e3a5f, roughness: 0.4, metalness: 0.5
});
const door = new THREE.Mesh(new THREE.BoxGeometry(doorW, doorH, 0.06), doorMat);
door.position.set(0, baseH + doorH / 2, B_DEPTH / 2 + 0.12);
group.add(door);
// Kapı kolu
const handle = new THREE.Mesh(
  new THREE.CylinderGeometry(0.03, 0.03, 0.28, 8),
  metalMat(0xf59e0b)
);
handle.rotation.z = Math.PI / 2;
handle.position.set(doorW * 0.28, baseH + doorH * 0.42, B_DEPTH / 2 + 0.16);
group.add(handle);

// Giriş merdivenleri
for (let s = 0; s < 3; s++) {
  const step = new THREE.Mesh(
    new THREE.BoxGeometry(doorW * 2 - s * 0.4, 0.14, 0.38 - s * 0.02),
    concreteMat(0xaaa8a4)
  );
  step.position.set(0, s * 0.14, B_DEPTH / 2 + 0.55 + s * 0.22);
  group.add(step);
}

/* ── Batarya ünitesi ─────────────────────────────────────── */
const soc     = CFG.soc;
const battX   = bWidth / 2 + 3.2;
const battY0  = 0;
const battH   = 3.5;
const battW   = 1.6;
const battD   = 0.9;

// Metal kasa
const battCase = new THREE.Mesh(
  new THREE.BoxGeometry(battW, battH, battD),
  metalMat(0x374151)
);
battCase.position.set(battX, battY0 + battH / 2, 1.0);
battCase.castShadow = true;
group.add(battCase);

// Doluluk çubuğu (ön yüz)
const fillH   = Math.max((battH - 0.3) * soc, 0.05);
const fillCol = new THREE.Color(0xef4444)
  .lerp(new THREE.Color(0xfbbf24), Math.min(soc / 0.5, 1))
  .lerp(new THREE.Color(0x22c55e), Math.max((soc - 0.5) / 0.5, 0));
const battFillMat = new THREE.MeshStandardMaterial({
  color: fillCol,
  emissive: fillCol,
  emissiveIntensity: 0.35,
  roughness: 0.5
});
const battFill = new THREE.Mesh(
  new THREE.BoxGeometry(battW - 0.22, fillH, 0.06),
  battFillMat
);
battFill.position.set(battX, battY0 + 0.15 + fillH / 2, 1.0 + battD / 2 + 0.04);
group.add(battFill);
// Batarya doluluğu hafifçe "solur" — enerji canlılığı
energyFX.push({ mat: battFillMat, base: 0.35, amp: 0.18, speed: 1.6, phase: 1.2 });

// Batarya logo / etiket
const battLabel = new THREE.Mesh(
  new THREE.BoxGeometry(battW - 0.3, 0.4, 0.04),
  new THREE.MeshStandardMaterial({color: 0x1e293b})
);
battLabel.position.set(battX, battY0 + battH - 0.35, 1.0 + battD / 2 + 0.04);
group.add(battLabel);

// LED durum ışığı
const ledColor = soc > 0.5 ? 0x22c55e : soc > 0.2 ? 0xfbbf24 : 0xef4444;
const led = new THREE.Mesh(
  new THREE.SphereGeometry(0.1, 8, 8),
  new THREE.MeshStandardMaterial({
    color: ledColor, emissive: new THREE.Color(ledColor), emissiveIntensity: 1.0
  })
);
led.position.set(battX + battW * 0.28, battY0 + battH + 0.15, 1.0);
group.add(led);
const ledLight = new THREE.PointLight(ledColor, 0.5, 3);
ledLight.position.copy(led.position);
group.add(ledLight);

// Batarya bağlantı kabloları
const cableGeo = new THREE.CylinderGeometry(0.04, 0.04, 2.0, 6);
const cableMat = metalMat(0x111827);
const cable = new THREE.Mesh(cableGeo, cableMat);
cable.rotation.z = Math.PI / 4;
cable.position.set(battX - 1.2, battY0 + 1.2, 0.8);
group.add(cable);

/* ── EV Şarj istasyonu ───────────────────────────────────── */
if (CFG.ev) {
  const evX = battX + 0.6, evZ = 5.5;
  const evCharging = (hour >= 21 || hour < 7) && !CFG.outage;

  // Direk
  const post = new THREE.Mesh(
    new THREE.BoxGeometry(0.18, 2.2, 0.18),
    metalMat(0x374151)
  );
  post.position.set(evX - 1.5, 1.1, evZ);
  post.castShadow = true;
  group.add(post);

  // İstasyon ünitesi
  const station = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.8, 0.3),
    metalMat(evCharging ? 0x166534 : 0x374151)
  );
  station.position.set(evX - 1.5, 1.9, evZ);
  group.add(station);

  // EV ekranı
  const screen = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.3, 0.02),
    new THREE.MeshStandardMaterial({
      color: evCharging ? 0x4ade80 : 0x1e293b,
      emissive: evCharging ? new THREE.Color(0x4ade80) : new THREE.Color(0x000000),
      emissiveIntensity: evCharging ? 0.5 : 0
    })
  );
  screen.position.set(evX - 1.5, 1.95, evZ + 0.16);
  group.add(screen);

  // Araç
  const car = new THREE.Group();
  // Gövde
  const bodyMat = new THREE.MeshStandardMaterial({
    color: 0x1d4ed8, roughness: 0.3, metalness: 0.6
  });
  const carBody = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.8, 1.8), bodyMat);
  carBody.position.y = 0.55;
  car.add(carBody);

  // Kabin
  const cabin = new THREE.Mesh(
    new THREE.BoxGeometry(2.0, 0.7, 1.6),
    new THREE.MeshStandardMaterial({color: 0x1e3a8a, roughness: 0.4, metalness: 0.5})
  );
  cabin.position.set(-0.2, 1.15, 0);
  car.add(cabin);

  // Camlar
  const glassMat2 = new THREE.MeshStandardMaterial({
    color: 0xbae6fd, transparent: true, opacity: 0.6, roughness: 0.05
  });
  const windshield = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.6), glassMat2);
  windshield.rotation.y = -Math.PI / 6;
  windshield.position.set(0.7, 1.2, 0);
  car.add(windshield);

  // Tekerlekler
  const wheelMat = new THREE.MeshStandardMaterial({color: 0x111827, roughness: 0.9});
  const rimMat   = metalMat(0xd1d5db);
  for (const dx of [-1.3, 1.3]) for (const dz of [-0.9, 0.9]) {
    const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.25, 16), wheelMat);
    wheel.rotation.x = Math.PI / 2;
    wheel.position.set(dx, 0.38, dz);
    car.add(wheel);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.26, 8), rimMat);
    rim.rotation.x = Math.PI / 2;
    rim.position.set(dx, 0.38, dz);
    car.add(rim);
  }

  // Farlar
  const headlightMat = new THREE.MeshStandardMaterial({
    color: 0xfef9c3, emissive: new THREE.Color(0xfef9c3),
    emissiveIntensity: evCharging ? 0 : 0.1
  });
  for (const dz of [-0.6, 0.6]) {
    const hl = new THREE.Mesh(new THREE.CircleGeometry(0.14, 8), headlightMat);
    hl.rotation.y = -Math.PI / 2;
    hl.position.set(-1.91, 0.65, dz);
    car.add(hl);
  }

  car.position.set(evX + 0.5, 0.01, evZ);
  car.castShadow = true;
  // Gerçekçi elektrikli araç modeli verilmişse ilkel kutuları onunla değiştir (~1.5 m boy)
  swapWithModel(car, ASSETS.car, { targetHeight: 1.5, rotY: -Math.PI / 2 });
  group.add(car);

  // Şarj kablosu — şarj sırasında yeşil enerji akışı gibi nabız atar
  const evCableMat = new THREE.MeshStandardMaterial({
    color: 0x065f46, roughness: 0.4, metalness: 0.6,
    emissive: new THREE.Color(0x22c55e),
    emissiveIntensity: evCharging ? 0.6 : 0.0
  });
  const chargeCable = new THREE.Mesh(
    new THREE.CylinderGeometry(0.03, 0.03, 1.8, 6),
    evCableMat
  );
  chargeCable.rotation.z = Math.PI / 3;
  chargeCable.position.set(evX - 0.8, 0.8, evZ);
  group.add(chargeCable);

  if (evCharging) {
    // Kabloyu "akan enerji" gibi yakıp söndür (Math.sin nabzı)
    energyFX.push({ mat: evCableMat, base: 0.55, amp: 0.45, speed: 5.0, phase: 0 });
    const evLight = new THREE.PointLight(0x4ade80, 0.6, 5);
    evLight.position.set(evX - 1.5, 2.5, evZ);
    group.add(evLight);
  }
}

/* ── Asansör dışı şaft ───────────────────────────────────── */
let cab = null;
if (CFG.elevator) {
  const shaftMat = new THREE.MeshStandardMaterial({
    color: 0x93c5fd, transparent: true, opacity: 0.18, roughness: 0.1
  });
  const shaft = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, bHeight, 1.2), shaftMat
  );
  shaft.position.set(-bWidth / 2 - 0.9, baseH + bHeight / 2, 0);
  group.add(shaft);

  const shaftBorder = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, bHeight, 1.2),
    new THREE.MeshBasicMaterial({color: 0x3b82f6, wireframe: true, opacity: 0.3, transparent: true})
  );
  shaftBorder.position.copy(shaft.position);
  group.add(shaftBorder);

  cab = new THREE.Mesh(
    new THREE.BoxGeometry(1.0, 1.1, 1.0),
    new THREE.MeshStandardMaterial({color: 0xe2e8f0, roughness: 0.5})
  );
  cab.position.set(-bWidth / 2 - 0.9, baseH + 0.6, 0);
  group.add(cab);
}

/* ── Mimari ağaçlar (düzleştirilmiş küre tacı — low-poly koni yok) ──── */
function tree(x, z, h) {
  const g = new THREE.Group();
  // İnce mimari gövde
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x1e140a, roughness: 0.92, metalness: 0.0 });
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.085, h * 0.52, 8), trunkMat);
  trunk.position.y = h * 0.26;
  g.add(trunk);
  // Düzleştirilmiş küre taç (elipsoid — çok daha doğal)
  const leafCol = dayF > 0.35
    ? new THREE.Color(0x2a5c1a).lerp(new THREE.Color(0x3a7228), dayF * 0.7)
    : new THREE.Color(0x111e0a);
  const canopyMat = new THREE.MeshStandardMaterial({ color: leafCol, roughness: 0.88, metalness: 0.0 });
  const canopy = new THREE.Mesh(new THREE.SphereGeometry(h * 0.27, 10, 8), canopyMat);
  canopy.scale.set(1, 0.62, 1); // elipsoid
  canopy.position.y = h * 0.52 + h * 0.17;
  g.add(canopy);
  g.position.set(x, 0, z);
  g.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });
  swapWithModel(g, ASSETS.tree, { targetHeight: h, rotY: Math.random() * Math.PI * 2 });
  return g;
}

// 4 ağaç, simetrik düzende — minimal & temiz
group.add(tree(-bWidth / 2 - 3.5, 1.5, 4.8));
group.add(tree(-bWidth / 2 - 3.5, -2.5, 5.6));
group.add(tree( bWidth / 2 + battW + 4.8, 1.5, 4.2));
group.add(tree( bWidth / 2 + battW + 4.8, -2.2, 5.0));

/* ── Digital Twin zemin grid ────────────────────────────── */
// Tech estetiği: ince açık çizgiler — "sanal dünya" hissi
{
  const gridMat = new THREE.LineBasicMaterial({
    color: 0x1e3a5c, transparent: true, opacity: 0.45
  });
  const gridSize = 80, gridDiv = 40;
  const step = gridSize / gridDiv;
  const points = [];
  for (let i = 0; i <= gridDiv; i++) {
    const p = -gridSize / 2 + i * step;
    points.push(-gridSize / 2, 0, p,  gridSize / 2, 0, p);
    points.push(p, 0, -gridSize / 2,  p, 0, gridSize / 2);
  }
  const gridGeo = new THREE.BufferGeometry();
  gridGeo.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  const gridLines = new THREE.LineSegments(gridGeo, gridMat);
  gridLines.position.y = 0.018;
  scene.add(gridLines);
}

/* ── Enerji akış partikülleri (Digital Twin görselleştirme) ── */
// Solar panellerden bataryaya, bataryadan binaya akan enerji
const flowParticles = [];
const roofCx = group.position.x;
const roofCy = roofY + 0.5;
const battCx = battX;
const battCy = battY0 + battH * 0.5;

function mkFlowParticle(fx, fy, fz, tx, ty, tz, col, spd, phase) {
  const geo = new THREE.SphereGeometry(0.09, 6, 6);
  const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.9 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.visible = false;
  scene.add(mesh);
  return { mesh, from: new THREE.Vector3(fx, fy, fz), to: new THREE.Vector3(tx, ty, tz),
           t: phase, spd };
}

// Solar → Batarya (üretim varsa)
if (CFG.solar_norm > 0.08) {
  const flowN = Math.min(5, Math.ceil(CFG.solar_norm * 6));
  for (let i = 0; i < flowN; i++) {
    flowParticles.push(mkFlowParticle(
      0, roofCy, 0,              // çatıdan
      battCx, battCy, 1.0,       // bataryaya
      0xfbbf24, 0.38 + Math.random() * 0.18, i / flowN
    ));
  }
}
// Batarya → Bina girişi (SOC > 0.15 ise)
if (soc > 0.15) {
  const flowN2 = 3;
  for (let i = 0; i < flowN2; i++) {
    flowParticles.push(mkFlowParticle(
      battCx, battCy, 1.0,       // bataryadan
      0, baseH + bHeight * 0.35, B_DEPTH / 2,  // bina cephesine
      0x60a5fa, 0.28 + Math.random() * 0.14, i / flowN2
    ));
  }
}

/* ── Güvenlik kameraları ─────────────────────────────────── */
if (CFG.kamera) {
  const camPositions = [
    [bWidth / 2 + 0.05,  baseH + bHeight - 0.4,  B_DEPTH / 2 + 0.05,  Math.PI * 0.75],
    [-bWidth / 2 - 0.05, baseH + bHeight - 0.4,  B_DEPTH / 2 + 0.05, -Math.PI * 0.25],
    [bWidth / 2 + 0.05,  baseH + bHeight - 0.4, -B_DEPTH / 2 - 0.05,  Math.PI * 0.25],
    [-bWidth / 2 - 0.05, baseH + bHeight - 0.4, -B_DEPTH / 2 - 0.05,  Math.PI * 1.25],
  ];
  camPositions.forEach(([cx, cy, cz, ry]) => {
    // Braket
    const bracket = new THREE.Mesh(
      new THREE.BoxGeometry(0.06, 0.28, 0.06),
      metalMat(0x374151)
    );
    bracket.position.set(cx, cy, cz);
    group.add(bracket);
    // Kamera gövdesi
    const camBody = new THREE.Mesh(
      new THREE.BoxGeometry(0.22, 0.14, 0.32),
      metalMat(0x1f2937)
    );
    camBody.rotation.y = ry;
    camBody.position.set(
      cx + Math.sin(ry) * 0.18,
      cy - 0.18,
      cz + Math.cos(ry) * 0.18
    );
    group.add(camBody);
    // Lens
    const lens = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.05, 0.1, 8),
      new THREE.MeshStandardMaterial({color: 0x000000, roughness: 0.1, metalness: 0.8})
    );
    lens.rotation.x = Math.PI / 2;
    lens.position.copy(camBody.position);
    lens.position.y -= 0.02;
    group.add(lens);
    // Kızılötesi LED (gece)
    if (hour >= 19 || hour < 7) {
      const irLed = new THREE.PointLight(0xff0000, 0.1, 2.5);
      irLed.position.copy(camBody.position);
      group.add(irLed);
    }
  });
}

/* ── Kesinti uyarısı ─────────────────────────────────────── */
let alarmLight = null;
if (CFG.outage) {
  const alarmEl = document.getElementById('alarm');
  if (alarmEl) { alarmEl.style.display = 'block'; alarmEl.style.animation = 'blink 0.7s infinite'; }

  alarmLight = new THREE.PointLight(0xef4444, 2.0, 35);
  alarmLight.position.set(0, roofY + 3, 0);
  scene.add(alarmLight);

  // Kırmızı tepe ışığı
  const beacon = new THREE.Mesh(
    new THREE.SphereGeometry(0.3, 8, 8),
    new THREE.MeshStandardMaterial({
      color: 0xef4444, emissive: new THREE.Color(0xef4444), emissiveIntensity: 1
    })
  );
  beacon.position.set(0, roofY + 1.2, 0);
  group.add(beacon);
}

/* ── Sokak lambası ───────────────────────────────────────── */
function streetLamp(x, z) {
  const g = new THREE.Group();
  const pole = new THREE.Mesh(
    new THREE.CylinderGeometry(0.06, 0.08, 5.5, 8),
    metalMat(0x4b5563)
  );
  pole.position.y = 2.75;
  g.add(pole);
  const head = new THREE.Mesh(
    new THREE.BoxGeometry(0.6, 0.2, 0.3),
    metalMat(0x374151)
  );
  head.position.set(0.25, 5.6, 0);
  g.add(head);

  if (hour >= 19 || hour < 7) {
    const lamp = new THREE.PointLight(0xfef08a, 1.0, 12);
    lamp.position.set(0.25, 5.4, 0);
    g.add(lamp);
    const bulb = new THREE.Mesh(
      new THREE.SphereGeometry(0.12, 8, 8),
      new THREE.MeshStandardMaterial({
        color: 0xfef08a, emissive: new THREE.Color(0xfef08a), emissiveIntensity: 1
      })
    );
    bulb.position.set(0.25, 5.4, 0);
    g.add(bulb);
  }

  g.position.set(x, 0, z);
  // Gerçekçi sokak lambası modeli verilmişse ilkel geometriyle değiştir
  swapWithModel(g, ASSETS.lamp, { targetHeight: 5.8 });
  return g;
}

group.add(streetLamp(-bWidth / 2 - 1, 9));
group.add(streetLamp( bWidth / 2 + 1, 9));

/* ── Sahneye ekle ────────────────────────────────────────── */
group.position.set(0, 0, 0);
group.traverse(c => {
  if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; }
});
scene.add(group);

/* ── PBR ortam haritası — YALNIZCA gerçek HDRI verilirse ──── */
// NOT: Sahneden otomatik env üretmek (pmrem.fromScene) haritayı sahne
// merkezinden = bina içi karanlığından örneklediği için görüntüyü
// koyulaştırıyordu; kaldırıldı. Gerçek yansıma istiyorsan assets={'hdri': url} ver.
if (ASSETS.hdri && THREE.RGBELoader) {
  try {
    const pmrem = new THREE.PMREMGenerator(renderer);
    pmrem.compileEquirectangularShader();
    new THREE.RGBELoader().load(ASSETS.hdri, (hdr) => {
      scene.environment = pmrem.fromEquirectangular(hdr).texture;  // sadece yansıma; ışık zaten kurulu
      hdr.dispose();
    }, undefined, (e) => console.warn('HDRI yüklenemedi:', e));
  } catch (e) { console.warn('Ortam haritası kurulamadı:', e); }
}

/* ── Digital Twin HUD ───────────────────────────────────── */
const hud = document.getElementById('dt-hud');
const socPct = Math.round(soc * 100);
const socColor = soc > 0.6 ? '#4ade80' : soc > 0.3 ? '#fbbf24' : '#f87171';
const socBarColor = soc > 0.6 ? '#22c55e' : soc > 0.3 ? '#f59e0b' : '#ef4444';
const solarPct = Math.round(CFG.solar_norm * 100);
const timeStr = String(hour).padStart(2,'0') + ':00';
const phaseStr = hour >= 6 && hour < 10 ? CFG.t.morning : hour >= 10 && hour < 17 ? CFG.t.daytime : hour >= 17 && hour < 21 ? CFG.t.evening : CFG.t.night;
const isCharging = CFG.solar_norm > 0.05 && soc < 0.98;
const isDischarging = soc > 0.15 && CFG.solar_norm < 0.1 && (hour >= 17 || hour < 7);
const battStatus = isCharging ? CFG.t.charging : isDischarging ? CFG.t.discharging : CFG.t.standby;
// Alarm badge metnini dile göre güncelle
const _alarmTxt = document.getElementById('alarm-text');
if (_alarmTxt) _alarmTxt.textContent = CFG.t.grid_outage;
const battDotColor = isCharging ? '#4ade80' : isDischarging ? '#60a5fa' : '#94a3b8';

hud.innerHTML = `
  <div style="flex:0 0 auto;padding-right:18px;border-right:1px solid rgba(255,255,255,.07);">
    <div class="dt-logo">SmartHome · Digital Twin</div>
    <div style="font-size:28px;font-weight:800;color:#f8fafc;letter-spacing:-.02em;line-height:1">${timeStr}</div>
    <div class="dt-sub" style="color:rgba(148,163,184,.6)">${phaseStr} · ${CFG.t.simulation}</div>
  </div>
  <div class="dt-metric">
    <div class="dt-label">${CFG.t.battery}</div>
    <div class="dt-value" style="color:${socColor}">${socPct}<span style="font-size:12px;font-weight:500;color:rgba(148,163,184,.6)">%</span></div>
    <div class="dt-bar-wrap"><div class="dt-bar" style="width:${socPct}%;background:${socBarColor}"></div></div>
    <div class="dt-sub"><span class="dt-status-dot" style="background:${battDotColor};box-shadow:0 0 6px ${battDotColor}"></span>${battStatus}</div>
  </div>
  <div class="dt-metric">
    <div class="dt-label">${CFG.t.solar}</div>
    <div class="dt-value" style="color:${CFG.solar_norm > 0.1 ? '#fbbf24' : '#94a3b8'}">${CFG.solar_kw.toFixed(1)}<span style="font-size:12px;font-weight:500;color:rgba(148,163,184,.6)"> kW</span></div>
    <div class="dt-bar-wrap"><div class="dt-bar" style="width:${solarPct}%;background:linear-gradient(90deg,#f59e0b,#fbbf24)"></div></div>
    <div class="dt-sub">${solarPct}% ${CFG.t.capacity}</div>
  </div>
  <div class="dt-metric">
    <div class="dt-label">${CFG.t.active} ${CFG.unit_label}</div>
    <div class="dt-value">${CFG.active_units}<span style="font-size:14px;font-weight:400;color:rgba(148,163,184,.4)">/${CFG.total_units}</span></div>
    <div class="dt-bar-wrap"><div class="dt-bar" style="width:${Math.round(CFG.active_units/CFG.total_units*100)}%;background:linear-gradient(90deg,#3b82f6,#60a5fa)"></div></div>
    <div class="dt-sub">${Math.round(CFG.active_units/CFG.total_units*100)}% ${CFG.t.occupancy}</div>
  </div>
  <div class="dt-metric" style="flex:0 0 auto;border-right:none">
    <div class="dt-label">${CFG.t.grid_status}</div>
    <div style="display:flex;align-items:center;gap:6px;margin-top:2px">
      <div style="width:8px;height:8px;border-radius:50%;background:${CFG.outage?'#ef4444':'#4ade80'};box-shadow:0 0 8px ${CFG.outage?'#ef4444':'#22c55e'};flex-shrink:0"></div>
      <div class="dt-value" style="font-size:14px;color:${CFG.outage?'#f87171':'#4ade80'}">${CFG.outage?CFG.t.outage_status:CFG.t.connected}</div>
    </div>
    <div class="dt-sub" style="margin-top:8px">${CFG.t.rl_agent}</div>
  </div>
`;

/* ── Kamera ──────────────────────────────────────────────── */
// FOV 38 → daha dar, daha mimari/profesyonel; az distorsiyon
const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 500);
const lookAt = new THREE.Vector3(0, (baseH + bHeight) * 0.38, 0);
const R0 = Math.max(bHeight * 2.6, bWidth * 2.8, 20);
// phi 0.40 → biraz daha geniş açı, bina tam görünsün
let theta = 0.62, phi = 0.40, radius = R0, autoRot = true;

function updateCam() {
  camera.position.set(
    lookAt.x + radius * Math.cos(phi) * Math.sin(theta),
    lookAt.y + radius * Math.sin(phi),
    lookAt.z + radius * Math.cos(phi) * Math.cos(theta)
  );
  camera.lookAt(lookAt);
}

/* ── Fare kontrolleri ────────────────────────────────────── */
let drag = false, px = 0, py = 0;
renderer.domElement.addEventListener('mousedown', e => {
  drag = true; autoRot = false; px = e.clientX; py = e.clientY;
});
window.addEventListener('mouseup', () => drag = false);
window.addEventListener('mousemove', e => {
  if (!drag) return;
  theta -= (e.clientX - px) * 0.007;
  phi = Math.min(1.3, Math.max(0.06, phi + (e.clientY - py) * 0.005));
  px = e.clientX; py = e.clientY;
});
renderer.domElement.addEventListener('wheel', e => {
  e.preventDefault();
  radius = Math.min(R0 * 2.8, Math.max(5, radius + e.deltaY * 0.035));
}, { passive: false });

// Dokunmatik destek
let touch0 = null;
renderer.domElement.addEventListener('touchstart', e => {
  if (e.touches.length === 1) { drag = true; autoRot = false; touch0 = e.touches[0]; }
});
renderer.domElement.addEventListener('touchend', () => drag = false);
renderer.domElement.addEventListener('touchmove', e => {
  if (!drag || !touch0) return;
  const t = e.touches[0];
  theta -= (t.clientX - touch0.clientX) * 0.007;
  phi = Math.min(1.3, Math.max(0.06, phi + (t.clientY - touch0.clientY) * 0.005));
  touch0 = t;
});

/* ── Sinematik post-process (bloom) ──────────────────────── */
// Pencereler, LED'ler ve enerji akışı hafifçe parlasın.
// Renk yönetimi: RenderPass+Bloom lineer uzayda çalışır, GammaCorrection ile sRGB'ye çevrilir.
let composer = null;
if (USE_BLOOM) {
  try {
    composer = new THREE.EffectComposer(renderer);
    composer.addPass(new THREE.RenderPass(scene, camera));
    // Gündüz strength düşük (0.25) → parlak sıva/gökyüzü blooming yapıp sahneyi
    // sütlü göstermesin; gece güçlü (~0.8) → pencere/LED/enerji akışı parlasın.
    const bloomStrength = 0.25 + 0.55 * (1 - dayF);
    const bloom = new THREE.UnrealBloomPass(
      new THREE.Vector2(W, H),
      bloomStrength,  // strength
      0.5,            // radius
      0.85            // threshold — yalnızca gerçek emissive'ler parlar (sıva/gök değil)
    );
    composer.addPass(bloom);
    composer.addPass(new THREE.ShaderPass(THREE.GammaCorrectionShader)); // lineer → sRGB
  } catch (e) { composer = null; console.warn('Bloom kurulamadı, düz render kullanılıyor:', e); }
}

/* ── Animasyon döngüsü ───────────────────────────────────── */
let t0 = 0;
function animate(ts) {
  requestAnimationFrame(animate);
  const dt = Math.min((ts - t0) / 1000, 0.1); t0 = ts;

  // Otomatik yavaş döndürme — daha sinematik
  if (autoRot) theta += 0.045 * dt;

  // Asansör
  if (cab) {
    const span = baseH + bHeight - 1.6;
    cab.position.y = baseH + 0.6 + span * (0.5 + 0.5 * Math.sin(ts / 3200));
  }

  // Kesinti ışığı titremesi
  if (alarmLight) alarmLight.intensity = 1.5 + Math.sin(ts / 120) * 1.2;

  // Enerji akışı nabzı — kablo/batarya/panel emissive'i Math.sin ile solup parlar
  const tsec = ts / 1000;
  for (let i = 0; i < energyFX.length; i++) {
    const fx = energyFX[i];
    fx.mat.emissiveIntensity = fx.base + fx.amp * (0.5 + 0.5 * Math.sin(tsec * fx.speed + fx.phase));
  }

  // Enerji akış partikülleri — from → to arası lerp, t döngüsel
  for (const p of flowParticles) {
    p.t = (p.t + p.spd * dt) % 1.0;
    // Ease-in-out: parabolik yay (parabolic arc) — gerçekçi hareket
    const tEased = p.t < 0.5 ? 2 * p.t * p.t : 1 - Math.pow(-2 * p.t + 2, 2) / 2;
    p.mesh.position.lerpVectors(p.from, p.to, tEased);
    // Yay — ortada biraz yukarı kalk (arc efekti)
    p.mesh.position.y += Math.sin(p.t * Math.PI) * 1.8;
    p.mesh.visible = true;
    // Tail fade — başta ve sonda şeffaf
    const fade = Math.sin(p.t * Math.PI);
    p.mesh.material.opacity = 0.25 + 0.75 * fade;
    const s = 0.6 + 0.6 * fade;
    p.mesh.scale.setScalar(s);
  }

  // Highlight halkası animasyonu — döndür + pulse
  if (_hlGroup) {
    _hlGroup.rotation.y += dt * 0.9;
    if (_hlRingMat) _hlRingMat.opacity = 0.55 + 0.45 * Math.sin(tsec * 2.5);
    if (_hlGlow) _hlGlow.intensity = 1.5 + 1.0 * Math.sin(tsec * 3.0);
  }

  updateCam();
  if (composer) composer.render(); else renderer.render(scene, camera);
}

updateCam();
requestAnimationFrame(animate);

// Pencere/iframe boyutu değişince — canvas'ı yeniden boyutlandır
function onResize() {
  const nW = wrap.clientWidth  || window.innerWidth  || 640;
  const nH = wrap.clientHeight || window.innerHeight || __H__;
  if (nW < 10 || nH < 10) return;
  renderer.setSize(nW, nH);
  camera.aspect = nW / nH;
  camera.updateProjectionMatrix();
  if (composer) composer.setSize(nW, nH);
}
window.addEventListener('resize', onResize);
// İframe layout sonrası ilk düzeltme (srcdoc gecikmeli render)
setTimeout(onResize, 50);
setTimeout(onResize, 300);

/* ── Highlight sistemi — postMessage API ─────────────────────
   Simulasyon.jsx → Building.jsx → iframe.contentWindow.postMessage
   { type: 'HIGHLIGHT', system: 'hvac' | 'battery' | null }
   Seçili sistem üzerine mavi pulsing halkası + nokta ışık eklenir.
──────────────────────────────────────────────────────────────── */
const SYS_POS = {
  solar_pv:      { x: 0,               y: roofY + 0.5,   z: 0 },
  battery:       { x: bWidth / 2 + 1,  y: bHeight * 0.5, z: 0 },
  hvac:          { x: bWidth * 0.38,   y: roofY + 0.7,   z: B_DEPTH * 0.36 },
  su_pompasi:    { x: -bWidth * 0.3,   y: roofY + 1.1,   z: -B_DEPTH * 0.25 },
  gunes_isitici: { x: bWidth * 0.2,    y: roofY + 0.5,   z: -B_DEPTH * 0.35 },
  jenerator:     { x: -bWidth / 2 - 0.8, y: 0.6,         z: -B_DEPTH * 0.3 },
  asansor:       { x: 0,               y: bHeight * 0.55, z: 0 },
  ev_sarj:       { x: bWidth / 2 + 1.5, y: 0.35,         z: 0.5 },
  kamera:        { x: bWidth / 2,      y: bHeight * 0.8,  z: B_DEPTH / 2 },
};

let _hlGroup = null;
let _hlRingMat = null;
let _hlGlow = null;

function clearHighlight() {
  if (_hlGroup) { scene.remove(_hlGroup); _hlGroup = null; _hlRingMat = null; _hlGlow = null; }
}

function setHighlight(sysId) {
  clearHighlight();
  const pos = SYS_POS[sysId];
  if (!pos) return;

  const g = new THREE.Group();

  // Outer pulsing ring
  const ringGeo = new THREE.TorusGeometry(1.4, 0.07, 10, 56);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x60a5fa, transparent: true, opacity: 0.9 });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = Math.PI / 2;
  g.add(ring);
  _hlRingMat = ringMat;

  // Inner smaller ring (stacked)
  const ring2Geo = new THREE.TorusGeometry(0.9, 0.04, 8, 48);
  const ring2Mat = new THREE.MeshBasicMaterial({ color: 0x93c5fd, transparent: true, opacity: 0.6 });
  const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
  ring2.rotation.x = Math.PI / 2;
  g.add(ring2);

  // Glow point light
  const glow = new THREE.PointLight(0x60a5fa, 2.0, 5);
  g.add(glow);
  _hlGlow = glow;

  g.position.set(pos.x, pos.y, pos.z);
  scene.add(g);
  _hlGroup = g;
}


window.addEventListener('message', (e) => {
  try {
    const d = e.data;
    if (!d || d.type !== 'HIGHLIGHT') return;
    if (d.system) setHighlight(d.system);
    else clearHighlight();
  } catch(_) {}
});
})();
</script>
"""


_T = {
    "tr": {
        "grid_outage": "ŞEBEKE KESİNTİSİ",
        "connected": "BAĞLI", "outage_status": "KESİNTİ",
        "grid_status": "Şebeke Durumu", "battery": "Batarya (SOC)",
        "solar": "Güneş Üretim", "active": "Aktif",
        "capacity": "kapasite", "occupancy": "doluluk",
        "simulation": "SİMÜLASYON",
        "charging": "ŞARJ", "discharging": "DEŞARJ", "standby": "BEKLEMEDE",
        "morning": "SABAH", "daytime": "GÜNDÜZ", "evening": "AKŞAM", "night": "GECE",
        "rl_agent": "RL Ajan: TD3/SAC",
    },
    "en": {
        "grid_outage": "GRID OUTAGE",
        "connected": "CONNECTED", "outage_status": "OUTAGE",
        "grid_status": "Grid Status", "battery": "Battery (SOC)",
        "solar": "Solar Output", "active": "Active",
        "capacity": "capacity", "occupancy": "occupancy",
        "simulation": "SIMULATION",
        "charging": "CHARGING", "discharging": "DISCHARGING", "standby": "STANDBY",
        "morning": "MORNING", "daytime": "DAYTIME", "evening": "EVENING", "night": "NIGHT",
        "rl_agent": "RL Agent: TD3/SAC",
    },
    "ar": {
        "grid_outage": "انقطاع الشبكة",
        "connected": "متصل", "outage_status": "انقطاع",
        "grid_status": "حالة الشبكة", "battery": "البطارية",
        "solar": "الطاقة الشمسية", "active": "نشط",
        "capacity": "سعة", "occupancy": "إشغال",
        "simulation": "محاكاة",
        "charging": "شحن", "discharging": "تفريغ", "standby": "انتظار",
        "morning": "صباح", "daytime": "نهار", "evening": "مساء", "night": "ليل",
        "rl_agent": "وكيل RL: TD3/SAC",
    },
}


def building_html(cfg: BinaConfig, hour: int, soc: float,
                  solar_kw: float, outage: bool = False, height: int = 520,
                  unit_label: str = "daire", dil: str = "tr",
                  assets: dict | None = None, bloom: bool = True,
                  month: int = 7) -> str:
    """assets: {'hdri': url, 'car': url, 'tree': url, 'lamp': url} — verilen .glb / .hdr
    adresleri ilgili ilkel geometrilerin yerine yüklenir. Boş bırakılırsa mevcut
    prosedürel geometri (fallback) kullanılır; hiçbir şey bozulmaz.
    bloom: sinematik parlama efekti. VARSAYILAN KAPALI — r128 renk yönetimi hassas
    olduğu için açınca renkleri kontrol et; soluk/karanlık olursa kapalı bırak.
    NOT: Streamlit iframe'i srcdoc ile çalışır → model/HDRI adresleri MUTLAK ve
    CORS-açık olmalı (yerel dosya yolu çalışmaz)."""
    solar_max = max(cfg.panel_kw * 0.80, 0.1)
    labels = _T.get(dil, _T["tr"])
    params = dict(
        assets=dict(assets or {}),
        bloom=bool(bloom),
        unit_label=str(unit_label),
        t=labels,
        floors=int(cfg.kat),
        units_per_floor=int(cfg.daire_per_kat),
        active_units=int(min(cfg.aktif_daire, cfg.toplam_daire)),
        total_units=int(cfg.toplam_daire),
        panels=int(cfg.panel_sayisi),
        hour=int(hour),
        month=int(month),   # 1=Jan…12=Dec — season-aware sun position
        soc=float(round(soc, 3)),
        solar_kw=float(round(solar_kw, 2)),
        solar_norm=float(round(min(solar_kw / solar_max, 1.0), 3)),
        elevator=bool(cfg.asansor),
        ev=bool(cfg.ev_sarj),
        hvac=bool(cfg.hvac),
        su_pompasi=bool(cfg.su_pompasi),
        kamera=bool(cfg.kamera),
        gunes_isitici=bool(cfg.gunes_isitici),
        jenerator=bool(cfg.jenerator),
        outage=bool(outage),
    )
    return _TEMPLATE.replace("__CFG__", json.dumps(params)).replace("__H__", str(height))
