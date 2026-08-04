import { AnimatePresence, motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import {
  Arrow, Battery, Bolt, Brain, Chart, Check, Chevron,
  Coins, Cube, Gauge, Home, Shield, Star, Sun, X,
} from "./icons.jsx";

const fadeUp = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-70px" },
  transition: { duration: 0.55, ease: "easeOut" },
};

/* ── Nav ─────────────────────────────────────────────────────── */
function Nav() {
  return (
    <div className="nav">
      <div style={{ padding: "0 14px" }}>
        <motion.div className="nav-pill" initial={{ y: -70, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          <a href="#top" className="logo">
            <span className="logo-mark"><Bolt size={17} /></span> SmartHome Energy RL
          </a>
          <nav className="nav-links" aria-label="Ana menü">
            <a href="#features">Özellikler</a>
            <a href="#how">Nasıl Çalışır</a>
            <a href="#stats">Sonuçlar</a>
            <a href="#faq">SSS</a>
          </nav>
          <a className="btn btn-blue" href="http://localhost:8501" style={{ padding: "11px 20px" }}>
            Dashboard'u Aç <span className="arr"><Arrow size={14} /></span>
          </a>
        </motion.div>
      </div>
    </div>
  );
}

/* ── Mockup: gerçekçi BMS dashboard önizlemesi ───────────────── */
function Mockup() {
  const navItems = [
    { label: "Bina Simülasyonu", icon: "🏠", active: true },
    { label: "Canlı EPİAŞ", icon: "⚡", active: false },
    { label: "Yatırım & Çevre", icon: "💰", active: false },
    { label: "Uzman Modu", icon: "📊", active: false },
  ];

  const prices = [2100,1900,1750,1680,1820,2400,3200,3800,3500,3100,2900,2700,
                  2500,2300,2600,3100,3600,4100,3900,3400,2800,2400,2200,2000];
  const soc =    [0.50,0.55,0.62,0.71,0.78,0.82,0.79,0.74,0.70,0.66,0.62,0.58,
                  0.55,0.52,0.50,0.49,0.48,0.40,0.34,0.28,0.36,0.44,0.50,0.52];
  const solar =  [0,0,0,0,0,0.2,1.8,5.4,9.2,13.1,15.8,16.2,15.4,13.8,10.6,6.9,3.2,0.8,0,0,0,0,0,0];
  const W = 560; const H = 90;
  const maxP = 4100;
  const pPoints = prices.map((p,i) => `${(i/23)*W},${H-(p/maxP)*H}`).join(" ");
  const sPoints = soc.map((s,i) => `${(i/23)*W},${H-s*H}`).join(" ");
  const charges  = [3,4,5];
  const discharges = [17,18,19];

  /* mini 3D bina SVG */
  const Building = () => (
    <svg viewBox="0 0 120 130" width="90" height="98" aria-label="3D bina önizlemesi">
      {/* zemin */}
      <ellipse cx="60" cy="118" rx="48" ry="8" fill="#e2e8f0"/>
      {/* arka yüz */}
      <rect x="18" y="30" width="60" height="80" rx="2" fill="#94a3b8"/>
      {/* yan yüz */}
      <polygon points="78,30 102,18 102,98 78,110" fill="#64748b"/>
      {/* ön yüz */}
      <rect x="18" y="30" width="60" height="80" rx="2" fill="#cbd5e1"/>
      {/* çatı */}
      <polygon points="18,30 78,30 102,18 42,18" fill="#e2e8f0"/>
      {/* pencereler — ön */}
      {[[26,42],[42,42],[58,42],[26,58],[42,58],[58,58],[26,74],[42,74],[58,74]].map(([x,y],i) => (
        <rect key={i} x={x} y={y} width="10" height="8" rx="1"
          fill={i % 3 === 0 ? "#fef08a" : "#bfdbfe"} opacity="0.9"/>
      ))}
      {/* güneş paneli — çatı */}
      <rect x="46" y="20" width="22" height="10" rx="1" fill="#3b82f6" opacity="0.8"/>
      <line x1="57" y1="20" x2="57" y2="30" stroke="#1d4ed8" strokeWidth="0.8"/>
      <line x1="46" y1="25" x2="68" y2="25" stroke="#1d4ed8" strokeWidth="0.8"/>
      {/* batarya — yan */}
      <rect x="83" y="72" width="12" height="22" rx="2" fill="#22c55e" opacity="0.85"/>
      <rect x="83" y="72" width="12" height="7" rx="1" fill="#86efac" opacity="0.6"/>
      <rect x="87" y="70" width="4" height="3" rx="1" fill="#16a34a"/>
    </svg>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 60 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4, duration: 0.75 }}
      style={{
        background: "#fff", borderRadius: 20,
        boxShadow: "0 40px 80px -24px #00000040, 0 0 0 1px #e2e8f0",
        overflow: "hidden", display: "flex",
        maxWidth: 980, margin: "0 auto", textAlign: "left",
      }}>

      {/* ── Sol sidebar ──────────────────────────────── */}
      <div style={{
        background: "#0f172a", width: 200, flexShrink: 0,
        padding: "20px 14px", display: "flex", flexDirection: "column", gap: 4,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 8px 18px", borderBottom: "1px solid #1e293b" }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "#22c55e", display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Bolt size={14} style={{ color: "#fff" }} />
          </div>
          <span style={{ color: "#f8fafc", fontWeight: 800, fontSize: 13 }}>SmartHome BMS</span>
        </div>

        {navItems.map(({ label, icon, active }) => (
          <div key={label} style={{
            display: "flex", alignItems: "center", gap: 9,
            padding: "8px 10px", borderRadius: 8, fontSize: 12.5,
            background: active ? "#1e293b" : "transparent",
            color: active ? "#f8fafc" : "#94a3b8",
            cursor: "pointer",
          }}>
            <span style={{ fontSize: 14 }}>{icon}</span>
            {label}
          </div>
        ))}

        <div style={{ marginTop: "auto", borderTop: "1px solid #1e293b", paddingTop: 12 }}>
          <div style={{ fontSize: 11, color: "#475569", marginBottom: 6, padding: "0 10px" }}>Bina Konfigürasyonu</div>
          {[["Bina tipi", "Apartman"], ["Kat", "5"], ["Aktif daire", "12 / 15"], ["Batarya", "24.4 kWh"]].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 10px", fontSize: 11, color: "#64748b" }}>
              <span>{k}</span><span style={{ color: "#94a3b8", fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Ana içerik ───────────────────────────────── */}
      <div style={{ flex: 1, padding: "20px 22px", background: "#f8fafc", overflow: "hidden" }}>
        {/* Başlık satırı */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, color: "#0f172a" }}>Bina Simülasyonu</div>
            <div style={{ fontSize: 11.5, color: "#64748b" }}>SAC ajanı aktif · 5 kat · 12 daire · veri: Sentetik EPİAŞ</div>
          </div>
          <div style={{
            background: "#dcfce7", color: "#15803d", borderRadius: 999,
            padding: "4px 12px", fontSize: 11.5, fontWeight: 700,
          }}>🤖 SAC ajan aktif</div>
        </div>

        {/* Metrik kartlar */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, margin: "14px 0" }}>
          {[
            ["💰 Bugünkü tasarruf", "+312 TL", "#15803d", "#dcfce7"],
            ["🔋 Batarya SOC", "%68", "#1d4ed8", "#dbeafe"],
            ["☀️ Güneş üretimi", "18.4 kWh", "#b45309", "#fef3c7"],
            ["⚡ Şu an karar", "Deşarj ▼", "#b91c1c", "#fee2e2"],
          ].map(([label, val, fg, bg]) => (
            <div key={label} style={{ background: "#fff", borderRadius: 12, padding: "12px 14px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: 10.5, color: "#64748b", marginBottom: 4 }}>{label}</div>
              <div style={{ fontSize: 17, fontWeight: 800, color: fg }}>{val}</div>
            </div>
          ))}
        </div>

        {/* İki sütun: 3D + grafik */}
        <div style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: 14 }}>
          {/* Mini bina + batarya göstergesi */}
          <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "10px 8px", display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <Building />
            <div style={{ fontSize: 10, color: "#64748b", textAlign: "center" }}>Panel: 37 adet<br/>8.0 kW kurulu</div>
            <div style={{ width: "100%", height: 6, background: "#e2e8f0", borderRadius: 999 }}>
              <div style={{ width: "68%", height: "100%", background: "#22c55e", borderRadius: 999 }}/>
            </div>
            <div style={{ fontSize: 10, color: "#15803d", fontWeight: 700 }}>Batarya %68</div>
          </div>

          {/* Fiyat + SOC grafiği */}
          <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>EPİAŞ PTF & Batarya SOC — bugün</div>
              <div style={{ display: "flex", gap: 10, fontSize: 10 }}>
                <span style={{ color: "#f59e0b" }}>— Fiyat</span>
                <span style={{ color: "#22c55e" }}>— SOC</span>
                <span style={{ color: "#3b82f6" }}>▲ şarj</span>
                <span style={{ color: "#ef4444" }}>▼ deşarj</span>
              </div>
            </div>
            <svg viewBox={`0 0 ${W} ${H+10}`} style={{ width: "100%" }} role="img" aria-label="Fiyat ve SOC grafiği">
              {/* grid lines */}
              {[0.25,0.5,0.75].map(f => (
                <line key={f} x1="0" y1={H-f*H} x2={W} y2={H-f*H} stroke="#f1f5f9" strokeWidth="1"/>
              ))}
              {/* fiyat alanı */}
              <polyline fill="none" stroke="#f59e0b" strokeWidth="2" points={pPoints}/>
              {/* SOC çizgisi */}
              <polyline fill="none" stroke="#22c55e" strokeWidth="2" strokeDasharray="4 2" points={sPoints}/>
              {/* şarj kararları */}
              {charges.map(i => (
                <polygon key={i}
                  points={`${(i/23)*W},${H-(prices[i]/maxP)*H-12} ${(i/23)*W-5},${H-(prices[i]/maxP)*H} ${(i/23)*W+5},${H-(prices[i]/maxP)*H}`}
                  fill="#3b82f6"/>
              ))}
              {/* deşarj kararları */}
              {discharges.map(i => (
                <polygon key={i}
                  points={`${(i/23)*W},${H-(prices[i]/maxP)*H+12} ${(i/23)*W-5},${H-(prices[i]/maxP)*H} ${(i/23)*W+5},${H-(prices[i]/maxP)*H}`}
                  fill="#ef4444"/>
              ))}
              {/* şu anki saat çizgisi (saat 14) */}
              <line x1={(14/23)*W} y1="0" x2={(14/23)*W} y2={H} stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 2"/>
              {/* saat etiketleri */}
              {[0,6,12,18,23].map(h => (
                <text key={h} x={(h/23)*W} y={H+10} textAnchor="middle" fontSize="9" fill="#94a3b8">{h}:00</text>
              ))}
            </svg>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Hero ────────────────────────────────────────────────────── */
/* ── Parallax 3D Hero ─────────────────────────────────────────── */
function HeroScene() {
  const skyRef   = useRef(null);
  const cloud1Ref = useRef(null);
  const cloud2Ref = useRef(null);
  const sunRef   = useRef(null);
  const cityRef  = useRef(null);
  const groundRef = useRef(null);
  const particleRef = useRef(null);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      if (skyRef.current)    skyRef.current.style.transform    = `translateY(${y * 0.18}px)`;
      if (sunRef.current)    sunRef.current.style.transform    = `translateY(${y * 0.22}px)`;
      if (cloud1Ref.current) cloud1Ref.current.style.transform = `translateY(${y * 0.30}px) translateX(${y * 0.04}px)`;
      if (cloud2Ref.current) cloud2Ref.current.style.transform = `translateY(${y * 0.24}px) translateX(${-y * 0.03}px)`;
      if (cityRef.current)   cityRef.current.style.transform   = `translateY(${y * 0.42}px)`;
      if (groundRef.current) groundRef.current.style.transform = `translateY(${y * 0.55}px)`;
      if (particleRef.current) particleRef.current.style.transform = `translateY(${y * 0.35}px)`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", zIndex: 0, pointerEvents: "none" }}>
      {/* Gökyüzü gradyan */}
      <div ref={skyRef} style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(180deg, #bae6fd 0%, #e0f2fe 40%, #f0fdf4 75%, #dcfce7 100%)",
        willChange: "transform",
      }} />

      {/* Güneş */}
      <div ref={sunRef} style={{ position: "absolute", top: "8%", right: "14%", willChange: "transform" }}>
        <div style={{ position: "relative", width: 110, height: 110 }}>
          {/* ışın halkası */}
          <div style={{
            position: "absolute", inset: -18,
            borderRadius: "50%",
            background: "radial-gradient(circle, #fde04788 0%, transparent 70%)",
            animation: "sunPulse 3s ease-in-out infinite",
          }}/>
          {/* güneş diski */}
          <div style={{
            position: "absolute", inset: 0, borderRadius: "50%",
            background: "radial-gradient(circle at 35% 35%, #fef08a, #fbbf24)",
            boxShadow: "0 0 60px 20px #fde04755, 0 0 120px 50px #fbbf2422",
          }}/>
          {/* güneş ışınları */}
          {[0,30,60,90,120,150,180,210,240,270,300,330].map(a => (
            <div key={a} style={{
              position: "absolute", top: "50%", left: "50%", width: 3, height: 22,
              background: "linear-gradient(#fbbf24, transparent)",
              transformOrigin: "50% 0",
              transform: `rotate(${a}deg) translateX(-50%) translateY(-${55 + 22}px)`,
              borderRadius: 2, opacity: 0.7,
            }}/>
          ))}
        </div>
      </div>

      {/* Uzak bulutlar */}
      <div ref={cloud1Ref} style={{ position: "absolute", top: "12%", left: "6%", willChange: "transform", opacity: 0.88 }}>
        <svg width="260" height="90" viewBox="0 0 260 90">
          <ellipse cx="90" cy="60" rx="88" ry="30" fill="white"/>
          <ellipse cx="60" cy="52" rx="52" ry="28" fill="white"/>
          <ellipse cx="130" cy="48" rx="46" ry="24" fill="white"/>
          <ellipse cx="180" cy="56" rx="62" ry="26" fill="white"/>
          <ellipse cx="210" cy="62" rx="48" ry="22" fill="white"/>
        </svg>
      </div>

      {/* Yakın bulutlar */}
      <div ref={cloud2Ref} style={{ position: "absolute", top: "18%", right: "4%", willChange: "transform", opacity: 0.75 }}>
        <svg width="200" height="70" viewBox="0 0 200 70">
          <ellipse cx="70" cy="46" rx="68" ry="24" fill="white"/>
          <ellipse cx="48" cy="38" rx="40" ry="22" fill="white"/>
          <ellipse cx="100" cy="34" rx="36" ry="20" fill="white"/>
          <ellipse cx="140" cy="44" rx="52" ry="22" fill="white"/>
        </svg>
      </div>

      {/* Enerji partikülleri */}
      <div ref={particleRef} style={{ position: "absolute", inset: 0, willChange: "transform" }}>
        {[
          { x:"18%", y:"32%", delay:0,   size:8,  color:"#22c55e" },
          { x:"72%", y:"28%", delay:0.6, size:6,  color:"#3b82f6" },
          { x:"45%", y:"22%", delay:1.1, size:10, color:"#f59e0b" },
          { x:"85%", y:"40%", delay:0.3, size:7,  color:"#22c55e" },
          { x:"10%", y:"55%", delay:1.4, size:5,  color:"#a78bfa" },
          { x:"60%", y:"48%", delay:0.8, size:9,  color:"#f59e0b" },
        ].map((p, i) => (
          <div key={i} style={{
            position: "absolute", left: p.x, top: p.y,
            width: p.size, height: p.size, borderRadius: "50%",
            background: p.color, opacity: 0.65,
            boxShadow: `0 0 ${p.size * 3}px ${p.color}`,
            animation: `floatPart ${2.8 + i * 0.4}s ease-in-out ${p.delay}s infinite alternate`,
          }}/>
        ))}
      </div>

      {/* Şehir silüeti — orta katman */}
      <div ref={cityRef} style={{ position: "absolute", bottom: "18%", left: 0, right: 0, willChange: "transform" }}>
        <svg viewBox="0 0 1440 280" style={{ width: "100%", display: "block" }} preserveAspectRatio="xMidYMax slice">
          {/* arka bina grubu (gri/mavi) */}
          <rect x="0"   y="160" width="60"  height="120" fill="#93c5fd" opacity="0.5"/>
          <rect x="50"  y="120" width="50"  height="160" fill="#bfdbfe" opacity="0.5"/>
          <rect x="110" y="145" width="40"  height="135" fill="#93c5fd" opacity="0.45"/>
          <rect x="160" y="100" width="70"  height="180" fill="#bfdbfe" opacity="0.5"/>
          <rect x="220" y="130" width="45"  height="150" fill="#93c5fd" opacity="0.45"/>
          <rect x="280" y="80"  width="90"  height="200" fill="#bfdbfe" opacity="0.5"/>
          <rect x="360" y="140" width="55"  height="140" fill="#93c5fd" opacity="0.45"/>
          <rect x="420" y="110" width="65"  height="170" fill="#bfdbfe" opacity="0.5"/>
          <rect x="500" y="90"  width="80"  height="190" fill="#93c5fd" opacity="0.45"/>
          <rect x="590" y="120" width="60"  height="160" fill="#bfdbfe" opacity="0.5"/>
          <rect x="660" y="70"  width="100" height="210" fill="#93c5fd" opacity="0.45"/>
          <rect x="770" y="115" width="70"  height="165" fill="#bfdbfe" opacity="0.5"/>
          <rect x="850" y="95"  width="85"  height="185" fill="#93c5fd" opacity="0.45"/>
          <rect x="940" y="130" width="55"  height="150" fill="#bfdbfe" opacity="0.5"/>
          <rect x="1000" y="85" width="95"  height="195" fill="#93c5fd" opacity="0.45"/>
          <rect x="1100" y="125" width="60" height="155" fill="#bfdbfe" opacity="0.5"/>
          <rect x="1170" y="100" width="75" height="180" fill="#93c5fd" opacity="0.45"/>
          <rect x="1250" y="140" width="50" height="140" fill="#bfdbfe" opacity="0.5"/>
          <rect x="1310" y="110" width="65" height="170" fill="#93c5fd" opacity="0.45"/>
          <rect x="1380" y="130" width="60" height="150" fill="#bfdbfe" opacity="0.5"/>

          {/* güneş paneli çatılar */}
          {[[282,80],[500,90],[662,70],[1002,85]].map(([x,y],i) => (
            <g key={i}>
              <rect x={x+5}  y={y-10} width={18} height={8} rx="1" fill="#fbbf24" opacity="0.85"/>
              <rect x={x+26} y={y-10} width={18} height={8} rx="1" fill="#fbbf24" opacity="0.85"/>
              <rect x={x+47} y={y-10} width={18} height={8} rx="1" fill="#fbbf24" opacity="0.85"/>
            </g>
          ))}

          {/* pencere ışıkları */}
          {[[170,115],[290,100],[510,110],[670,90],[860,115],[1010,105],[1180,120]].map(([x,y],i) => (
            <g key={`w${i}`} opacity="0.6">
              <rect x={x}    y={y}    width="8" height="6" rx="1" fill="#fef9c3"/>
              <rect x={x+14} y={y}    width="8" height="6" rx="1" fill="#fef9c3"/>
              <rect x={x}    y={y+16} width="8" height="6" rx="1" fill="#fef9c3"/>
              <rect x={x+14} y={y+16} width="8" height="6" rx="1" fill="#bfdbfe"/>
            </g>
          ))}
        </svg>
      </div>

      {/* Yeşil zemin — ön */}
      <div ref={groundRef} style={{ position: "absolute", bottom: 0, left: 0, right: 0, willChange: "transform" }}>
        <svg viewBox="0 0 1440 180" style={{ width: "100%", display: "block" }} preserveAspectRatio="xMidYMax slice">
          {/* arka tepe */}
          <ellipse cx="300"  cy="160" rx="420" ry="90" fill="#bbf7d0" opacity="0.8"/>
          <ellipse cx="1150" cy="160" rx="380" ry="85" fill="#bbf7d0" opacity="0.8"/>
          {/* ön tepe */}
          <ellipse cx="0"    cy="180" rx="300" ry="100" fill="#86efac"/>
          <ellipse cx="480"  cy="180" rx="480" ry="120" fill="#4ade80"/>
          <ellipse cx="960"  cy="180" rx="500" ry="110" fill="#86efac"/>
          <ellipse cx="1440" cy="180" rx="320" ry="100" fill="#4ade80"/>
          {/* zemin şeridi */}
          <rect x="0" y="155" width="1440" height="30" fill="#22c55e"/>
          {/* küçük çiçekler */}
          {[80,200,350,520,680,820,980,1120,1280,1400].map((x,i) => (
            <g key={i}>
              <circle cx={x}   cy="155" r="4" fill={i%3===0?"#fbbf24":i%3===1?"#f472b6":"#a78bfa"} opacity="0.9"/>
              <circle cx={x+20} cy="158" r="3" fill={i%2===0?"#fde047":"#86efac"} opacity="0.8"/>
            </g>
          ))}
        </svg>
      </div>

      <style>{`
        @keyframes sunPulse { 0%,100%{transform:scale(1);opacity:0.8} 50%{transform:scale(1.12);opacity:1} }
        @keyframes floatPart { 0%{transform:translateY(0)} 100%{transform:translateY(-18px)} }
      `}</style>
    </div>
  );
}

function Hero() {
  return (
    <section id="top" style={{
      position: "relative",
      paddingTop: 160, paddingBottom: 0,
      textAlign: "center",
      overflow: "hidden",
      minHeight: "100vh",
    }}>
      {/* 3D parallax arka plan */}
      <HeroScene />

      {/* İçerik */}
      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        <motion.div initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <span className="eyebrow" style={{ background: "rgba(255,255,255,0.75)", backdropFilter: "blur(8px)" }}>
            Takviyeli Öğrenme · EPİAŞ · Gerçek Zamanlı
          </span>
          <h1 style={{ textShadow: "0 2px 24px rgba(0,0,0,0.08)" }}>
            Binanız için{" "}
            <span style={{
              display: "inline-flex", verticalAlign: "middle",
              width: "0.95em", height: "0.95em", borderRadius: "22%",
              background: "linear-gradient(135deg,#f59e0b,#22c55e)",
              color: "#fff", alignItems: "center", justifyContent: "center",
              fontSize: "0.5em", fontWeight: 800, margin: "0 0.08em",
              boxShadow: "0 4px 20px #22c55e44",
            }}>RL</span>{" "}
            enerji yönetimi
          </h1>
        </motion.div>
        <motion.p className="sub" style={{ margin: "22px auto 30px", maxWidth: 560 }}
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
          Güneş paneli ve bataryası olan binanız için gerçek EPİAŞ fiyat verisiyle eğitilmiş SAC ajanı
          saat saat şarj/deşarj kararları verir — faturanızı otomatik düşürür.
        </motion.p>
        <motion.div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }}>
          <a className="btn btn-blue" href="http://localhost:8501">
            Dashboard'u Aç <span className="arr"><Arrow size={14} /></span>
          </a>
          <a className="btn btn-white" href="#how">Nasıl Çalışır</a>
        </motion.div>
        <motion.div style={{ display: "flex", gap: 22, justifyContent: "center", flexWrap: "wrap", margin: "26px 0 50px" }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
          <span className="chip" style={{ background: "rgba(255,255,255,0.8)", backdropFilter: "blur(6px)" }}>
            <span style={{ color: "var(--amber)", display: "flex" }}><Star size={17} /></span> SAC +14.4 TL/gün
          </span>
          <span className="chip" style={{ background: "rgba(255,255,255,0.8)", backdropFilter: "blur(6px)" }}>
            <span style={{ color: "var(--green)", display: "flex" }}><Shield size={17} /></span> %29.93 sMAPE tahmin
          </span>
          <span className="chip" style={{ background: "rgba(255,255,255,0.8)", backdropFilter: "blur(6px)" }}>
            <span style={{ color: "#3b82f6", display: "flex" }}><Bolt size={17} /></span> 74 gün test seti
          </span>
        </motion.div>
      </div>

      {/* Dashboard mockup — sahne içinde yüzer */}
      <div style={{ position: "relative", zIndex: 1, padding: "0 20px 0" }}>
        <div style={{ maxWidth: 1020, margin: "0 auto" }}>
          <Mockup />
        </div>
      </div>
    </section>
  );
}

/* ── Bina tipleri (Brands yerine) ────────────────────────────── */
/* ── SVG bina ikonları ──────────────────────────────────────── */
function MustakilSvg({ hovered }) {
  return (
    <svg viewBox="0 0 120 100" width="100" height="84">
      {/* zemin */}
      <rect x="10" y="72" width="100" height="5" rx="2" fill="#bbf7d0"/>
      {/* bina gövde */}
      <rect x="22" y="45" width="76" height="32" fill={hovered ? "#d1fae5" : "#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      {/* çatı */}
      <polygon points="60,10 8,45 112,45" fill={hovered ? "#22c55e" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* güneş paneli */}
      <rect x="38" y="22" width="14" height="8" rx="1" fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="55" y="22" width="14" height="8" rx="1" fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* kapı */}
      <rect x="50" y="57" width="20" height="20" rx="2" fill={hovered ? "#6ee7b7" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* pencereler */}
      <rect x="27" y="52" width="14" height="11" rx="2" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="79" y="52" width="14" height="11" rx="2" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* baca */}
      <rect x="78" y="15" width="8" height="14" rx="2" fill="#94a3b8"/>
      {hovered && <circle cx="82" cy="13" r="5" fill="#fbbf2466"><animate attributeName="r" values="5;9;5" dur="1.2s" repeatCount="indefinite"/></circle>}
    </svg>
  );
}

function VillaSvg({ hovered }) {
  return (
    <svg viewBox="0 0 120 100" width="100" height="84">
      <rect x="10" y="72" width="100" height="5" rx="2" fill="#bbf7d0"/>
      {/* 1. kat */}
      <rect x="10" y="45" width="100" height="30" fill={hovered ? "#d1fae5" : "#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      {/* 2. kat */}
      <rect x="28" y="25" width="64" height="22" fill={hovered ? "#a7f3d0" : "#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      {/* düz çatı şeritleri */}
      <rect x="8"  y="42" width="104" height="5" rx="1" fill={hovered ? "#22c55e" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      <rect x="26" y="22" width="68"  height="5" rx="1" fill={hovered ? "#22c55e" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* güneş panelleri çatıda */}
      <rect x="35" y="24" width="12" height="7" rx="1" fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="50" y="24" width="12" height="7" rx="1" fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="65" y="24" width="12" height="7" rx="1" fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* kapı */}
      <rect x="50" y="55" width="20" height="20" rx="2" fill={hovered ? "#6ee7b7" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* 1. kat pencereleri */}
      <rect x="15" y="50" width="14" height="10" rx="2" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="91" y="50" width="14" height="10" rx="2" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* 2. kat pencereleri */}
      <rect x="34" y="30" width="12" height="8" rx="1" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="74" y="30" width="12" height="8" rx="1" fill={hovered ? "#bfdbfe" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* havuz */}
      {hovered && <ellipse cx="60" cy="80" rx="18" ry="5" fill="#7dd3fc" opacity="0.7"><animate attributeName="rx" values="18;22;18" dur="2s" repeatCount="indefinite"/></ellipse>}
    </svg>
  );
}

function ApartmanSvg({ hovered }) {
  return (
    <svg viewBox="0 0 120 100" width="100" height="84">
      <rect x="10" y="78" width="100" height="5" rx="2" fill="#bbf7d0"/>
      {/* gövde */}
      <rect x="18" y="18" width="84" height="62" fill={hovered ? "#d1fae5" : "#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      {/* çatı şeridi */}
      <rect x="15" y="14" width="90" height="6" rx="2" fill={hovered ? "#22c55e" : "#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* güneş panelleri */}
      {[24,40,56,72,88].map((x,i) => (
        <rect key={i} x={x} y="15" width="11" height="5" rx="1"
          fill={hovered ? "#fbbf24" : "#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      ))}
      {/* kat çizgileri */}
      <line x1="18" y1="38" x2="102" y2="38" stroke={hovered?"#a7f3d0":"#cbd5e1"} strokeWidth="1"/>
      <line x1="18" y1="55" x2="102" y2="55" stroke={hovered?"#a7f3d0":"#cbd5e1"} strokeWidth="1"/>
      <line x1="18" y1="62" x2="102" y2="62" stroke={hovered?"#a7f3d0":"#cbd5e1"} strokeWidth="1"/>
      {/* pencereler 3 kat × 4 sütun */}
      {[0,1,2].map(row => [26,42,62,78].map((x,c) => (
        <rect key={`${row}-${c}`} x={x} y={22+row*17} width="12" height="10" rx="1"
          fill={hovered ? (row===0&&c===1?"#fef9c3":"#bfdbfe") : "#cbd5e1"}
          style={{transition:"fill 0.3s"}}/>
      )))}
      {/* giriş kapısı */}
      <rect x="50" y="62" width="20" height="18" rx="2" fill={hovered?"#6ee7b7":"#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* asansör ışığı */}
      {hovered && <rect x="54" y="25" width="12" height="28" rx="2" fill="#fef9c366"><animate attributeName="y" values="25;35;25" dur="1.8s" repeatCount="indefinite"/></rect>}
    </svg>
  );
}

function OfisSvg({ hovered }) {
  return (
    <svg viewBox="0 0 120 100" width="100" height="84">
      <rect x="10" y="78" width="100" height="5" rx="2" fill="#bbf7d0"/>
      {/* 2 kule */}
      <rect x="12" y="22" width="44" height="58" fill={hovered?"#d1fae5":"#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      <rect x="64" y="10" width="44" height="70" fill={hovered?"#a7f3d0":"#e2e8f0"} style={{transition:"fill 0.3s"}}/>
      {/* çatı şeritleri */}
      <rect x="10" y="18" width="48" height="5" rx="1" fill={hovered?"#22c55e":"#94a3b8"} style={{transition:"fill 0.3s"}}/>
      <rect x="62" y="6" width="48" height="5" rx="1" fill={hovered?"#22c55e":"#94a3b8"} style={{transition:"fill 0.3s"}}/>
      {/* güneş panelleri sol kule */}
      <rect x="18" y="19" width="10" height="5" rx="1" fill={hovered?"#fbbf24":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="31" y="19" width="10" height="5" rx="1" fill={hovered?"#fbbf24":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* güneş panelleri sağ kule */}
      <rect x="70" y="7"  width="10" height="5" rx="1" fill={hovered?"#fbbf24":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="83" y="7"  width="10" height="5" rx="1" fill={hovered?"#fbbf24":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      <rect x="96" y="7"  width="10" height="5" rx="1" fill={hovered?"#fbbf24":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      {/* sol kule pencereler */}
      {[0,1,2,3].map(row => [18,32].map((x,c) => (
        <rect key={`sl${row}${c}`} x={x} y={28+row*12} width="10" height="8" rx="1"
          fill={hovered?"#bfdbfe":"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      )))}
      {/* sağ kule pencereler */}
      {[0,1,2,3,4].map(row => [70,84,98].map((x,c) => (
        <rect key={`sr${row}${c}`} x={x} y={16+row*12} width="10" height="8" rx="1"
          fill={hovered?(row%2===c%2?"#fef9c3":"#bfdbfe"):"#cbd5e1"} style={{transition:"fill 0.3s"}}/>
      )))}
      {/* anten */}
      <rect x="84" y="2" width="2" height="10" fill="#94a3b8"/>
      {hovered && <circle cx="85" cy="2" r="3" fill="#ef444488"><animate attributeName="opacity" values="1;0;1" dur="0.8s" repeatCount="indefinite"/></circle>}
    </svg>
  );
}

function BinaTipleri() {
  const [hov, setHov] = useState(null);

  const tipler = [
    {
      id: "mustak", isim: "Müstakil Ev", color: "#22c55e", bg: "#f0fdf4",
      svg: (h) => <MustakilSvg hovered={h}/>,
      specs: [
        { label: "Kat", value: "1–2 kat" },
        { label: "Oda", value: "3–7 oda" },
        { label: "Çatı", value: "60–180 m²" },
        { label: "Batarya", value: "5–15 kWh" },
      ],
      desc: "Bahçeli müstakil evler için yüksek güneş potansiyeli.",
    },
    {
      id: "villa", isim: "Villa", color: "#3b82f6", bg: "#eff6ff",
      svg: (h) => <VillaSvg hovered={h}/>,
      specs: [
        { label: "Kat", value: "2–3 kat" },
        { label: "Oda", value: "4–10 oda" },
        { label: "Çatı", value: "120–300 m²" },
        { label: "Batarya", value: "10–25 kWh" },
      ],
      desc: "Geniş çatılı villalar için yüksek panel kapasitesi.",
    },
    {
      id: "apt", isim: "Apartman", color: "#8b5cf6", bg: "#f5f3ff",
      svg: (h) => <ApartmanSvg hovered={h}/>,
      specs: [
        { label: "Kat", value: "3–10 kat" },
        { label: "Daire/kat", value: "2–6 daire" },
        { label: "Asansör", value: "opsiyonel" },
        { label: "Batarya", value: "20–60 kWh" },
      ],
      desc: "Ortak alan tüketimi + daire bazlı optimizasyon.",
    },
    {
      id: "ofis", isim: "Ofis Binası", color: "#f59e0b", bg: "#fffbeb",
      svg: (h) => <OfisSvg hovered={h}/>,
      specs: [
        { label: "Kat", value: "4–12 kat" },
        { label: "Birim", value: "8–40 ofis" },
        { label: "HVAC", value: "merkezi sistem" },
        { label: "Batarya", value: "40–120 kWh" },
      ],
      desc: "Gündüz yoğun tüketim + EV şarj istasyonu desteği.",
    },
  ];

  return (
    <section style={{ padding: "80px 0", background: "#f8fafc" }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 52 }}>
          <span className="eyebrow">Desteklenen bina tipleri</span>
          <h2>Her bina tipi, kendi profiliyle</h2>
          <p className="sub" style={{ maxWidth: 480, margin: "12px auto 0" }}>
            Kat sayısı, oda sayısı, çatı alanı — hepsi slider ile ayarlanabilir. Batarya kapasitesi otomatik hesaplanır.
          </p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20 }}>
          {tipler.map((t) => {
            const isHov = hov === t.id;
            return (
              <motion.div
                key={t.id}
                onMouseEnter={() => setHov(t.id)}
                onMouseLeave={() => setHov(null)}
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                style={{
                  background: isHov ? t.bg : "#fff",
                  border: `2px solid ${isHov ? t.color : "#e2e8f0"}`,
                  borderRadius: 20, padding: "32px 24px",
                  cursor: "default",
                  transition: "background 0.3s, border-color 0.3s, box-shadow 0.3s",
                  boxShadow: isHov ? `0 12px 40px ${t.color}22` : "0 2px 8px #0000050a",
                  transform: isHov ? "translateY(-6px)" : "translateY(0)",
                }}>
                {/* SVG bina */}
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 20, height: 88 }}>
                  {t.svg(isHov)}
                </div>

                {/* başlık */}
                <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 4, color: isHov ? t.color : "#0f172a", transition: "color 0.3s" }}>
                  {t.isim}
                </div>
                <div style={{ fontSize: 13.5, color: "#64748b", marginBottom: 20, lineHeight: 1.6 }}>{t.desc}</div>

                {/* spec grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 12px" }}>
                  {t.specs.map(s => (
                    <div key={s.label} style={{
                      background: isHov ? t.color + "12" : "#f1f5f9",
                      borderRadius: 10, padding: "8px 10px",
                      transition: "background 0.3s",
                    }}>
                      <div style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>{s.label}</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: isHov ? t.color : "#334155", marginTop: 2, transition: "color 0.3s" }}>{s.value}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ── Önce / Sonra ────────────────────────────────────────────── */
function BeforeAfter() {
  const [after, setAfter] = useState(false);
  return (
    <section style={{ textAlign: "center" }}>
      <div className="container">
        <motion.h2 {...fadeUp}>Akıllı kararlar, daha düşük fatura</motion.h2>
        <motion.div {...fadeUp} style={{ margin: "26px 0 22px" }}>
          <div className="toggle-pill" role="tablist">
            <button className={!after ? "on" : ""} onClick={() => setAfter(false)} role="tab" aria-selected={!after}>Sisteme sahip olmadan</button>
            <button className={after ? "on" : ""} onClick={() => setAfter(true)} role="tab" aria-selected={after}>SmartHome RL ile</button>
          </div>
        </motion.div>
        <div style={{ maxWidth: 560, margin: "0 auto", perspective: 900 }}>
          <AnimatePresence mode="wait">
            {!after ? (
              <motion.div key="b" className="card" style={{ textAlign: "left" }}
                initial={{ opacity: 0, rotateY: -14 }} animate={{ opacity: 1, rotateY: 0 }}
                exit={{ opacity: 0, rotateY: 14 }} transition={{ duration: 0.3 }}>
                <h3 style={{ marginBottom: 14 }}>Enerji yönetimindeki zorluklar</h3>
                {["Güneş üretimi en pahalı saatte değil, en ucuz saatte depoya giriyor",
                  "Elektrik kesintisinde batarya yeterince hazır değil",
                  "Hangi saatte şarj, hangi saatte deşarj yapılacağı bilinmiyor",
                  "EPİAŞ fiyat değişimlerini takip etmek zaman alıyor"].map((t) => (
                  <div className="tick" key={t}><span className="c" style={{ color: "var(--red)" }}><X /></span>{t}</div>
                ))}
                <div style={{ display: "flex", gap: 30, marginTop: 20 }}>
                  <div><div style={{ fontSize: 30, fontWeight: 800 }}>%40+</div><div className="sub" style={{ fontSize: 14 }}>Kaçırılan arbitraj fırsatı</div></div>
                  <div><div style={{ fontSize: 30, fontWeight: 800 }}>Manuel</div><div className="sub" style={{ fontSize: 14 }}>Saatlik takip gerekliliği</div></div>
                </div>
              </motion.div>
            ) : (
              <motion.div key="a" className="card" style={{ textAlign: "left", background: "#141414", color: "#fff" }}
                initial={{ opacity: 0, rotateY: -14 }} animate={{ opacity: 1, rotateY: 0 }}
                exit={{ opacity: 0, rotateY: 14 }} transition={{ duration: 0.3 }}>
                <h3 style={{ marginBottom: 14 }}>RL ajanıyla <span style={{ color: "var(--green)" }}>otomatik optimizasyon</span></h3>
                {["Ucuz saatte şarj, pahalı saatte deşarj — her gün otomatik",
                  "Kesinti öncesi batarya hazır tutulur, jeneratör devreye girer",
                  "SAC ajanı 74 günlük test setinde günde +14.4 TL net tasarruf sağladı",
                  "EPİAŞ API ile gerçek zamanlı fiyat takibi, tahmin olmadan da çalışır"].map((t) => (
                  <div className="tick" key={t} style={{ color: "#d8d8d8" }}>
                    <span className="c" style={{ color: "var(--green)" }}><Check /></span>{t}
                  </div>
                ))}
                <div style={{ display: "flex", gap: 30, marginTop: 20 }}>
                  <div><div style={{ fontSize: 30, fontWeight: 800, color: "var(--green)" }}>+14.4 TL</div><div style={{ fontSize: 14, color: "#9a9a9a" }}>Günlük ortalama tasarruf</div></div>
                  <div><div style={{ fontSize: 30, fontWeight: 800, color: "var(--green)" }}>7/24</div><div style={{ fontSize: 14, color: "#9a9a9a" }}>Tam otomatik karar</div></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

/* ── Bina SVG — aktif duruma göre değişir ─────────────────────── */
function BuildingViz({ active }) {
  const isSolar   = active === 0;
  const isBattery = active === 1;
  const isEpias   = active === 2;
  const isOutage  = active === 3;
  const isAgent   = active === 4;

  const winColor = (floor, col) => {
    if (isOutage) return (floor === 1 && col === 1) ? "#fbbf24" : "#1e293b";
    if (isSolar)  return "#fef3c7";
    return (floor + col) % 2 === 0 ? "#bfdbfe" : "#dbeafe";
  };

  const battFill = isBattery ? 0.85 : 0.52;
  const chartPts = [0,6,4,10,3,2,12,16,14,9].map((v,i) => `${i*7},${18-v}`).join(" ");
  const skyColor = isOutage ? "#0f172a" : isSolar ? "#fef9c3" : "#e0f2fe";
  const wallColor = isOutage ? "#1e293b" : "#e2e8f0";
  const sideColor = isOutage ? "#0f172a" : "#94a3b8";
  const roofColor = isOutage ? "#334155" : "#cbd5e1";

  return (
    <div style={{ position: "relative", userSelect: "none" }}>
      <svg viewBox="0 0 280 370" style={{ width: "100%", maxHeight: 460, transition: "all 0.5s" }}>
        {/* gökyüzü */}
        <rect x="0" y="0" width="280" height="370" fill={skyColor} style={{ transition: "fill 0.6s" }}/>

        {/* güneş (solar modda) */}
        {isSolar && (
          <g>
            <circle cx="228" cy="52" r="26" fill="#fde047" opacity="0.95">
              <animate attributeName="r" values="26;30;26" dur="2.5s" repeatCount="indefinite"/>
            </circle>
            {[0,45,90,135,180,225,270,315].map(a => (
              <line key={a}
                x1={228 + Math.cos(a*Math.PI/180)*32} y1={52 + Math.sin(a*Math.PI/180)*32}
                x2={228 + Math.cos(a*Math.PI/180)*40} y2={52 + Math.sin(a*Math.PI/180)*40}
                stroke="#fde047" strokeWidth="2" opacity="0.6"/>
            ))}
          </g>
        )}

        {/* zemin */}
        <rect x="0" y="318" width="280" height="52" fill={isOutage ? "#1e293b" : "#e2e8f0"} style={{ transition: "fill 0.6s" }}/>

        {/* yan yüz (3D derinlik) */}
        <polygon points="200,62 238,44 238,308 200,318" fill={sideColor} style={{ transition: "fill 0.6s" }}/>

        {/* ön yüz */}
        <rect x="42" y="62" width="158" height="256" fill={wallColor} style={{ transition: "fill 0.6s" }}/>

        {/* çatı */}
        <polygon points="42,62 200,62 238,44 80,44" fill={roofColor} style={{ transition: "fill 0.6s" }}/>

        {/* kat çizgileri */}
        {[112, 162, 212, 262].map(y => (
          <line key={y} x1="42" y1={y} x2="200" y2={y}
            stroke={isOutage ? "#334155" : "#cbd5e1"} strokeWidth="1" style={{ transition: "stroke 0.6s" }}/>
        ))}

        {/* pencereler 5 kat × 3 sütun */}
        {[0,1,2,3,4].map(floor =>
          [0,1,2].map(col => {
            const x = 58 + col * 44;
            const y = 72 + floor * 50;
            return (
              <rect key={`${floor}-${col}`} x={x} y={y} width="28" height="26" rx="2"
                fill={winColor(floor, col)}
                style={{ transition: "fill 0.5s" }}
              />
            );
          })
        )}

        {/* güneş panelleri — çatı üzeri */}
        {[0,1,2].map(i => (
          <g key={`panel-${i}`}>
            <rect x={82+i*32} y="47" width="26" height="12" rx="1"
              fill={isSolar ? "#f59e0b" : "#3b82f6"}
              opacity={isSolar ? 1 : 0.65}
              style={{ transition: "fill 0.4s" }}
            >
              {isSolar && <animate attributeName="opacity" values="0.85;1;0.85" dur="1.8s" repeatCount="indefinite"/>}
            </rect>
            <line x1={95+i*32} y1="47" x2={95+i*32} y2="59"
              stroke={isSolar ? "#b45309" : "#1d4ed8"} strokeWidth="0.8"/>
            <line x1={82+i*32} y1="53" x2={108+i*32} y2="53"
              stroke={isSolar ? "#b45309" : "#1d4ed8"} strokeWidth="0.8"/>
          </g>
        ))}

        {/* batarya ünitesi — yan yüzde */}
        <rect x="208" y="205" width="22" height="68" rx="3"
          fill={isOutage ? "#334155" : "#f1f5f9"} stroke="#94a3b8" strokeWidth="1"/>
        <rect x="208" y={205 + 68*(1-battFill)} width="22" height={68*battFill} rx="2"
          fill={isBattery ? "#22c55e" : "#86efac"}
          style={{ transition: "all 0.8s" }}
        />
        <rect x="214" y="202" width="10" height="4" rx="1" fill="#64748b"/>
        {isBattery && (
          <>
            <text x="219" y="280" textAnchor="middle" fontSize="7.5" fontWeight="800" fill="#15803d">
              {Math.round(battFill*100)}%
            </text>
            <circle cx="219" cy="195" r="5" fill="#22c55e" opacity="0.7">
              <animate attributeName="opacity" values="0.5;1;0.5" dur="1.2s" repeatCount="indefinite"/>
            </circle>
          </>
        )}

        {/* EPİAŞ fiyat mini-ekran (ortadaki pencerede) */}
        {isEpias && (
          <g transform="translate(147, 72)">
            <rect width="28" height="26" rx="2" fill="#0f172a"/>
            <polyline points={chartPts} fill="none" stroke="#f59e0b" strokeWidth="1.5"
              transform="translate(2,5)"/>
          </g>
        )}
        {isEpias && (
          <>
            <text x="121" y="108" textAnchor="middle" fontSize="12" fontWeight="800" fill="#15803d">+312 ₺</text>
            <text x="121" y="121" textAnchor="middle" fontSize="8.5" fill="#64748b">günlük tasarruf</text>
          </>
        )}

        {/* kesinti alarmı */}
        {isOutage && (
          <>
            <circle cx="121" cy="32" r="9" fill="#ef4444">
              <animate attributeName="opacity" values="1;0.15;1" dur="0.7s" repeatCount="indefinite"/>
            </circle>
            <text x="121" y="28" textAnchor="middle" fontSize="7" fontWeight="800" fill="#fef2f2">!</text>
            <text x="121" y="20" textAnchor="middle" fontSize="8" fontWeight="700" fill="#ef4444">KESİNTİ</text>
          </>
        )}

        {/* ajan karar okları */}
        {isAgent && (
          <>
            <polygon points="72,83 80,100 64,100" fill="#3b82f6"/>
            <text x="72" y="76" textAnchor="middle" fontSize="7" fill="#1d4ed8" fontWeight="800">ŞARJ</text>
            <polygon points="152,142 160,126 144,126" fill="#ef4444"/>
            <text x="152" y="122" textAnchor="middle" fontSize="7" fill="#b91c1c" fontWeight="800">DEŞARJ</text>
            <text x="121" y="266" textAnchor="middle" fontSize="11" fontWeight="800" fill="#15803d">▲ +14.4 TL/gün</text>
          </>
        )}

        {/* EV şarj direği */}
        <rect x="50" y="286" width="6" height="30" rx="1" fill="#64748b"/>
        <rect x="46" y="281" width="14" height="10" rx="2" fill="#3b82f6" opacity="0.75"/>

        {/* zemin gölgesi */}
        <ellipse cx="121" cy="322" rx="76" ry="6" fill="#00000018"/>
      </svg>

      {/* Aktif durum etiketi */}
      <div style={{
        position: "absolute", bottom: 12, left: "50%", transform: "translateX(-50%)",
        background: "#0f172a", color: "#f8fafc", borderRadius: 999,
        padding: "6px 18px", fontSize: 12.5, fontWeight: 700, whiteSpace: "nowrap",
      }}>
        {["☀️ Güneş Paneli", "🔋 Akıllı Batarya", "⚡ EPİAŞ Fiyatları", "🚨 Kesinti Koruması", "🤖 SAC/TD3 Ajanı"][active]}
      </div>
    </div>
  );
}

/* ── Sticky Showcase — scroll-linked bina animasyonu ─────────── */
function StickyShowcase() {
  const [active, setActive] = useState(0);
  const refs = useRef([]);

  const features = [
    {
      icon: "☀️", color: "#f59e0b", bg: "#fef3c7",
      title: "Güneş Paneli Optimizasyonu",
      desc: "Çatı alanına göre panel sayısı ve kurulu güç otomatik hesaplanır. Mevsimsel üretim profili, öz-tüketim önceliği ve fazla üretim şebeke satışı tam entegre çalışır.",
      tags: ["450 W/panel", "%80 sistem verimi", "Mevsimsel profil"],
    },
    {
      icon: "🔋", color: "#22c55e", bg: "#dcfce7",
      title: "Akıllı Batarya Yönetimi",
      desc: "SAC ajanı ucuz saatte şarj, pahalı saatte deşarj kararı verir. Günlük tüketimin %40'ı kapasiteli batarya; %95 verim, %10 minimum SOC, C/2 şarj hızı.",
      tags: ["η = %95", "Min SOC %10", "C/2 şarj hızı"],
    },
    {
      icon: "⚡", color: "#3b82f6", bg: "#dbeafe",
      title: "Gerçek Zamanlı EPİAŞ",
      desc: "Gün öncesi piyasasından saatlik PTF fiyatları çekilir. API → arşiv CSV → Sentetik üçlü fallback zinciri sayesinde dashboard hiçbir zaman çökmez.",
      tags: ["TGT API auth", "CSV yedek", "Sentetik fallback"],
    },
    {
      icon: "🚨", color: "#ef4444", bg: "#fee2e2",
      title: "Kesinti Koruması",
      desc: "Elektrik kesildiğinde batarya ve güneş otomatik devreye girer. Opsiyonel jeneratör (12 TL/kWh) ile kesintisiz güç; karşılanamayan yük raporlanır.",
      tags: ["Otomatik devreye", "Jeneratör desteği", "Yük raporu"],
    },
    {
      icon: "🤖", color: "#8b5cf6", bg: "#ede9fe",
      title: "SAC / TD3 RL Ajanı",
      desc: "500k adım Curriculum Learning ile eğitilmiş. Oracle'dan Naive tahmine geçişte sadece ±0.2 TL fark — tahmine bağımlı değil, gerçek bir strateji öğrenmiş.",
      tags: ["+14.4 TL/gün", "±0.2 TL robust", "Faz 1→2→3"],
    },
  ];

  useEffect(() => {
    const observers = refs.current.map((el, i) => {
      if (!el) return null;
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActive(i); },
        { threshold: 0.55 }
      );
      obs.observe(el);
      return obs;
    });
    return () => observers.forEach(obs => obs && obs.disconnect());
  }, []);

  return (
    <section id="features" style={{ padding: "100px 0", background: "#fafaf8" }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 72 }}>
          <span className="eyebrow">Scroll ile keşfet</span>
          <h2>Her sistem, canlı görselleştirme ile</h2>
          <p className="sub" style={{ maxWidth: 480, margin: "12px auto 0" }}>
            Güneş panelinden kesinti korumasına — beş temel özellik, binanız üzerinde.
          </p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 64, alignItems: "start" }}>
          {/* Sol — yapışık bina görselleştirmesi */}
          <div style={{ position: "sticky", top: "14vh" }}>
            <BuildingViz active={active} />
          </div>

          {/* Sağ — kaydırmalı özellik kartları */}
          <div>
            {features.map((f, i) => (
              <div
                key={f.icon}
                ref={el => refs.current[i] = el}
                style={{ minHeight: "68vh", display: "flex", alignItems: "center" }}
              >
                <div style={{
                  background: active === i ? f.bg : "#fff",
                  border: `2px solid ${active === i ? f.color : "#e2e8f0"}`,
                  borderRadius: 20, padding: "36px 32px", width: "100%",
                  transition: "background 0.45s, border-color 0.45s",
                  boxShadow: active === i ? `0 8px 32px ${f.color}28` : "none",
                }}>
                  <div style={{
                    width: 54, height: 54, borderRadius: 14,
                    background: f.color + "20", fontSize: 28,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    marginBottom: 22,
                  }}>{f.icon}</div>
                  <h3 style={{ fontSize: 22, marginBottom: 12 }}>{f.title}</h3>
                  <p style={{ color: "#64748b", fontSize: 15.5, lineHeight: 1.75, marginBottom: 22 }}>{f.desc}</p>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {f.tags.map(tag => (
                      <span key={tag} style={{
                        background: f.color + "18", color: f.color,
                        borderRadius: 999, padding: "5px 15px",
                        fontSize: 13, fontWeight: 700,
                      }}>{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── İstatistikler ───────────────────────────────────────────── */
function Stats() {
  const rows = [
    ["SAC Algoritması", "+14.4 TL/gün", "Oracle modunda 74 günlük test seti ortalaması", "#141414", "#fff"],
    ["TD3 Algoritması", "+14.7 TL/gün", "SAC ile birlikte en yüksek performans", "#22c55e", "#fff"],
    ["Tahmin doğruluğu", "%29.93 sMAPE", "LightGBM+Optuna fiyat tahmini (gün-öncesi)", "#eceae6", "#1b1b1b"],
    ["Tahmine dayanıklılık", "±0.2 TL", "Oracle → Forecast → Naive arasındaki fark", "#3b82f6", "#fff"],
    ["Curriculum aşaması", "Faz 1→2→3", "Arbitraj → Güneş → Ertelenebilir yük eğitimi", "#f59e0b", "#1b1b1b"],
  ];
  return (
    <section id="stats">
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 34 }}>
          <span className="eyebrow">Gerçek sonuçlar</span>
          <h2>74 günlük test setinden performans</h2>
          <p className="sub" style={{ margin: "12px auto 0", maxWidth: 520 }}>
            Tüm metrikler, aligned_dataset'in son %20'si üzerinde hesaplanmıştır.
          </p>
        </motion.div>
        {rows.map(([l, n, d, bg, fg], i) => (
          <motion.div key={l} {...fadeUp} transition={{ ...fadeUp.transition, delay: i * 0.05 }}
            className="stat-row" style={{ background: bg, color: fg }}>
            <div style={{ fontSize: 14.5, fontWeight: 600, opacity: 0.85 }}>{l}</div>
            <div className="num">{n}</div>
            <div style={{ fontSize: 14.5, opacity: 0.75 }}>{d}</div>
            <span className="stat-icon" style={{ background: fg === "#fff" ? "#ffffff22" : "#00000010", color: fg }}>
              {[<Brain key="br" />, <Bolt key="bo" />, <Chart key="ch" />, <Gauge key="ga" />, <Cube key="cu" />][i]}
            </span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

/* ── Kullanım senaryoları ─────────────────────────────────────── */
function UseCases() {
  const cases = [
    ["🏠", "Müstakil ev & villa sahipleri",
     "Güneş paneli ve bataryanız varsa, ajan sabah ucuz saatte şarj edip akşam pahalı saatte deşarj ederek faturanızı düşürür.",
     "+5.200 TL/yıl", "Ortalama yıllık tasarruf tahmini"],
    ["🏢", "Apartman yöneticileri",
     "Asansör, ortak alan ve su pompası tüketimini gerçek EPİAŞ fiyatlarıyla optimize edin. Kesinti senaryosunu test edin.",
     "%40", "Pik talep azalması"],
    ["🏬", "Ofis binaları & ticari",
     "HVAC, EV şarj istasyonu ve güvenlik kameralarını birlikte yönetin. Amorti süresi ve CO₂ tasarrufu anında görülür.",
     "3–6 yıl", "Ortalama amorti süresi"],
    ["🔬", "Araştırmacılar & mühendisler",
     "Uzman modunda SAC/TD3/PPO/A2C algoritma karşılaştırması, Oracle/Forecast/Naive fiyat modu pivotu, mevsimsel ısı haritaları.",
     "4 mod", "Oracle · Forecast · Ensemble · Naive"],
  ];
  return (
    <section id="use-cases">
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 34 }}>
          <span className="eyebrow">Kullanım senaryoları</span>
          <h2>Kim için geliştirildi?</h2>
        </motion.div>
        {cases.map(([emoji, t, d, m, md], i) => (
          <motion.div key={t} {...fadeUp} transition={{ ...fadeUp.transition, delay: i * 0.05 }}
            className="photo-card"
            style={{ background: i % 2 === 0 ? "#f9fafb" : "#fff", padding: "34px 32px", marginBottom: 16, border: "1px solid var(--line)", borderRadius: 20 }}>
            <div style={{ display: "flex", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
              <span style={{ fontSize: 36 }}>{emoji}</span>
              <div style={{ flex: 1 }}>
                <h3>{t}</h3>
                <p className="sub" style={{ maxWidth: 500, margin: "6px 0 16px", fontSize: 15.5 }}>{d}</p>
                <div style={{ fontSize: 26, fontWeight: 800 }}>{m}</div>
                <div className="sub" style={{ fontSize: 14 }}>{md}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

/* ── Mimari quote ─────────────────────────────────────────────── */
function TechQuote() {
  return (
    <section style={{ paddingTop: 20 }}>
      <div className="container">
        <motion.div {...fadeUp} className="card" style={{ padding: "44px 32px", textAlign: "center" }}>
          <div style={{ display: "flex", gap: 20, justifyContent: "center", flexWrap: "wrap", marginBottom: 24 }}>
            {["Stable-Baselines3", "LightGBM + Optuna", "Streamlit + Three.js", "EPİAŞ API"].map((c) => (
              <span key={c} className="eyebrow" style={{ marginBottom: 0 }}>{c}</span>
            ))}
          </div>
          <blockquote style={{ fontSize: "clamp(18px,2.4vw,26px)", fontWeight: 700, maxWidth: 720, margin: "0 auto 22px", letterSpacing: "-0.01em" }}>
            "SAC ve TD3 ajanları tahmin belirsizliğine karşı robust — Oracle'dan Naive'e geçişte sadece ±0.2 TL fark var. Tahmin kalitesi kritik değil."
          </blockquote>
          <div style={{ fontWeight: 700 }}>Gün 15 Karşılaştırma Analizi · SmartHome-EnergyRL</div>
        </motion.div>
      </div>
    </section>
  );
}

/* ── SSS ─────────────────────────────────────────────────────── */
function Faq() {
  const qs = [
    ["Gerçek bir bina ile entegre edilebilir mi?",
     "Dashboard simülasyon tabanlıdır; gerçek bina entegrasyonu için MQTT broker, akıllı sayaç veya Home Assistant API bağlantısı eklenmesi gerekir. Bu Faz 5 kapsamında planlanmaktadır."],
    ["EPİAŞ API hesabı olmadan çalışır mı?",
     "Evet. EPİAŞ API bilgileri boş bırakılırsa sistem otomatik olarak arşiv CSV'sine, o da yoksa sentetik EPİAŞ deseni üreteciye geçer."],
    ["Model nasıl eğitildi?",
     "SAC ve TD3, Curriculum Learning Faz 1→2→3 ile eğitildi: önce fiyat arbitrajı, sonra güneş+talep, son olarak ertelenebilir yük + tahmin robustluğu. 500k adım, Colab T4 GPU."],
    ["Batarya ve panel boyutunu nasıl belirliyor?",
     "Batarya kapasitesi günlük tüketimin %40'ı, şarj/deşarj gücü C/2, panel sayısı çatı alanı ÷ 1.7 m² × 450 W olarak otomatik hesaplanır."],
    ["Hangi algoritmalar destekleniyor?",
     "SAC, TD3, PPO, A2C (Stable-Baselines3), Eşik Kuralı, ForecastAwarePolicy ve Bekle baseline'ları. Uzman modunda tüm algoritmaların Oracle/Forecast/Naive karşılaştırması görülebilir."],
  ];
  const [open, setOpen] = useState(0);
  return (
    <section id="faq">
      <div className="container grid grid-2" style={{ alignItems: "start" }}>
        <motion.div {...fadeUp}>
          <h2 style={{ maxWidth: 420 }}>Sıkça sorulan sorular</h2>
          <p className="sub" style={{ margin: "12px 0 26px", maxWidth: 400 }}>
            Proje, teknik detaylar ve entegrasyon hakkında sık sorulan sorular.
          </p>
          <div className="card" style={{ maxWidth: 380 }}>
            <h3 style={{ fontSize: 19, marginBottom: 8 }}>Hâlâ sorunuz var mı?</h3>
            <p className="sub" style={{ fontSize: 14.5, margin: "4px 0 16px" }}>
              GitHub Issues üzerinden soru sorabilirsiniz.
            </p>
            <a className="btn btn-dark" href="https://github.com/isambais/SmartHome-EnergyRL/issues" target="_blank" rel="noreferrer" style={{ padding: "11px 20px", fontSize: 14 }}>
              GitHub Issues <span className="arr"><Arrow size={13} /></span>
            </a>
          </div>
        </motion.div>
        <motion.div {...fadeUp}>
          {qs.map(([q, a], i) => (
            <div key={q} className="faq-item">
              <button className="faq-q" onClick={() => setOpen(open === i ? -1 : i)} aria-expanded={open === i}>
                {q}
                <motion.span animate={{ rotate: open === i ? 45 : 0 }}
                  style={{ display: "flex", color: "var(--muted)", fontSize: 22, fontWeight: 400 }}>+</motion.span>
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.26 }} style={{ overflow: "hidden" }}>
                    <div className="faq-a">{a}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* ── CTA ─────────────────────────────────────────────────────── */
function Cta() {
  return (
    <section style={{
      background: "linear-gradient(135deg, #0d1117 0%, #1a2332 50%, #0f2417 100%)",
      textAlign: "center", padding: "110px 0",
    }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ color: "#e6edf3" }}>
          <span className="eyebrow" style={{ background: "#21262d", color: "#58a6ff" }}>Ücretsiz & Açık Kaynak</span>
          <h2 style={{ color: "#fff", marginTop: 16 }}>Dashboard'u şimdi açın</h2>
          <p style={{ color: "#8b949e", margin: "14px auto 30px", maxWidth: 480, fontSize: 18 }}>
            Binanızı tanımlayın, simülasyonu başlatın — SAC ajanı saat saat karar versin.
          </p>
          <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
            <a className="btn btn-blue" href="http://localhost:8501">
              Dashboard'u Aç <span className="arr"><Arrow size={14} /></span>
            </a>
            <a className="btn" href="https://github.com/isambais/SmartHome-EnergyRL" target="_blank" rel="noreferrer"
              style={{ background: "#21262d", color: "#e6edf3", border: "1px solid #30363d" }}>
              GitHub'da Gör
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer>
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 30 }} className="foot-grid">
          <div>
            <div className="logo" style={{ marginBottom: 12 }}>
              <span className="logo-mark"><Bolt size={17} /></span> SmartHome Energy RL
            </div>
            <p className="sub" style={{ fontSize: 14.5, maxWidth: 260 }}>
  EPİAŞ verisiyle eğitilmiş RL ajanı tabanlı bina enerji yönetim sistemi.
</p>
<a
  href="mailto:isambais18@gmail.com"
  style={{ marginTop: 10, fontWeight: 600, color: "var(--ink)" }}
>
  isambais18@gmail.com
</a>
</div>
          <div>
            <h4>Dashboard</h4>
            <a href="http://localhost:8501">Bina Simülasyonu</a>
            <a href="http://localhost:8501">Canlı EPİAŞ</a>
            <a href="http://localhost:8501">Yatırım & Çevre</a>
            <a href="http://localhost:8501">Uzman Modu</a>
          </div>
          <div>
            <h4>Proje</h4>
            <a href="#features">Özellikler</a>
            <a href="#how">Nasıl Çalışır</a>
            <a href="#stats">Sonuçlar</a>
            <a href="#faq">SSS</a>
          </div>
          <div>
            <h4>Bağlantılar</h4>
            <a href="https://github.com/isambais/SmartHome-EnergyRL" target="_blank" rel="noreferrer">GitHub</a>
            <a href="https://github.com/isambais/SmartHome-EnergyRL/issues" target="_blank" rel="noreferrer">Issues</a>
            <a href="https://github.com/isambais/SmartHome-EnergyRL/pulls" target="_blank" rel="noreferrer">Pull Requests</a>
          </div>
        </div>
        <div style={{ borderTop: "1px solid var(--line)", marginTop: 34, paddingTop: 24, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 14, color: "var(--muted)" }}>
          <span>© {new Date().getFullYear()} SmartHome-EnergyRL · Trunçgil Teknoloji Staj Projesi</span>
          <span style={{ fontSize: 13 }}>Gaziantep Teknopark · SAC + EPİAŞ + Three.js</span>
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <BinaTipleri />
        <BeforeAfter />
        <StickyShowcase />
        <UseCases />
        <TechQuote />
        <Stats />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </>
  );
}

