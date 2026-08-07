"""Three.js 3D bina görselleştirmesi — gerçekçi, profesyonel, döndür/zoom."""

from __future__ import annotations
import json
from .config import BinaConfig

_TEMPLATE = r"""
<div id="wrap" style="width:100%;height:__H__px;position:relative;border-radius:12px;overflow:hidden;">
<div id="hud" style="
  position:absolute;top:12px;left:14px;z-index:9;
  display:flex;gap:10px;flex-wrap:wrap;font-family:'Inter',system-ui,sans-serif;font-size:13px;">
</div>
<div id="alarm" style="display:none;position:absolute;top:12px;right:14px;z-index:9;
  background:#dc2626;color:#fff;font-weight:700;font-size:13px;
  padding:6px 14px;border-radius:8px;font-family:system-ui;">⚠ KESİNTİ</div>
<style>
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
  @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
  .hud-chip{
    background:rgba(10,12,20,.72);backdrop-filter:blur(6px);
    color:#f1f5f9;padding:5px 12px;border-radius:20px;
    border:1px solid rgba(255,255,255,.12);white-space:nowrap;
  }
</style>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
const CFG = __CFG__;
const wrap = document.getElementById('wrap');
const W = wrap.clientWidth || 640, H = wrap.clientHeight || __H__;

/* ── Renderer ─────────────────────────────────────────────── */
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:false});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
wrap.appendChild(renderer.domElement);

/* ── Scene ────────────────────────────────────────────────── */
const scene = new THREE.Scene();

/* ── Zaman & gökyüzü ─────────────────────────────────────── */
const hour = CFG.hour;
// Gün faktörü: 0=gece tam, 1=öğlen tam
const dayF = Math.max(0, Math.min(1,
  hour >= 6 && hour <= 20
    ? Math.sin((hour - 6) / 14 * Math.PI)
    : 0
));
const isSunrise = hour >= 5 && hour < 8;
const isSunset  = hour >= 18 && hour < 21;
const isGolden  = isSunrise || isSunset;

// Gökyüzü rengi
function skyColor() {
  if (hour < 5 || hour >= 22) return new THREE.Color(0x01060f); // derin gece
  if (hour < 6)  return new THREE.Color(0x040d1e); // gece sonu
  if (hour < 7)  return new THREE.Color(0xc45c1e); // şafak
  if (hour < 8)  return new THREE.Color(0xe8955a); // sabah altını
  if (hour < 10) return new THREE.Color(0x6fb8e8); // sabah
  if (hour < 17) return new THREE.Color(0x4a9fd4); // gündüz
  if (hour < 18) return new THREE.Color(0x6ab0d8); // öğleden sonra
  if (hour < 19) return new THREE.Color(0xe07030); // gün batımı
  if (hour < 20) return new THREE.Color(0x8a2a10); // alaca karanlık
  if (hour < 21) return new THREE.Color(0x1a0a20); // akşam
  return new THREE.Color(0x02060e); // gece
}
const sky = skyColor();
scene.background = sky;
scene.fog = new THREE.FogExp2(sky, 0.008);

/* ── Işıklandırma ────────────────────────────────────────── */
// Hemisphere: gökyüzü rengi yukarıdan, toprak yeşili aşağıdan
const hemi = new THREE.HemisphereLight(
  sky, new THREE.Color(0x2d4a1e), 0.5 + 0.4 * dayF
);
scene.add(hemi);

// Güneş konumu: saat 6→doğu, 12→tepe, 18→batı
const sunAngle = ((hour - 6) / 12) * Math.PI;
const sunDist = 80;
const sunX = Math.cos(sunAngle) * sunDist;
const sunY = Math.max(2, Math.sin(sunAngle) * sunDist);
const sunZ = -30;

const sunLight = new THREE.DirectionalLight(
  isGolden ? 0xffb347 : 0xfff6e0,
  dayF > 0.05 ? (isGolden ? 1.4 : 1.2) : 0
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

// Arka ambient fill
scene.add(new THREE.AmbientLight(0xffffff, 0.15 + 0.2 * dayF));

/* ── Güneş diski ─────────────────────────────────────────── */
if (dayF > 0.05) {
  const sunGeo = new THREE.SphereGeometry(2.8, 24, 24);
  const sunMat = new THREE.MeshBasicMaterial({
    color: isGolden ? 0xff8c30 : 0xfff5a0
  });
  const sunMesh = new THREE.Mesh(sunGeo, sunMat);
  sunMesh.position.set(sunX * 0.7, sunY * 0.7, sunZ * 0.7);
  scene.add(sunMesh);

  // Hale (glow) — büyük transparan küre
  const glowMat = new THREE.MeshBasicMaterial({
    color: isGolden ? 0xff6010 : 0xffee88,
    transparent: true, opacity: 0.12, side: THREE.BackSide
  });
  const glow = new THREE.Mesh(new THREE.SphereGeometry(7, 16, 16), glowMat);
  glow.position.copy(sunMesh.position);
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
const grassMat = new THREE.MeshStandardMaterial({
  color: dayF > 0.5 ? 0x4a7c3f : 0x1a3010,
  roughness: 0.9
});
const grass = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), grassMat);
grass.rotation.x = -Math.PI / 2;
grass.receiveShadow = true;
scene.add(grass);

// Beton kaldırım
const sidewalkMat = new THREE.MeshStandardMaterial({color: 0xb8bfc9, roughness: 0.8});
const sidewalk = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), sidewalkMat);
sidewalk.rotation.x = -Math.PI / 2;
sidewalk.position.set(0, 0.01, 5);
sidewalk.receiveShadow = true;
scene.add(sidewalk);

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

// Ana duvar rengi
const wallColor = dayF > 0.4 ? 0xd4cfc9 : 0x6a6560;
const wallMat   = concreteMat(wallColor);

// Temel
const baseH = 0.6;
const base = new THREE.Mesh(
  new THREE.BoxGeometry(bWidth + 0.6, baseH, B_DEPTH + 0.6),
  concreteMat(0x8a8680)
);
base.position.y = baseH / 2;
base.castShadow = true;
base.receiveShadow = true;
group.add(base);

// Her kat
for (let f = 0; f < CFG.floors; f++) {
  const yBase = baseH + f * FLOOR_H;

  // Döşeme levhası
  const slab = new THREE.Mesh(
    new THREE.BoxGeometry(bWidth + 0.3, FLOOR_T, B_DEPTH + 0.3),
    concreteMat(0x9a9590)
  );
  slab.position.y = yBase;
  slab.castShadow = true;
  slab.receiveShadow = true;
  group.add(slab);

  // Duvar: ön ve arka panel (pencereler arasındaki solid kısımlar)
  for (const zSign of [1, -1]) {
    const wallZ = zSign * (B_DEPTH / 2 + 0.01);
    // Sol stütün (solid)
    const colW = 0.35;
    const wallH = FLOOR_H - FLOOR_T - 0.1;

    // Kolonlar (pencereler arası dikey duvar)
    for (let u = 0; u <= CFG.units_per_floor; u++) {
      const colX = -bWidth / 2 + u * UNIT_W;
      const col = new THREE.Mesh(
        new THREE.BoxGeometry(colW, wallH, 0.28),
        wallMat
      );
      col.position.set(colX, yBase + FLOOR_T + wallH / 2, wallZ);
      group.add(col);
    }

    // Üst kiriş (pencere üstü)
    const beam = new THREE.Mesh(
      new THREE.BoxGeometry(bWidth, 0.55, 0.28),
      wallMat
    );
    beam.position.set(0, yBase + FLOOR_H - 0.3, wallZ);
    group.add(beam);

    // Alt parapet / windowsill
    const sill = new THREE.Mesh(
      new THREE.BoxGeometry(bWidth, 0.28, 0.32),
      concreteMat(0xb8b4ae)
    );
    sill.position.set(0, yBase + FLOOR_T + 0.28, wallZ);
    group.add(sill);
  }

  // Yan duvarlar
  for (const xSign of [1, -1]) {
    const wall = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, FLOOR_H - FLOOR_T, B_DEPTH),
      wallMat
    );
    wall.position.set(xSign * (bWidth / 2 + 0.15), yBase + FLOOR_T + (FLOOR_H - FLOOR_T) / 2, 0);
    wall.castShadow = true;
    group.add(wall);
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

    // Cam rengi
    let glassColor, emissiveColor, emissiveInt = 0;
    if (CFG.outage) {
      glassColor = isActive && isLit && unitGlobal === 0 ? 0xfbbf24 : 0x0a0a0a;
    } else if (isLit) {
      glassColor = 0xfef3c7;
      emissiveColor = new THREE.Color(0xfcd34d);
      emissiveInt = 0.4;
    } else if (dayF > 0.5) {
      // gündüz yansıma
      glassColor = 0x8ec8e8;
    } else {
      glassColor = 0x0d1520;
    }

    const glassMat = new THREE.MeshStandardMaterial({
      color: glassColor,
      emissive: emissiveColor || new THREE.Color(0x000000),
      emissiveIntensity: emissiveInt,
      roughness: 0.05,
      metalness: 0.15,
      transparent: true,
      opacity: 0.88
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

      // Pencere çerçevesi
      const frameMat = metalMat(0x6b7280);
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
// Çatı döşemesi
const roofSlab = new THREE.Mesh(
  new THREE.BoxGeometry(bWidth + 0.4, 0.3, B_DEPTH + 0.4),
  concreteMat(0x8a8680)
);
roofSlab.position.y = roofY + 0.15;
group.add(roofSlab);

// Parapet (çatı kenar duvarı)
for (const [axis, sign] of [['x',1],['x',-1],['z',1],['z',-1]]) {
  const isX = axis === 'x';
  const par = new THREE.Mesh(
    new THREE.BoxGeometry(
      isX ? 0.25 : bWidth + 0.5,
      0.7,
      isX ? B_DEPTH + 0.5 : 0.25
    ),
    concreteMat(0x9a9590)
  );
  par.position.set(
    isX ? sign * (bWidth / 2 + 0.12) : 0,
    roofY + 0.65,
    isX ? 0 : sign * (B_DEPTH / 2 + 0.12)
  );
  group.add(par);
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
const battFill = new THREE.Mesh(
  new THREE.BoxGeometry(battW - 0.22, fillH, 0.06),
  new THREE.MeshStandardMaterial({
    color: fillCol,
    emissive: fillCol,
    emissiveIntensity: 0.35,
    roughness: 0.5
  })
);
battFill.position.set(battX, battY0 + 0.15 + fillH / 2, 1.0 + battD / 2 + 0.04);
group.add(battFill);

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
  group.add(car);

  // Şarj kablosu
  const chargeCable = new THREE.Mesh(
    new THREE.CylinderGeometry(0.03, 0.03, 1.8, 6),
    metalMat(0x065f46)
  );
  chargeCable.rotation.z = Math.PI / 3;
  chargeCable.position.set(evX - 0.8, 0.8, evZ);
  group.add(chargeCable);

  if (evCharging) {
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

/* ── Ağaçlar ─────────────────────────────────────────────── */
function tree(x, z, h) {
  const g = new THREE.Group();
  const trunkH = h * 0.38;
  // Gövde
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.14, 0.2, trunkH, 8),
    new THREE.MeshStandardMaterial({color: 0x5c3d1e, roughness: 0.9})
  );
  trunk.position.y = trunkH / 2;
  g.add(trunk);

  // Yaprak katmanları
  const leafColor = dayF > 0.3 ? 0x2d7a2d : 0x1a4a1a;
  for (let i = 0; i < 3; i++) {
    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(0.7 - i * 0.15, h * 0.35, 8),
      new THREE.MeshStandardMaterial({color: leafColor, roughness: 0.8})
    );
    cone.position.y = trunkH + i * h * 0.22;
    g.add(cone);
  }
  g.position.set(x, 0, z);
  g.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });
  return g;
}

group.add(tree(-bWidth / 2 - 4,  2.5, 4.5));
group.add(tree(-bWidth / 2 - 4, -3.0, 5.5));
group.add(tree( bWidth / 2 + battW + 5.5, 3.0, 4.0));
group.add(tree( bWidth / 2 + battW + 5.5, -2.5, 5.0));
group.add(tree(-bWidth / 2 - 7,  0.0, 6.0));

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
  document.getElementById('alarm').style.display = 'block';
  document.getElementById('alarm').style.animation = 'blink 0.7s infinite';

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

/* ── HUD ─────────────────────────────────────────────────── */
const hud = document.getElementById('hud');
const socPct = Math.round(soc * 100);
const socColor = soc > 0.5 ? '#22c55e' : soc > 0.2 ? '#f59e0b' : '#ef4444';
hud.innerHTML = [
  `<span class="hud-chip">🕐 ${String(hour).padStart(2,'0')}:00</span>`,
  `<span class="hud-chip">🔋 <span style="color:${socColor};font-weight:700">%${socPct}</span></span>`,
  `<span class="hud-chip">☀️ ${CFG.solar_kw.toFixed(1)} kW</span>`,
  `<span class="hud-chip">🏠 ${CFG.active_units}/${CFG.total_units} daire</span>`,
].join('');

/* ── Kamera ──────────────────────────────────────────────── */
const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 500);
const lookAt = new THREE.Vector3(0, (baseH + bHeight) * 0.45, 0);
const R0 = Math.max(bHeight * 2.1, bWidth * 2.4, 16);
let theta = 0.72, phi = 0.38, radius = R0, autoRot = true;

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

/* ── Animasyon döngüsü ───────────────────────────────────── */
let t0 = 0;
function animate(ts) {
  requestAnimationFrame(animate);
  const dt = Math.min((ts - t0) / 1000, 0.1); t0 = ts;

  // Otomatik yavaş döndürme
  if (autoRot) theta += 0.08 * dt;

  // Asansör
  if (cab) {
    const span = baseH + bHeight - 1.6;
    cab.position.y = baseH + 0.6 + span * (0.5 + 0.5 * Math.sin(ts / 3200));
  }

  // Kesinti ışığı titremesi
  if (alarmLight) alarmLight.intensity = 1.5 + Math.sin(ts / 120) * 1.2;

  updateCam();
  renderer.render(scene, camera);
}

updateCam();
requestAnimationFrame(animate);

// Pencere boyutu değişince
window.addEventListener('resize', () => {
  const nW = wrap.clientWidth, nH = wrap.clientHeight;
  camera.aspect = nW / nH;
  camera.updateProjectionMatrix();
  renderer.setSize(nW, nH);
});
})();
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
        hvac=bool(cfg.hvac),
        su_pompasi=bool(cfg.su_pompasi),
        kamera=bool(cfg.kamera),
        gunes_isitici=bool(cfg.gunes_isitici),
        jenerator=bool(cfg.jenerator),
        outage=bool(outage),
    )
    return _TEMPLATE.replace("__CFG__", json.dumps(params)).replace("__H__", str(height))
