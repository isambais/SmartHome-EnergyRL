import { AnimatePresence, motion, useScroll, useSpring } from "framer-motion";
import Footer from "../components/Footer.jsx";
import { Link } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import { useState, useEffect, useRef } from "react";
import {
  Alert, Arrow, Battery, Bolt, Brain, Chart, Check, Chevron,
  Coins, Cube, Gauge, Home, Shield, Star, Sun, X,
} from "../icons.jsx";
import { useI18n, useT } from "../i18n.jsx";

/* Kaydırınca içerik belirgin biçimde aşağıdan yukarı süzülür.
   margin: alttan -12% → eleman ekrana iyice girmeden tetiklenmez,
   böylece kullanıcı hareketi gerçekten görür. */
const EASE = [0.22, 1, 0.36, 1];
const fadeUp = {
  initial: { opacity: 0, y: 46 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "0px 0px -80px 0px" },
  transition: { duration: 0.6, ease: EASE },
};

/* Grid/list öğelerini sırayla (cascade) açmak için yardımcı.
   i = öğe indeksi → her kart bir öncekinden 0.1s sonra gelir.
   NOT: viewport.margin yalnızca px kabul eder — % observer'ı bozar. */
const reveal = (i = 0, y = 46) => ({
  initial: { opacity: 0, y },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "0px 0px -70px 0px" },
  transition: { duration: 0.55, ease: EASE, delay: i * 0.1 },
});

/* Sayfa üstünde kaydırma ilerleme çubuğu — sayfaya "canlılık" katar. */
function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 30, restDelta: 0.001 });
  return (
    <motion.div style={{
      position: "fixed", top: 0, left: 0, right: 0, height: 3, zIndex: 100,
      transformOrigin: "0%", scaleX,
      background: "linear-gradient(90deg,#34d399,#60a5fa,#f59e0b)",
      boxShadow: "0 0 10px rgba(52,211,153,0.6)",
    }} />
  );
}

/* ── Mockup: gerçekçi BMS dashboard önizlemesi ───────────────── */
function Mockup() {
  const { t, fmtPara, fmtFiyat } = useI18n();
  const navItems = [
    { label: t("nav.sim"), Icon: Home, active: true },
    { label: t("nav.epias"), Icon: Bolt, active: false },
    { label: t("nav.invest"), Icon: Coins, active: false },
    { label: t("nav.expert"), Icon: Chart, active: false },
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
      <ellipse cx="60" cy="118" rx="48" ry="8" fill="rgba(255,255,255,0.10)"/>
      {/* arka yüz */}
      <rect x="18" y="30" width="60" height="80" rx="2" fill="#94a3b8"/>
      {/* yan yüz */}
      <polygon points="78,30 102,18 102,98 78,110" fill="#64748b"/>
      {/* ön yüz */}
      <rect x="18" y="30" width="60" height="80" rx="2" fill="#cbd5e1"/>
      {/* çatı */}
      <polygon points="18,30 78,30 102,18 42,18" fill="rgba(255,255,255,0.10)"/>
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
    <motion.div className="hero-mock"
      initial={{ opacity: 0, y: 60 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4, duration: 0.75 }}
      style={{
        background: "#0d0d10", borderRadius: 20,
        boxShadow: "0 40px 80px -24px #00000040, 0 0 0 1px #e2e8f0",
        overflow: "hidden", display: "flex",
        maxWidth: 980, margin: "0 auto", textAlign: "left",
      }}>

      {/* ── Sol sidebar ──────────────────────────────── */}
      <div className="hero-mock-side" style={{
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

        {navItems.map(({ label, Icon, active }) => (
          <div key={label} style={{
            display: "flex", alignItems: "center", gap: 9,
            padding: "8px 10px", borderRadius: 8, fontSize: 12.5,
            background: active ? "#1e293b" : "transparent",
            color: active ? "#f8fafc" : "#94a3b8",
            cursor: "pointer",
          }}>
            <Icon size={14} />
            {label}
          </div>
        ))}

        <div style={{ marginTop: "auto", borderTop: "1px solid #1e293b", paddingTop: 12 }}>
          <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 6, padding: "0 10px" }}>{t("mock.config")}</div>
          {[[t("mock.cfgType"), t("mock.cfgTypeVal")], [t("mock.cfgFloor"), "5"], [t("mock.cfgFlats"), "12 / 15"], [t("mock.cfgBatt"), "24.4 kWh"]].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 10px", fontSize: 11, color: "#a1a1aa" }}>
              <span>{k}</span><span style={{ color: "#94a3b8", fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Ana içerik ───────────────────────────────── */}
      <div style={{ flex: 1, padding: "20px 22px", background: "#0a0a0c", overflow: "hidden" }}>
        {/* Başlık satırı */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, color: "#f4f4f5" }}>{t("mock.title")}</div>
            <div style={{ fontSize: 11.5, color: "#a1a1aa" }}>{t("mock.sub")}</div>
          </div>
          <div style={{
            background: "rgba(52,211,153,0.15)", color: "#4ade80", borderRadius: 999,
            padding: "4px 12px", fontSize: 11.5, fontWeight: 700,
            display: "inline-flex", alignItems: "center", gap: 6,
          }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 6px #22c55e" }} />
            {t("mock.running")}
          </div>
        </div>

        {/* Metrik kartlar */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, margin: "14px 0" }}>
          {[
            [Coins, t("mock.save"), "+" + fmtPara(312), "#4ade80"],
            [Battery, t("mock.soc"), "%68", "#60a5fa"],
            [Sun, t("mock.solar"), "18.4 kWh", "#fbbf24"],
            [Bolt, t("mock.now"), t("mock.discharging"), "#f87171"],
          ].map(([Icon, label, val, fg]) => (
            <div key={label} style={{ background: "rgba(255,255,255,0.05)", borderRadius: 12, padding: "12px 14px", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 10.5, color: "#a1a1aa", marginBottom: 4 }}>
                <span style={{ color: fg, display: "flex" }}><Icon size={13} /></span>{label}
              </div>
              <div style={{ fontSize: 17, fontWeight: 800, color: fg }}>{val}</div>
            </div>
          ))}
        </div>

        {/* İki sütun: 3D + grafik */}
        <div style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: 14 }}>
          {/* Mini bina + batarya göstergesi */}
          <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid #e2e8f0", padding: "10px 8px", display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <Building />
            <div style={{ fontSize: 10, color: "#a1a1aa", textAlign: "center" }}>{t("mock.panels")}<br/>{t("mock.installed")}</div>
            <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.10)", borderRadius: 999 }}>
              <div style={{ width: "68%", height: "100%", background: "#22c55e", borderRadius: 999 }}/>
            </div>
            <div style={{ fontSize: 10, color: "#4ade80", fontWeight: 700 }}>{t("mock.batt")} %68</div>
          </div>

          {/* Fiyat + SOC grafiği */}
          <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 12, border: "1px solid #e2e8f0", padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f4f4f5" }}>{t("mock.chartTitle")}</div>
              <div style={{ display: "flex", gap: 10, fontSize: 10 }}>
                <span style={{ color: "#f59e0b" }}>— {t("mock.legPrice")}</span>
                <span style={{ color: "#22c55e" }}>— {t("mock.legSoc")}</span>
                <span style={{ color: "#3b82f6" }}>▲ {t("mock.legCharge")}</span>
                <span style={{ color: "#ef4444" }}>▼ {t("mock.legDischarge")}</span>
              </div>
            </div>
            <svg viewBox={`0 0 ${W} ${H+10}`} style={{ width: "100%" }} role="img" aria-label="Fiyat ve SOC grafiği">
              {/* grid lines */}
              {[0.25,0.5,0.75].map(f => (
                <line key={f} x1="0" y1={H-f*H} x2={W} y2={H-f*H} stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
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
  const skyRef      = useRef(null);
  const moonRef     = useRef(null);
  const starsRef    = useRef(null);
  const glowRef     = useRef(null);
  const cityRef     = useRef(null);
  const groundRef   = useRef(null);
  const particleRef = useRef(null);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      if (skyRef.current)      skyRef.current.style.transform      = `translateY(${y * 0.5}px)`;
      if (moonRef.current)     moonRef.current.style.transform     = `translateY(${y * 0.42}px)`;
      if (starsRef.current)    starsRef.current.style.transform    = `translateY(${y * 0.32}px)`;
      if (glowRef.current)     glowRef.current.style.transform     = `translateY(${y * 0.2}px)`;
      if (cityRef.current)     cityRef.current.style.transform     = `translateY(${y * 0.16}px)`;
      if (groundRef.current)   groundRef.current.style.transform   = `translateY(${y * 0.05}px)`;
      if (particleRef.current) particleRef.current.style.transform = `translateY(${y * 0.28}px)`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // deterministik yıldız alanı
  const stars = Array.from({ length: 80 }, (_, i) => ({
    x: (i * 127.3) % 100,
    y: (i * 41.7) % 64,
    s: i % 6 === 0 ? 2.4 : 1.3,
    d: (i % 5) * 0.7,
    dur: 2.4 + (i % 4) * 0.8,
  }));

  // şehir silüeti — binalar
  const city = [
    { x: 20, w: 70, h: 150 }, { x: 100, w: 54, h: 205 }, { x: 165, w: 82, h: 168 },
    { x: 258, w: 60, h: 232 }, { x: 330, w: 92, h: 188 }, { x: 434, w: 64, h: 250 },
    { x: 510, w: 86, h: 208 }, { x: 608, w: 72, h: 272 }, { x: 692, w: 96, h: 198 },
    { x: 800, w: 60, h: 242 }, { x: 872, w: 100, h: 178 }, { x: 984, w: 70, h: 262 },
    { x: 1066, w: 86, h: 210 }, { x: 1164, w: 66, h: 244 }, { x: 1242, w: 92, h: 190 },
    { x: 1346, w: 78, h: 222 },
  ];

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", zIndex: 0, pointerEvents: "none" }}>
      {/* Gece göğü */}
      <div ref={skyRef} style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(130% 90% at 50% -15%, #0b1226 0%, #05070f 46%, #000000 100%)",
        willChange: "transform",
      }} />

      {/* Üstte yeşil enerji ışıması (aurora) */}
      <div ref={glowRef} style={{
        position: "absolute", top: "-25%", left: "50%", width: "95vw", height: "70vh",
        transform: "translateX(-50%)",
        background: "radial-gradient(circle, rgba(52,211,153,0.13) 0%, rgba(96,165,250,0.06) 40%, transparent 65%)",
        filter: "blur(30px)", willChange: "transform",
      }} />

      {/* Yıldızlar */}
      <div ref={starsRef} style={{ position: "absolute", inset: 0, willChange: "transform" }}>
        {stars.map((st, i) => (
          <div key={i} style={{
            position: "absolute", left: st.x + "%", top: st.y + "%",
            width: st.s, height: st.s, borderRadius: "50%", background: "#fff", opacity: 0.65,
            boxShadow: st.s > 2 ? "0 0 6px #fff" : "none",
            animation: `twinkle ${st.dur}s ease-in-out ${st.d}s infinite alternate`,
          }} />
        ))}
        {/* kayan yıldız */}
        <div style={{
          position: "absolute", top: "13%", left: "8%", width: 3, height: 3, borderRadius: "50%",
          background: "#fff", boxShadow: "0 0 8px 2px #ffffffcc", animation: "shoot 7s linear 2.5s infinite",
        }} />
      </div>

      {/* Ay */}
      <div ref={moonRef} style={{ position: "absolute", top: "10%", right: "13%", willChange: "transform" }}>
        <div style={{ position: "relative", width: 104, height: 104, animation: "moonBob 7s ease-in-out infinite" }}>
          <div style={{
            position: "absolute", inset: -28, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(191,219,254,0.30) 0%, transparent 70%)",
            animation: "moonGlow 5s ease-in-out infinite",
          }} />
          <div style={{
            position: "absolute", inset: 0, borderRadius: "50%",
            background: "radial-gradient(circle at 38% 34%, #f4f8ff, #c6d2ea)",
            boxShadow: "0 0 60px 10px rgba(199,210,232,0.35), inset -14px -10px 26px rgba(110,122,158,0.55)",
          }} />
          <div style={{ position: "absolute", top: "30%", left: "52%", width: 14, height: 14, borderRadius: "50%", background: "rgba(140,152,186,0.42)" }} />
          <div style={{ position: "absolute", top: "58%", left: "30%", width: 10, height: 10, borderRadius: "50%", background: "rgba(140,152,186,0.36)" }} />
          <div style={{ position: "absolute", top: "46%", left: "66%", width: 7, height: 7, borderRadius: "50%", background: "rgba(140,152,186,0.3)" }} />
        </div>
      </div>

      {/* Enerji partikülleri */}
      <div ref={particleRef} style={{ position: "absolute", inset: 0, willChange: "transform" }}>
        {[
          { x: "18%", y: "40%", d: 0, s: 8, c: "#34d399" },
          { x: "72%", y: "30%", d: 0.6, s: 6, c: "#60a5fa" },
          { x: "45%", y: "24%", d: 1.1, s: 10, c: "#fbbf24" },
          { x: "85%", y: "46%", d: 0.3, s: 7, c: "#34d399" },
          { x: "10%", y: "58%", d: 1.4, s: 5, c: "#a78bfa" },
          { x: "60%", y: "52%", d: 0.8, s: 9, c: "#60a5fa" },
        ].map((p, i) => (
          <div key={i} style={{
            position: "absolute", left: p.x, top: p.y, width: p.s, height: p.s, borderRadius: "50%",
            background: p.c, opacity: 0.8, boxShadow: `0 0 ${p.s * 3}px ${p.c}`,
            animation: `floatPart ${2.8 + i * 0.4}s ease-in-out ${p.d}s infinite alternate`,
          }} />
        ))}
      </div>

      {/* Şehir silüeti — ışıklı pencereler + glow'lu paneller */}
      <div ref={cityRef} style={{ position: "absolute", bottom: "15%", left: 0, right: 0, willChange: "transform" }}>
        <svg viewBox="0 0 1440 290" style={{ width: "100%", display: "block" }} preserveAspectRatio="xMidYMax slice">
          <defs>
            <linearGradient id="bld" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#121627" />
              <stop offset="1" stopColor="#070a13" />
            </linearGradient>
          </defs>
          {city.map((b, bi) => {
            const top = 290 - b.h;
            const cols = Math.max(2, Math.floor(b.w / 24));
            const rows = Math.floor(b.h / 26);
            const cw = (b.w - 16) / cols;
            const wins = [];
            for (let r = 0; r < rows; r++) {
              for (let c = 0; c < cols; c++) {
                const lit = ((bi * 5 + r * 3 + c * 7) % 5) < 2;
                const warm = ((bi + r + c) % 3) !== 0;
                wins.push(
                  <rect key={r + "-" + c}
                    x={b.x + 8 + c * cw} y={top + 14 + r * 22}
                    width={Math.max(4, Math.min(9, cw - 6))} height={11} rx={1}
                    fill={lit ? (warm ? "#fbbf24" : "#93c5fd") : "#1b2133"}
                    opacity={lit ? 0.9 : 0.45} />
                );
              }
            }
            return (
              <g key={bi}>
                <rect x={b.x} y={top} width={b.w} height={b.h} rx={2} fill="url(#bld)" stroke="rgba(255,255,255,0.06)" />
                {wins}
                {bi % 4 === 0 && [0, 1, 2].map((k) => (
                  <rect key={"p" + k} x={b.x + 8 + k * ((b.w - 16) / 3)} y={top - 7}
                    width={(b.w - 16) / 3 - 4} height={6} rx={1} fill="#60a5fa" opacity={0.8} />
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Zemin — koyu yansıma + ufuk çizgisi glow */}
      <div ref={groundRef} style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "24%",
        background: "linear-gradient(180deg, transparent, #04060c 45%, #000)", willChange: "transform" }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2,
          background: "linear-gradient(90deg, transparent, rgba(52,211,153,0.55), rgba(96,165,250,0.4), transparent)",
          filter: "blur(1px)" }} />
      </div>

      {/* Alttan sayfaya yumuşak geçiş (siyaha) */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 160,
        background: "linear-gradient(180deg, transparent, #000)" }} />

      <style>{`
        @keyframes twinkle { from { opacity: 0.15; } to { opacity: 0.9; } }
        @keyframes moonBob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        @keyframes moonGlow { 0%,100% { opacity: 0.7; transform: scale(1); } 50% { opacity: 1; transform: scale(1.08); } }
        @keyframes floatPart { 0% { transform: translateY(0); } 100% { transform: translateY(-18px); } }
        @keyframes shoot {
          0% { transform: translate(0,0); opacity: 0; }
          4% { opacity: 1; }
          22% { transform: translate(260px,130px); opacity: 0; }
          100% { opacity: 0; }
        }
        @media (prefers-reduced-motion: reduce) {
          *[style*="animation"] { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

function Hero() {
  const { t, fmtPara } = useI18n();
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
          <span className="eyebrow">
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px #34d399" }} />
            {t("lp.hero.badge")}
          </span>
          <h1 style={{ textShadow: "0 4px 40px rgba(52,211,153,0.15)" }}>
            <span style={{
              display: "inline-flex",
              width: "0.9em", height: "0.9em", borderRadius: "22%",
              background: "linear-gradient(135deg,#f59e0b,#22c55e)",
              color: "#fff", alignItems: "center", justifyContent: "center",
              fontSize: "0.5em", fontWeight: 800, marginInlineEnd: "0.22em",
              boxShadow: "0 4px 20px #22c55e44", verticalAlign: "0.12em",
            }}>AI</span>
            {t("lp.hero.titleFull")}
          </h1>
        </motion.div>
        <motion.p className="sub" style={{ margin: "22px auto 30px", maxWidth: 560 }}
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
          {t("lp.hero.sub")}
        </motion.p>
        <motion.div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }}>
          <Link className="btn btn-blue" to="/simulasyon">
            {t("lp.hero.cta")} <span className="arr"><Arrow size={14} /></span>
          </Link>
          <a className="btn btn-white" href="#features">{t("lp.hero.how")}</a>
        </motion.div>
        <motion.div style={{ display: "flex", gap: 22, justifyContent: "center", flexWrap: "wrap", margin: "26px 0 50px" }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
          <span className="chip" style={{ background: "var(--card)", border: "1px solid var(--line)", borderRadius: 999, padding: "8px 16px", backdropFilter: "blur(8px)" }}>
            <span style={{ color: "var(--amber)", display: "flex" }}><Star size={17} /></span> {t("lp.hero.chip1").replace("{d}", fmtPara(14))}
          </span>
          <span className="chip" style={{ background: "var(--card)", border: "1px solid var(--line)", borderRadius: 999, padding: "8px 16px", backdropFilter: "blur(8px)" }}>
            <span style={{ color: "var(--green)", display: "flex" }}><Shield size={17} /></span> {t("lp.hero.chip2")}
          </span>
          <span className="chip" style={{ background: "var(--card)", border: "1px solid var(--line)", borderRadius: 999, padding: "8px 16px", backdropFilter: "blur(8px)" }}>
            <span style={{ color: "var(--blue)", display: "flex" }}><Bolt size={17} /></span> {t("lp.hero.chip3")}
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
      <rect x="22" y="45" width="76" height="32" fill={hovered ? "#d1fae5" : "rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
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
      <rect x="10" y="45" width="100" height="30" fill={hovered ? "#d1fae5" : "rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
      {/* 2. kat */}
      <rect x="28" y="25" width="64" height="22" fill={hovered ? "#a7f3d0" : "rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
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
      <rect x="18" y="18" width="84" height="62" fill={hovered ? "#d1fae5" : "rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
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
      <rect x="12" y="22" width="44" height="58" fill={hovered?"#d1fae5":"rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
      <rect x="64" y="10" width="44" height="70" fill={hovered?"#a7f3d0":"rgba(255,255,255,0.10)"} style={{transition:"fill 0.3s"}}/>
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
  const tt = useT();
  const [hov, setHov] = useState(null);

  const tipler = [
    {
      id: "mustak", isim: tt("btype.Müstakil Ev"), color: "#22c55e",
      svg: (h) => <MustakilSvg hovered={h}/>,
      specs: [
        { label: tt("lp.bt.floor"), value: "1–2" },
        { label: tt("lp.bt.room"), value: "3–7" },
        { label: tt("lp.bt.roof"), value: "60–180 m²" },
        { label: tt("lp.bt.battery"), value: "5–15 kWh" },
      ],
      desc: tt("lp.bt.mustak.d"),
    },
    {
      id: "villa", isim: tt("btype.Villa"), color: "#3b82f6",
      svg: (h) => <VillaSvg hovered={h}/>,
      specs: [
        { label: tt("lp.bt.floor"), value: "2–3" },
        { label: tt("lp.bt.room"), value: "4–10" },
        { label: tt("lp.bt.roof"), value: "120–300 m²" },
        { label: tt("lp.bt.battery"), value: "10–25 kWh" },
      ],
      desc: tt("lp.bt.villa.d"),
    },
    {
      id: "apt", isim: tt("btype.Apartman"), color: "#8b5cf6",
      svg: (h) => <ApartmanSvg hovered={h}/>,
      specs: [
        { label: tt("lp.bt.floor"), value: "3–10" },
        { label: tt("lp.bt.flatPer"), value: "2–6" },
        { label: tt("lp.bt.elevator"), value: tt("lp.bt.optional") },
        { label: tt("lp.bt.battery"), value: "20–60 kWh" },
      ],
      desc: tt("lp.bt.apt.d"),
    },
    {
      id: "ofis", isim: tt("btype.Ofis Binası"), color: "#f59e0b",
      svg: (h) => <OfisSvg hovered={h}/>,
      specs: [
        { label: tt("lp.bt.floor"), value: "4–12" },
        { label: tt("lp.bt.unit"), value: "8–40" },
        { label: tt("lp.bt.hvac"), value: tt("lp.bt.central") },
        { label: tt("lp.bt.battery"), value: "40–120 kWh" },
      ],
      desc: tt("lp.bt.ofis.d"),
    },
  ];

  return (
    <section style={{ padding: "80px 0", background: "#0a0a0c" }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 52 }}>
          <span className="eyebrow">{tt("lp.bt.eyebrow")}</span>
          <h2>{tt("lp.bt.title")}</h2>
          <p className="sub" style={{ maxWidth: 480, margin: "12px auto 0" }}>{tt("lp.bt.sub")}</p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20 }}>
          {tipler.map((t, ti) => {
            const isHov = hov === t.id;
            return (
              <motion.div
                key={t.id}
                onMouseEnter={() => setHov(t.id)}
                onMouseLeave={() => setHov(null)}
                {...reveal(ti, 40)}
                whileHover={{ y: -6 }}
                style={{
                  background: isHov ? t.color + "1a" : "rgba(255,255,255,0.03)",
                  border: `1px solid ${isHov ? t.color : "rgba(255,255,255,0.10)"}`,
                  borderRadius: 20, padding: "32px 24px",
                  cursor: "default",
                  transition: "background 0.3s, border-color 0.3s, box-shadow 0.3s",
                  boxShadow: isHov ? `0 16px 50px -12px ${t.color}55` : "none",
                }}>
                {/* SVG bina */}
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 20, height: 88 }}>
                  {t.svg(isHov)}
                </div>

                {/* başlık */}
                <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 4, color: isHov ? t.color : "#f4f4f5", transition: "color 0.3s" }}>
                  {t.isim}
                </div>
                <div style={{ fontSize: 13.5, color: "#a1a1aa", marginBottom: 20, lineHeight: 1.6 }}>{t.desc}</div>

                {/* spec grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 12px" }}>
                  {t.specs.map(s => (
                    <div key={s.label} style={{
                      background: isHov ? t.color + "12" : "rgba(255,255,255,0.06)",
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
  const { t, fmtPara } = useI18n();
  const cards = [
    {
      good: false, accent: "#f87171", Icon: X, tag: t("lp.problem.before"),
      title: t("lp.problem.beforeTitle"),
      items: ["lp.problem.b1", "lp.problem.b2", "lp.problem.b3", "lp.problem.b4"],
      stats: [["%40+", t("lp.problem.stat1")], [t("lp.problem.constant"), t("lp.problem.stat2")]],
    },
    {
      good: true, accent: "#34d399", Icon: Check, tag: t("lp.problem.after"),
      title: t("lp.problem.afterTitle"),
      items: ["lp.problem.a1", "lp.problem.a2", "lp.problem.a3", "lp.problem.a4"],
      stats: [["+" + fmtPara(14), t("lp.problem.stat3")], ["7/24", t("lp.problem.stat4")]],
    },
  ];
  return (
    <section style={{ textAlign: "center" }}>
      <div className="container">
        <motion.h2 {...fadeUp} style={{ marginBottom: 40 }}>{t("lp.problem.title")}</motion.h2>
        <div className="cmp-grid">
          {cards.map((c, i) => (
            <motion.article key={i} {...reveal(i, 40)}
              className={"cmp-card" + (c.good ? " good" : "")}
              style={{ "--c": c.accent, "--c-soft": c.accent + "22" }}>
              <div className="cmp-head">
                <span className="cmp-badge"><c.Icon size={20} /></span>
                <span className="cmp-tag">{c.tag}</span>
              </div>
              <h3>{c.title}</h3>
              <div style={{ marginBottom: 6 }}>
                {c.items.map((k) => (
                  <div className="cmp-tick" key={k}>
                    <span className="ic"><c.Icon size={17} /></span>{t(k).replace("{d}", fmtPara(14)).replace("{y}", fmtPara(5000))}
                  </div>
                ))}
              </div>
              <div className="cmp-stats">
                {c.stats.map(([n, d]) => (
                  <div key={d}>
                    <div className="num">{n}</div>
                    <div className="lbl">{d}</div>
                  </div>
                ))}
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Ürün arayüzü paneli — aktif özelliğe göre değişir ────────── */
const PANEL_META = [
  { title: "show.solar.title", color: "#f59e0b" },
  { title: "show.batt.title", color: "#22c55e" },
  { title: "show.price.title", color: "#3b82f6" },
  { title: "show.outage.title", color: "#ef4444" },
  { title: "show.agent.title", color: "#8b5cf6" },
];

function PanelKpi({ label, value, color }) {
  return (
    <div style={{ background: "#ffffff08", border: "1px solid #ffffff12", borderRadius: 12, padding: "10px 14px", flex: 1, minWidth: 100 }}>
      <div style={{ fontSize: 11, color: "#8b95a7" }}>{label}</div>
      <div style={{ fontSize: 17, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}

function SolarView() {
  const t = useT();
  return (
    <div>
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <PanelKpi label={t("show.solar.instant")} value="18.4 kW" color="#fbbf24" />
        <PanelKpi label={t("show.solar.dayTotal")} value="126 kWh" color="#fff" />
        <PanelKpi label={t("show.solar.selfUse")} value="%74" color="#22c55e" />
      </div>
      <svg viewBox="0 0 460 170" style={{ width: "100%" }}>
        <defs>
          <linearGradient id="solarG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1="0" y1={40 * i + 10} x2="460" y2={40 * i + 10} stroke="#ffffff0d" />
        ))}
        <motion.path
          d="M0,160 C40,158 70,140 100,110 C130,80 160,40 230,32 C300,40 330,80 360,110 C390,140 420,158 460,160 L460,170 L0,170 Z"
          fill="url(#solarG)"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }} />
        <motion.path
          d="M0,160 C40,158 70,140 100,110 C130,80 160,40 230,32 C300,40 330,80 360,110 C390,140 420,158 460,160"
          fill="none" stroke="#fbbf24" strokeWidth="3" strokeLinecap="round"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1, ease: "easeInOut" }} />
        <motion.circle r="6" fill="#fbbf24" stroke="#0b1220" strokeWidth="3"
          initial={{ cx: 0, cy: 160, opacity: 0 }} animate={{ cx: 230, cy: 32, opacity: 1 }}
          transition={{ duration: 1.1, ease: "easeInOut" }} />
        <text x="8" y="165" fontSize="10" fill="#8b95a7">06:00</text>
        <text x="222" y="24" fontSize="10" fill="#fbbf24" fontWeight="700">13:00 {t("show.solar.peak")}</text>
        <text x="425" y="165" fontSize="10" fill="#8b95a7">21:00</text>
      </svg>
    </div>
  );
}

function BatteryView() {
  const t = useT();
  const hours = [0.7, 0.9, 0.8, 0.6, 0, 0, -0.5, -0.8, 0, 0.4, 0.6, 0, -0.9, -0.7, 0, 0.3];
  return (
    <div style={{ display: "flex", gap: 22, alignItems: "center" }}>
      <div style={{ position: "relative", width: 150, flexShrink: 0 }}>
        <svg viewBox="0 0 140 140" style={{ width: "100%" }}>
          <circle cx="70" cy="70" r="56" fill="none" stroke="#ffffff12" strokeWidth="13" />
          <motion.circle cx="70" cy="70" r="56" fill="none" stroke="#22c55e" strokeWidth="13"
            strokeLinecap="round" strokeDasharray="352" transform="rotate(-90 70 70)"
            initial={{ strokeDashoffset: 352 }} animate={{ strokeDashoffset: 352 * (1 - 0.68) }}
            transition={{ duration: 1.2, ease: "easeOut" }} />
          <text x="70" y="66" textAnchor="middle" fontSize="26" fontWeight="800" fill="#fff">%68</text>
          <text x="70" y="86" textAnchor="middle" fontSize="10.5" fill="#8b95a7">{t("show.batt.full")}</text>
        </svg>
        <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.6 }}
          style={{ position: "absolute", top: 4, right: 10, width: 10, height: 10, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 12px #22c55e" }} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: "#8b95a7", marginBottom: 8 }}>{t("show.batt.plan")}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 3, height: 90 }}>
          {hours.map((v, i) => (
            <motion.div key={i}
              initial={{ height: 0 }} animate={{ height: Math.max(Math.abs(v) * 76, 4) }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
              style={{
                flex: 1, borderRadius: 3,
                background: v > 0 ? "#22c55e" : v < 0 ? "#ef4444" : "#ffffff1c",
                alignSelf: v >= 0 ? "flex-end" : "flex-start",
              }} />
          ))}
        </div>
        <div style={{ display: "flex", gap: 14, marginTop: 10, fontSize: 11.5, color: "#8b95a7" }}>
          <span><span style={{ color: "#22c55e" }}>■</span> {t("show.batt.charge")}</span>
          <span><span style={{ color: "#ef4444" }}>■</span> {t("show.batt.discharge")}</span>
        </div>
      </div>
    </div>
  );
}

function EpiasView() {
  const { t, fmtPara } = useI18n();
  const bars = [42, 38, 35, 32, 30, 33, 40, 55, 68, 62, 52, 46, 44, 48, 55, 64, 78, 92, 100, 88, 74, 62, 52, 45];
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <span style={{ fontSize: 24, fontWeight: 800, color: "#fff" }}>{fmtPara(2412)}</span>
          <span style={{ fontSize: 12.5, color: "#8b95a7" }}> {t("show.price.now")}</span>
        </div>
        <motion.span animate={{ opacity: [1, 0.5, 1] }} transition={{ repeat: Infinity, duration: 1.8 }}
          style={{ background: "#22c55e22", color: "#4ade80", border: "1px solid #22c55e55", borderRadius: 999, padding: "4px 14px", fontSize: 12.5, fontWeight: 700 }}>
          ● {t("show.price.live")}
        </motion.span>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 130 }}>
        {bars.map((h, i) => (
          <motion.div key={i}
            initial={{ height: 0 }} animate={{ height: `${h}%` }}
            transition={{ delay: i * 0.035, duration: 0.4 }}
            style={{
              flex: 1, borderRadius: 3,
              background: h > 80 ? "#ef4444" : h < 40 ? "#22c55e" : "#ffffff22",
            }} />
        ))}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10.5, color: "#8b95a7", marginTop: 8 }}>
        <span>00:00</span><span style={{ color: "#4ade80" }}>▲ {t("show.price.cheap")}</span>
        <span style={{ color: "#f87171" }}>▼ {t("show.price.exp")}</span><span>23:00</span>
      </div>
    </div>
  );
}

function OutageView() {
  const t = useT();
  const rows = [[t("show.outage.critical"), 100], [t("show.outage.lighting"), 100], [t("show.outage.outlets"), 82], [t("show.outage.ev"), 0]];
  return (
    <div>
      <motion.div animate={{ opacity: [1, 0.6, 1] }} transition={{ repeat: Infinity, duration: 1 }}
        style={{ background: "#ef444418", border: "1px solid #ef444455", borderRadius: 12, padding: "10px 16px", color: "#f87171", fontWeight: 700, fontSize: 14, marginBottom: 16, display: "flex", gap: 10, alignItems: "center" }}>
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444", boxShadow: "0 0 12px #ef4444" }} />
        {t("show.outage.alert")}
      </motion.div>
      {rows.map(([l, p], i) => (
        <div key={l} style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, color: "#c3cad6", marginBottom: 5 }}>
            <span>{l}</span><span style={{ fontWeight: 700, color: p === 0 ? "#8b95a7" : p === 100 ? "#4ade80" : "#fbbf24" }}>{p === 0 ? t("show.outage.suspended") : `%${p}`}</span>
          </div>
          <div style={{ background: "#ffffff10", borderRadius: 999, height: 8, overflow: "hidden" }}>
            <motion.div initial={{ width: 0 }} animate={{ width: `${p}%` }}
              transition={{ delay: 0.2 + i * 0.15, duration: 0.7, ease: "easeOut" }}
              style={{ height: "100%", borderRadius: 999, background: p === 100 ? "#22c55e" : p > 0 ? "#fbbf24" : "transparent" }} />
          </div>
        </div>
      ))}
      <div style={{ fontSize: 12.5, color: "#8b95a7", marginTop: 14 }}>
        {t("show.outage.autonomy")}: <b style={{ color: "#fff" }}>{t("show.outage.autonomyVal")}</b> · {t("show.outage.gen")}: <b style={{ color: "#4ade80" }}>{t("show.outage.ready")}</b>
      </div>
    </div>
  );
}

function AgentView() {
  const { t, fmtPara } = useI18n();
  const decisions = [
    ["03:00", t("show.agent.store"), "#22c55e", t("show.agent.d1")],
    ["13:00", t("show.agent.wait"), "#8b95a7", t("show.agent.d2")],
    ["18:00", t("show.agent.use"), "#ef4444", t("show.agent.d3")],
    ["22:00", t("show.agent.store"), "#22c55e", t("show.agent.d4")],
  ];
  return (
    <div>
      {decisions.map(([saat, k, c, d], i) => (
        <motion.div key={saat}
          initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 + i * 0.16, duration: 0.4 }}
          style={{ display: "flex", alignItems: "center", gap: 12, background: "#ffffff07", border: "1px solid #ffffff10", borderRadius: 12, padding: "11px 15px", marginBottom: 10 }}>
          <span style={{ fontFamily: "monospace", fontSize: 13, color: "#8b95a7", width: 44 }}>{saat}</span>
          <span style={{ background: c + "22", color: c, borderRadius: 999, padding: "3px 13px", fontSize: 12, fontWeight: 800, letterSpacing: "0.04em" }}>{k}</span>
          <span style={{ fontSize: 12.5, color: "#c3cad6" }}>{d}</span>
        </motion.div>
      ))}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.85 }}
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg,#22c55e18,#8b5cf618)", border: "1px solid #ffffff14", borderRadius: 12, padding: "13px 16px", marginTop: 4 }}>
        <span style={{ fontSize: 13, color: "#c3cad6" }}>{t("show.agent.net")}</span>
        <span style={{ fontSize: 21, fontWeight: 800, color: "#4ade80" }}>+{fmtPara(14.4)}</span>
      </motion.div>
    </div>
  );
}

function ProductPanel({ active }) {
  const t = useT();
  const meta = PANEL_META[active];
  const views = [<SolarView key="s" />, <BatteryView key="b" />, <EpiasView key="e" />, <OutageView key="o" />, <AgentView key="a" />];
  return (
    <div style={{
      background: "linear-gradient(150deg,#0d1526,#0b1220 60%)",
      border: "1px solid #ffffff14",
      borderRadius: 24,
      boxShadow: `0 40px 90px -30px #000c, 0 0 0 1px ${meta.color}22, 0 0 90px -30px ${meta.color}55`,
      overflow: "hidden",
      transition: "box-shadow 0.6s",
    }}>
      {/* pencere başlığı */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 18px", borderBottom: "1px solid #ffffff0e" }}>
        <span style={{ display: "flex", gap: 6 }}>
          {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
            <span key={c} style={{ width: 11, height: 11, borderRadius: "50%", background: c, opacity: 0.85 }} />
          ))}
        </span>
        <motion.span key={active}
          initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
          style={{ fontSize: 13.5, fontWeight: 700, color: "#e6ebf2" }}>
          {t(meta.title)}
        </motion.span>
        <span style={{ marginLeft: "auto", width: 8, height: 8, borderRadius: "50%", background: meta.color, boxShadow: `0 0 10px ${meta.color}`, transition: "background 0.5s" }} />
      </div>
      {/* içerik */}
      <div style={{ padding: "22px 22px 26px", minHeight: 260 }}>
        <motion.div key={active}
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.32 }}>
          {views[active]}
        </motion.div>
      </div>
    </div>
  );
}

/* ── Showcase — otomatik dönen etkileşimli özellik listesi ────── */
const CYCLE_MS = 4200;
function StickyShowcase() {
  const t = useT();
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  const features = [
    { Icon: Sun, color: "#f59e0b", title: t("lp.feat.solar.t"), desc: t("lp.feat.solar.d") },
    { Icon: Battery, color: "#22c55e", title: t("lp.feat.batt.t"), desc: t("lp.feat.batt.d") },
    { Icon: Bolt, color: "#3b82f6", title: t("lp.feat.price.t"), desc: t("lp.feat.price.d") },
    { Icon: Alert, color: "#ef4444", title: t("lp.feat.outage.t"), desc: t("lp.feat.outage.d") },
    { Icon: Brain, color: "#8b5cf6", title: t("lp.feat.agent.t"), desc: t("lp.feat.agent.d") },
  ];

  // Otomatik ilerleme — her adımda sıfırlanır, hover'da durur.
  useEffect(() => {
    if (paused) return;
    const id = setTimeout(() => setActive((a) => (a + 1) % features.length), CYCLE_MS);
    return () => clearTimeout(id);
  }, [active, paused, features.length]);

  return (
    <section id="features" style={{ padding: "100px 0", background: "#08080a" }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 56 }}>
          <span className="eyebrow">{t("lp.feat.eyebrow")}</span>
          <h2>{t("lp.feat.title")}</h2>
          <p className="sub" style={{ maxWidth: 480, margin: "12px auto 0" }}>{t("lp.feat.sub")}</p>
        </motion.div>

        <motion.div {...fadeUp}
          className="showcase-grid"
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          {/* Sol — canlı ürün paneli */}
          <div className="showcase-sticky">
            <ProductPanel active={active} />
          </div>

          {/* Sağ — tıklanabilir özellik adımları */}
          <div className="feat-list">
            {features.map((f, i) => {
              const on = active === i;
              return (
                <button
                  key={i}
                  type="button"
                  className="feat-step"
                  data-on={on}
                  onClick={() => setActive(i)}
                  aria-pressed={on}
                  style={{ "--c": f.color, "--c-soft": f.color + "1e" }}
                >
                  <span className="feat-ic"><f.Icon size={22} /></span>
                  <div style={{ flex: 1 }}>
                    <div className="feat-t">{f.title}</div>
                    <AnimatePresence initial={false}>
                      {on && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.32, ease: EASE }}
                          style={{ overflow: "hidden" }}
                        >
                          <p className="feat-d" style={{ marginTop: 8 }}>{f.desc}</p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  {/* otomatik ilerleme çubuğu */}
                  {on && (
                    <motion.span
                      key={active + (paused ? "-p" : "")}
                      className="feat-bar"
                      initial={{ width: "0%" }}
                      animate={{ width: paused ? "0%" : "100%" }}
                      transition={{ duration: paused ? 0 : CYCLE_MS / 1000, ease: "linear" }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

/* ── İstatistikler ───────────────────────────────────────────── */
function Stats() {
  const { t, fmtPara } = useI18n();
  const rows = [
    [t("lp.stats.1l"), "~" + fmtPara(14), t("lp.stats.1d"), "#60a5fa", Brain],
    [t("lp.stats.2l"), fmtPara(5000) + "+", t("lp.stats.2d"), "#34d399", Bolt],
    [t("lp.stats.3l"), t("lp.stats.mins"), t("lp.stats.3d"), "#a78bfa", Chart],
    [t("lp.stats.4l"), t("lp.stats.hrs"), t("lp.stats.4d"), "#38bdf8", Gauge],
    [t("lp.stats.5l"), t("lp.stats.nothing"), t("lp.stats.5d"), "#f59e0b", Cube],
  ];
  return (
    <section id="stats">
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 44 }}>
          <span className="eyebrow">{t("lp.stats.eyebrow")}</span>
          <h2>{t("lp.stats.title")}</h2>
          <p className="sub" style={{ margin: "12px auto 0", maxWidth: 520 }}>{t("lp.stats.sub")}</p>
        </motion.div>
        <div className="stat-grid">
          {rows.map(([l, n, d, renk, Icon], i) => (
            <motion.div key={l} {...reveal(i, 36)}
              className="stat-tile" style={{ "--c": renk, "--c-soft": renk + "22" }}>
              <span className="stat-badge" style={{ background: `linear-gradient(135deg, ${renk}, ${renk}bb)` }}>
                <Icon size={22} />
              </span>
              <div className="num">{n}</div>
              <div className="stat-label">{l}</div>
              <div className="stat-desc">{d}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Kullanım senaryoları ─────────────────────────────────────── */
function UseCases() {
  const { t, fmtPara } = useI18n();
  const cases = [
    [Home, "#3b82f6", t("lp.use.1t"), t("lp.use.1d"), "+" + fmtPara(5200) + "/" + t("unit.year"), t("lp.use.1m")],
    [Cube, "#22c55e", t("lp.use.2t"), t("lp.use.2d"), "%40", t("lp.use.2m")],
    [Chart, "#f97316", t("lp.use.3t"), t("lp.use.3d"), "3–6 " + t("unit.year"), t("lp.use.3m")],
    [Brain, "#f59e0b", t("lp.use.4t"), t("lp.use.4d"), "", t("lp.use.4m")],
  ];
  return (
    <section id="use-cases">
      <div className="container">
        <motion.div {...fadeUp} style={{ textAlign: "center", marginBottom: 44 }}>
          <span className="eyebrow">{t("lp.use.eyebrow")}</span>
          <h2>{t("lp.use.title")}</h2>
        </motion.div>
        <div className="use-grid">
          {cases.map(([Icon, renk, baslik, d, m, md], i) => (
            <motion.article
              key={baslik}
              {...reveal(i, 40)}
              className="use-card"
              style={{ "--c": renk, "--c-soft": renk + "22" }}
            >
              {/* üst satır: rozet + indeks */}
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20 }}>
                <span className="use-badge" style={{ background: `linear-gradient(135deg, ${renk}, ${renk}bb)` }}>
                  <Icon size={25} />
                </span>
                <span className="use-index">{String(i + 1).padStart(2, "0")} / {String(cases.length).padStart(2, "0")}</span>
              </div>

              <h3 style={{ marginBottom: 10 }}>{baslik}</h3>
              <p className="sub" style={{ fontSize: 15.5, lineHeight: 1.65, marginBottom: 22 }}>{d}</p>

              {/* metrik / etiket */}
              <div className="use-metric">
                {m ? (
                  <>
                    <span className="num">{m}</span>
                    <span className="lbl">{md}</span>
                  </>
                ) : (
                  <span className="use-tag"><Check size={14} /> {md}</span>
                )}
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Mimari quote ─────────────────────────────────────────────── */
function TechQuote() {
  const t = useT();
  return (
    <section style={{ paddingTop: 20 }}>
      <div className="container">
        <motion.div {...fadeUp} className="card" style={{ padding: "44px 32px", textAlign: "center" }}>
          <div style={{ display: "flex", gap: 20, justifyContent: "center", flexWrap: "wrap", marginBottom: 24 }}>
            {["lp.quote.c1", "lp.quote.c2", "lp.quote.c3", "lp.quote.c4"].map((c) => (
              <span key={c} className="eyebrow" style={{ marginBottom: 0 }}>{t(c)}</span>
            ))}
          </div>
          <blockquote style={{ fontSize: "clamp(18px,2.4vw,26px)", fontWeight: 700, maxWidth: 720, margin: "0 auto 22px", letterSpacing: "-0.01em" }}>
            {t("lp.quote.text")}
          </blockquote>
          <div style={{ fontWeight: 700 }}>{t("lp.quote.by")}</div>
        </motion.div>
      </div>
    </section>
  );
}

/* ── SSS ─────────────────────────────────────────────────────── */
function Faq() {
  const { t, fmtPara } = useI18n();
  const qs = [
    [t("lp.faq.q1"), t("lp.faq.a1")],
    [t("lp.faq.q2"), t("lp.faq.a2").replace("{d}", fmtPara(14)).replace("{y}", fmtPara(5000))],
    [t("lp.faq.q3"), t("lp.faq.a3")],
    [t("lp.faq.q4"), t("lp.faq.a4")],
    [t("lp.faq.q5"), t("lp.faq.a5")],
  ];
  const [open, setOpen] = useState(0);
  return (
    <section id="faq">
      <div className="container grid grid-2" style={{ alignItems: "start" }}>
        <motion.div {...fadeUp}>
          <h2 style={{ maxWidth: 420 }}>{t("lp.faq.title")}</h2>
          <p className="sub" style={{ margin: "12px 0 26px", maxWidth: 400 }}>{t("expert.sub")}</p>
          <div className="card" style={{ maxWidth: 380 }}>
            <p style={{ fontSize: 19, fontWeight: 700, marginBottom: 8 }}>{t("lp.faq.title")}</p>
            <a className="btn btn-dark" href="https://github.com/isambais/SmartHome-EnergyRL/issues" target="_blank" rel="noreferrer" style={{ padding: "11px 20px", fontSize: 14, marginTop: 10 }}>
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
  const t = useT();
  return (
    <section style={{
      background: "linear-gradient(135deg, #0d1117 0%, #1a2332 50%, #0f2417 100%)",
      textAlign: "center", padding: "110px 0",
    }}>
      <div className="container">
        <motion.div {...fadeUp} style={{ color: "#e6edf3" }}>
          <h2 style={{ color: "#fff", marginTop: 16 }}>{t("lp.cta.title")}</h2>
          <p style={{ color: "#8b949e", margin: "14px auto 30px", maxWidth: 480, fontSize: 18 }}>{t("lp.cta.sub")}</p>
          <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
            <Link className="btn btn-blue" to="/simulasyon">
              {t("lp.cta.btn")} <span className="arr"><Arrow size={14} /></span>
            </Link>
            <a className="btn" href="https://github.com/isambais/SmartHome-EnergyRL" target="_blank" rel="noreferrer"
              style={{ background: "#21262d", color: "#e6edf3", border: "1px solid #30363d" }}>
              GitHub
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <div className="landing">
      <ScrollProgress />
      <TopNav />
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
    </div>
  );
}
