import { AnimatePresence, motion, useSpring } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  Area, ComposedChart, CartesianGrid, Line, ResponsiveContainer,
  Scatter, Tooltip, XAxis, YAxis, ReferenceLine,
} from "recharts";
import { api } from "../api.js";
import Building from "../components/Building.jsx";
import { useApp } from "../state.jsx";
import { AYLAR_FULL, useI18n } from "../i18n.jsx";

/* ══ Tek design system — token'lar ═══════════════════════════════
   Olgun/derin koyu palet + canlı ama okunur accent'ler. */
const TK = {
  bg: "#080B12",
  panel: "rgba(255,255,255,0.022)",
  panelSolid: "#0C111B",
  card: "rgba(255,255,255,0.035)",
  line: "rgba(255,255,255,0.07)",
  line2: "rgba(255,255,255,0.12)",
  fg: "#E7ECF3",
  muted: "#8B97A8",
  faint: "#5A6675",
  solar: "#F5A623",   // sıcak amber
  battery: "#2FD07A", // canlı yeşil
  grid: "#3B9EFF",    // elektrik mavisi
  price: "#FF8A4C",   // turuncu
  danger: "#F0553B",  // uyarı
  ai: "#8B93F8",      // indigo
  mono: "'SF Mono','Fira Code',ui-monospace,monospace",
};

/* ── Inline SVG icon sistemi ─────────────────────────────────── */
const I = ({ d, size = 14, sw = 1.6 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"
    style={{ flexShrink: 0 }}>
    <path d={d} />
  </svg>
);

const ICO = {
  solar:    "M12 3v1m0 16v1M4.22 4.22l.7.7m12.16 12.16.7.7M3 12h1m16 0h1M4.22 19.78l.7-.7M18.36 5.64l.7-.7M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  battery:  "M6 7H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2",
  hvac:     "M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 22 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2",
  elevator: "M7 16V4m0 0L3 8m4-4 4 4M17 8v12m0 0 4-4m-4 4-4-4",
  pump:     "M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0m9-4v8m0-8c-2 0-4 1.5-4 4s2 4 4 4",
  ev:       "M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2h-2M14 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0M5 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0",
  camera:   "M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3L14.5 4zm-2.5 9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  heater:   "M12 22V12M12 12C12 7 7 5 7 5s5 2 5 7M12 12c0-5 5-7 5-7s-5 2-5 7M3 22h18",
  generator:"M13 2 3 14h9l-1 8 10-12h-9l1-8z",
  clock:    "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zm0-10V7m0 5 3 3",
  sun:      "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42",
  leaf:     "M6.4 16c4.8-1.6 8-5.6 8-11.2 0 5.6 3.2 9.6 3.2 14.4-4 0-8-1.6-9.6-4.8C7.2 17.6 6.4 18.4 4 20",
  snowflake:"M12 2v20M2 12h20M4.93 4.93l14.14 14.14M19.07 4.93 4.93 19.07",
  zap:      "M13 2 3 14h9l-1 8 10-12h-9l1-8z",
  grid:     "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
  agent:    "M12 2a5 5 0 0 1 5 5v3a5 5 0 0 1-10 0V7a5 5 0 0 1 5-5zm0 15c-5 0-8 2.5-8 4h16c0-1.5-3-4-8-4z",
  building: "M6 2h12l2 4H4L6 2zM3 22h18V6H3v16zM9 11h2m4 0h2M9 16h2m4 0h2",
  chevron:  "M6 9l6 6 6-6",
  sunrise:  "M12 18a4 4 0 0 0-8 0M12 2v7m-3-4 3-3 3 3M2 18h2m16 0h2M4.9 12.9l1.4 1.4m11.4-1.4-1.4 1.4",
  export:   "M12 19V5m-7 7 7-7 7 7",
};

/* ── Animasyonlu sayı — durum değişiminde yumuşak geçiş ───────── */
function Num({ value, fmt }) {
  const mv = useSpring(value ?? 0, { stiffness: 120, damping: 24, restDelta: 0.01 });
  const [d, setD] = useState(value ?? 0);
  useEffect(() => { mv.set(value ?? 0); }, [value, mv]);
  useEffect(() => mv.on("change", (v) => setD(v)), [mv]);
  return <>{fmt ? fmt(d) : Math.round(d)}</>;
}

const Dot = ({ on, color }) => (
  <span style={{
    display: "inline-block", width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
    background: on ? (color || TK.battery) : "#334155",
    boxShadow: on ? `0 0 6px ${color || TK.battery}` : "none",
  }} />
);

/* ── Durum hesaplayıcılar (mevcut veriden — fake yok) ─────────── */
function solarStatus(kw, maxKw) {
  if (kw <= 0.1) return "s2.st.solarNone";
  const rt = maxKw > 0 ? kw / maxKw : 0;
  return rt > 0.6 ? "s2.st.solarHigh" : rt > 0.3 ? "s2.st.solarMid" : "s2.st.solarLow";
}
function loadStatus(kw, maxKw) {
  const rt = maxKw > 0 ? kw / maxKw : 0;
  return rt > 0.6 ? "s2.st.loadHigh" : rt > 0.33 ? "s2.st.loadMid" : "s2.st.loadLow";
}
function battStatus(soc) {
  return soc >= 0.8 ? "s2.st.battFull" : soc >= 0.4 ? "s2.st.battMid" : "s2.st.battLow";
}
function gridStatus(net) {
  if (net == null) return "s2.st.balanced";
  return net < -0.05 ? "s2.st.exp" : net > 0.05 ? "s2.st.imp" : "s2.st.balanced";
}
function priceStatus(p) {
  return p > 1200 ? "s2.st.priceHigh" : p > 700 ? "s2.st.priceMid" : "s2.st.priceLow";
}

/* ══ KPI Kartları — değer + insan-dili durum ══════════════════════ */
function KpiCards({ r, cfg, saat, maxSolar, maxLoad, paraCevir, fiyatBirimi, locale, t }) {
  if (!r) return (
    <div className="kpi-7-grid">
      {Array(7).fill(0).map((_, i) => (
        <div key={i} style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 12, height: 72 }} />
      ))}
    </div>
  );
  const socPct = Math.round(r.soc * 100);
  const net = r.net_kwh;
  const gridMag = net != null ? Math.abs(net) : 0;
  const exporting = net != null && net < -0.05;
  const priceCol = r.fiyat_tl_mwh > 1200 ? TK.danger : r.fiyat_tl_mwh > 700 ? TK.solar : TK.battery;

  const items = [
    { label: t("s2.kpi.time"), icon: "clock", color: TK.fg,
      text: String(saat).padStart(2, "0") + ":00", status: null },
    { label: t("s2.kpi.solar"), icon: "solar", color: r.gunes_kw > 0.1 ? TK.solar : TK.faint,
      value: r.gunes_kw, fmt: (v) => v.toFixed(1) + " kW", status: t(solarStatus(r.gunes_kw, maxSolar)) },
    { label: t("s2.kpi.load"), icon: "zap", color: TK.grid,
      value: r.talep_kw, fmt: (v) => v.toFixed(1) + " kW", status: t(loadStatus(r.talep_kw, maxLoad)) },
    { label: t("s2.kpi.battery"), icon: "battery",
      color: socPct > 60 ? TK.battery : socPct > 25 ? TK.solar : TK.danger,
      value: socPct, fmt: (v) => Math.round(v) + "%", status: t(battStatus(r.soc)) },
    { label: exporting ? t("s2.kpi.gridExp") : t("s2.kpi.gridImp"), icon: exporting ? "export" : "grid",
      color: exporting ? TK.battery : TK.muted,
      value: gridMag, fmt: (v) => (exporting ? "+" : "") + v.toFixed(1) + " kW",
      status: t(gridStatus(net)) },
    { label: t("s2.kpi.price"), icon: "zap", color: priceCol,
      value: paraCevir ? paraCevir(r.fiyat_tl_mwh) : r.fiyat_tl_mwh,
      fmt: (v) => Math.round(v).toLocaleString(locale) + " " + (fiyatBirimi || "TL/MWh"),
      status: t(priceStatus(r.fiyat_tl_mwh)) },
    { label: t("s2.kpi.units"), icon: "building", color: TK.grid,
      text: `${cfg.aktif_daire}/${cfg.kat * cfg.daire_per_kat}`, status: t("s2.st.units") },
  ];

  return (
    <div className="kpi-7-grid">
      {items.map((it, i) => (
        <motion.div key={it.label + i}
          initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.04, duration: 0.3 }}
          style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 12,
            padding: "12px 14px", minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 6,
            fontSize: 9.5, letterSpacing: ".08em", textTransform: "uppercase", color: TK.faint, fontWeight: 600 }}>
            <span style={{ color: it.color, opacity: .8, display: "flex" }}><I d={ICO[it.icon]} size={11} /></span>
            {it.label}
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: it.color, lineHeight: 1.05,
            fontVariantNumeric: "tabular-nums", letterSpacing: "-.02em",
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {it.text != null ? it.text : <Num value={it.value} fmt={it.fmt} />}
          </div>
          {it.status && (
            <div style={{ fontSize: 10.5, color: TK.muted, marginTop: 4, fontWeight: 500,
              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {it.status}
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

/* ══ Canlı Enerji Durumu — tek cümlelik özet (3D üstünde) ════════ */
function LiveStatus({ r, maxSolar, maxLoad, t }) {
  if (!r) return null;
  const parts = [
    t(solarStatus(r.gunes_kw, maxSolar)),
    t(loadStatus(r.talep_kw, maxLoad)),
    t(battStatus(r.soc)),
    t(gridStatus(r.net_kwh)),
  ];
  return (
    <motion.div key={parts.join()} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}
      style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 14px",
        background: "rgba(8,11,18,0.55)", borderBottom: `1px solid ${TK.line}` }}>
      <span style={{ fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", color: TK.faint,
        fontWeight: 700, flexShrink: 0 }}>{t("cc.liveStatus")}</span>
      <span style={{ fontSize: 12.5, color: TK.fg, fontWeight: 500, whiteSpace: "nowrap",
        overflow: "hidden", textOverflow: "ellipsis" }}>
        {parts.join("  ·  ")}
      </span>
    </motion.div>
  );
}

/* ══ Bina Sistemi Kartı (kompakt 2-kolon) ═══════════════════════ */
function SysCard({ id, icon, name, on, value, status, accent, selected, onSelect, onToggle, toggled, t }) {
  const active = selected === id;
  return (
    <motion.div whileHover={{ y: -2 }} onClick={() => onSelect(active ? null : id)}
      style={{
        background: active ? accent + "18" : TK.card,
        border: `1px solid ${active ? accent + "66" : TK.line}`,
        borderRadius: 10, padding: "9px 10px", cursor: "pointer",
        display: "flex", flexDirection: "column", gap: 7, minHeight: 60,
        transition: "background .15s, border-color .15s",
      }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <span style={{ color: on ? accent : "#4b5563", display: "flex" }}><I d={ICO[icon]} size={14} /></span>
        <span style={{ fontSize: 12, fontWeight: 600, color: on ? TK.fg : TK.faint, flex: 1, minWidth: 0,
          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{name}</span>
        <Dot on={on} color={accent} />
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 6 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: on ? TK.fg : TK.faint,
            fontFamily: TK.mono, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{value}</div>
          <div style={{ fontSize: 10, color: on ? TK.muted : TK.faint, marginTop: 1,
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{status}</div>
        </div>
        {onToggle && (
          <button onClick={(e) => { e.stopPropagation(); onToggle(); }}
            style={{ fontSize: 9.5, padding: "3px 8px", borderRadius: 5, cursor: "pointer", flexShrink: 0,
              fontWeight: 600, whiteSpace: "nowrap",
              background: toggled ? "rgba(240,85,59,.12)" : "rgba(47,208,122,.12)",
              border: toggled ? `1px solid ${TK.danger}55` : `1px solid ${TK.battery}55`,
              color: toggled ? "#fca5a5" : "#6ee7a8" }}>
            {toggled ? t("s2.sys.turnOff") : t("s2.sys.turnOn")}
          </button>
        )}
      </div>
    </motion.div>
  );
}


/* ══ AI Enerji Ajanı — tam genişlik (2 sütun) ════════════════════ */
function RLAgentPanelWide({ r, sim, fmtPara, t }) {
  if (!r || !sim) return null;
  const k = r.karar || "bekle";
  const exporting = r.net_kwh != null && r.net_kwh < -0.05;
  let stKey, expKey, col;
  if (exporting) { stKey = "cc.act.export"; expKey = "cc.exp.export"; col = TK.battery; }
  else if (k === "şarj") { stKey = "cc.act.store"; expKey = "cc.exp.store"; col = TK.battery; }
  else if (k === "deşarj") { stKey = "cc.act.use"; expKey = "cc.exp.use"; col = TK.danger; }
  else { stKey = "cc.act.hold"; expKey = "cc.exp.hold"; col = TK.muted; }
  const reward = r.tasarruf_tl != null ? r.tasarruf_tl : null;
  const kararLabel = { "şarj": "CHARGE", "deşarj": "DISCHARGE", "bekle": "HOLD" }[k];
  const mini = [
    ["cc.solar", `${r.gunes_kw?.toFixed(1)} kW`, TK.solar],
    ["cc.load", `${r.talep_kw?.toFixed(1)} kW`, TK.grid],
    ["cc.battery", `${Math.round(r.soc * 100)}%`, r.soc > 0.5 ? TK.battery : r.soc > 0.2 ? TK.solar : TK.danger],
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
      className="rl-agent-grid"
      style={{ background: "linear-gradient(135deg, rgba(139,147,248,.09), rgba(139,147,248,.02))",
        border: `1px solid ${TK.ai}44`, borderRadius: 14, padding: "20px 24px",
        boxShadow: "0 12px 40px -18px rgba(99,102,241,.45)" }}>
      {/* Sol: durum + açıklama */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <span style={{ color: TK.ai, display: "flex" }}><I d={ICO.agent} size={16} /></span>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".1em", color: "#c7d2fe", textTransform: "uppercase" }}>
            AI Energy Agent
          </span>
          <span style={{ fontSize: 9.5, color: "#a5b4fc", background: "rgba(139,147,248,.14)",
            border: `1px solid ${TK.ai}4d`, borderRadius: 6, padding: "2px 9px", fontWeight: 600 }}>{sim.ajan || "TD3"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <motion.span animate={{ opacity: [1, .4, 1] }} transition={{ repeat: Infinity, duration: 1.8 }}
            style={{ width: 10, height: 10, borderRadius: "50%", background: col, boxShadow: `0 0 12px ${col}`, flexShrink: 0 }} />
          <span style={{ fontSize: 20, fontWeight: 800, color: col, letterSpacing: "-.02em" }}>{t(stKey)}</span>
        </div>
        <p style={{ margin: 0, fontSize: 13.5, color: TK.muted, lineHeight: 1.6, maxWidth: 600 }}>{t(expKey)}</p>
        {r.defer_sinyal > 0 && (
          <div style={{ marginTop: 10, fontSize: 11, color: "#a5b4fc", display: "inline-flex", alignItems: "center", gap: 6,
            background: "rgba(139,147,248,.08)", borderRadius: 7, padding: "5px 12px" }}>
            <I d={ICO.zap} size={12} /> {t("cc.defer")}
          </div>
        )}
      </div>

      {/* Sağ: mini stats + kazanç */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "flex-end" }}>
        <div style={{ display: "flex", gap: 10 }}>
          {mini.map(([lbl, val, c]) => (
            <div key={lbl} style={{ background: "rgba(255,255,255,.04)", border: `1px solid ${TK.line}`,
              borderRadius: 10, padding: "10px 14px", textAlign: "center", minWidth: 80 }}>
              <div style={{ fontSize: 9.5, letterSpacing: ".06em", textTransform: "uppercase", color: TK.faint, marginBottom: 5 }}>{t(lbl)}</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: c, fontFamily: TK.mono }}>{val}</div>
            </div>
          ))}
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 9.5, letterSpacing: ".06em", textTransform: "uppercase", color: TK.faint, marginBottom: 3 }}>{t("cc.benefit")}</div>
          <div style={{ fontSize: 24, fontWeight: 800, color: reward > 0 ? TK.battery : reward < 0 ? TK.danger : TK.muted }}>
            {reward != null ? (reward > 0 ? "+" : "") + (fmtPara ? fmtPara(reward) : reward.toFixed(2) + " TL") : "—"}
          </div>
          <div style={{ fontSize: 9.5, color: TK.faint, marginTop: 2, fontFamily: TK.mono }}>
            {kararLabel}{r.aksiyon != null ? ` · α=${r.aksiyon > 0 ? "+" : ""}${r.aksiyon.toFixed(2)}` : ""}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Mevsim / gün doğumu hesabı ──────────────────────────────── */
const SEASONS = {
  winter: { key: "s2.sea.winter", icon: "snowflake", color: "#93c5fd", months: [12, 1, 2] },
  spring: { key: "s2.sea.spring", icon: "leaf", color: TK.battery, months: [3, 4, 5] },
  summer: { key: "s2.sea.summer", icon: "sun", color: TK.solar, months: [6, 7, 8] },
  autumn: { key: "s2.sea.autumn", icon: "leaf", color: "#f97316", months: [9, 10, 11] },
};

export function sunTimes(month, day = 15) {
  const LAT_RAD = 37.06 * Math.PI / 180;
  const dayOfYear = Math.round((month - 1) * 30.44 + day);
  const B = (2 * Math.PI * (dayOfYear - 1)) / 365;
  const decl = (180 / Math.PI) * (
    0.006918 - 0.399912 * Math.cos(B) + 0.070257 * Math.sin(B)
    - 0.006758 * Math.cos(2 * B) + 0.000907 * Math.sin(2 * B)
    - 0.002697 * Math.cos(3 * B) + 0.00148 * Math.sin(3 * B)
  );
  const declRad = decl * Math.PI / 180;
  const cosH0 = -Math.tan(LAT_RAD) * Math.tan(declRad);
  const H0deg = Math.acos(Math.max(-1, Math.min(1, cosH0))) * 180 / Math.PI;
  const noonOffset = 12 + (3 - 37.38 / 15);
  const sunrise = noonOffset - H0deg / 15;
  const sunset = noonOffset + H0deg / 15;
  const fmt = (t) => {
    const hh = Math.floor(t), mm = Math.round((t - hh) * 60);
    return `${String(hh).padStart(2, "0")}:${String(mm < 60 ? mm : 59).padStart(2, "0")}`;
  };
  const maxElev = 90 - 37.06 + decl;
  return { sunrise: fmt(sunrise), sunset: fmt(sunset), dayLen: fmt(H0deg / 7.5),
    sunriseH: sunrise, sunsetH: sunset, noonH: noonOffset, maxElev };
}

/* ── Küçük etiketler ─────────────────────────────────────────── */
const Lab = ({ children }) => (
  <div style={{ fontSize: 9.5, letterSpacing: ".08em", textTransform: "uppercase",
    color: TK.faint, fontWeight: 600 }}>{children}</div>
);
const SectionHead = ({ children }) => (
  <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: ".1em", color: TK.muted,
    textTransform: "uppercase", marginBottom: 10 }}>{children}</div>
);

/* ══ Mevsim + tarih/saat paneli ═════════════════════════════════ */
function SeasonPanel({ ay, saat, locale, t }) {
  const season = Object.values(SEASONS).find((s) => s.months.includes(ay)) || SEASONS.summer;
  const sun = sunTimes(ay);
  const month = (AYLAR_FULL[locale === "en-US" ? "en" : locale === "ar" ? "ar" : "tr"] || AYLAR_FULL.en || [])[ay - 1] || "";
  const year = new Date().getFullYear();
  const rows = [
    [t("s2.tl.sunrise"), sun.sunrise, TK.solar],
    [t("s2.tl.sunset"), sun.sunset, "#f97316"],
    [t("s2.tl.day"), sun.dayLen, TK.fg],
    [t("s2.tl.loc"), "Gaziantep, TR", TK.muted],
  ];
  return (
    <div style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 12, padding: "13px 15px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{ color: season.color, display: "flex" }}><I d={ICO[season.icon]} size={15} /></span>
        <span style={{ fontSize: 12.5, fontWeight: 800, letterSpacing: ".02em", color: season.color }}>
          {t(season.key)}
        </span>
        <span style={{ marginLeft: "auto", fontSize: 12, fontWeight: 600, color: TK.muted }}>{month} {year}</span>
      </div>
      {/* büyük saat göstergesi (TIME) */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 26, fontWeight: 800, color: TK.fg, fontVariantNumeric: "tabular-nums",
          letterSpacing: "-.02em", fontFamily: TK.mono }}>{String(saat).padStart(2, "0")}:00</span>
        <span style={{ fontSize: 10.5, color: TK.faint, textTransform: "uppercase", letterSpacing: ".08em" }}>
          {t("s2.kpi.time")}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 14px" }}>
        {rows.map(([l, v, c]) => (
          <div key={l}>
            <Lab>{l}</Lab>
            <div style={{ fontSize: 12, fontWeight: 700, color: c, fontFamily: TK.mono, marginTop: 1 }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Senaryolar ──────────────────────────────────────────────── */
const SCENARIOS = [
  { id: "normal", key: "s2.scn.normal", ay: null },
  { id: "summer", key: "s2.scn.summer", ay: 7 },
  { id: "winter", key: "s2.scn.winter", ay: 1 },
  { id: "cloudy", key: "s2.scn.cloudy", ay: 11 },
  { id: "solar", key: "s2.scn.solar", ay: 6 },
  { id: "peak", key: "s2.scn.peak", ay: 8 },
];

function ScenarioBar({ active, onSelect, t }) {
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {SCENARIOS.map((s) => {
        const on = active === s.id;
        return (
          <button key={s.id} onClick={() => onSelect(s)}
            style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".01em", padding: "6px 11px",
              borderRadius: 7, cursor: "pointer", transition: "all .15s",
              background: on ? `${TK.grid}22` : TK.card,
              border: `1px solid ${on ? TK.grid + "66" : TK.line}`,
              color: on ? "#bcdcff" : TK.muted }}>
            {t(s.key)}
          </button>
        );
      })}
    </div>
  );
}

/* ══ Timeline — fiyat heatmap + güneş işaretleri + lejant ════════ */
function Timeline({ chart, saat, setSaat, ay, fmtFiyat, t }) {
  if (!chart || chart.length === 0) return null;
  const maxP = Math.max(...chart.map((r) => r.fiyat_tl_mwh));
  const minP = Math.min(...chart.map((r) => r.fiyat_tl_mwh));
  const sun = sunTimes(ay);
  const pct = (h) => `${(h / 23) * 100}%`;
  const marks = [
    [sun.sunriseH, t("s2.tl.sunrise"), TK.solar],
    [sun.noonH, t("s2.tl.peak"), "#fde68a"],
    [sun.sunsetH, t("s2.tl.sunset"), "#f97316"],
  ];
  const cur = chart[saat];

  return (
    <div style={{ background: "rgba(8,11,18,0.55)", borderTop: `1px solid ${TK.line}`, padding: "10px 20px 12px" }}>
      {/* güneş işaretleri şeridi */}
      <div style={{ position: "relative", height: 14, marginBottom: 2 }}>
        {marks.map(([h, label, c]) => (
          <div key={label} style={{ position: "absolute", left: pct(h), transform: "translateX(-50%)",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
            <span style={{ fontSize: 8.5, color: c, whiteSpace: "nowrap", fontWeight: 600 }}>{label}</span>
            <span style={{ width: 1, height: 4, background: c, opacity: .6 }} />
          </div>
        ))}
      </div>
      {/* fiyat heatmap */}
      <div style={{ display: "flex", height: 7, borderRadius: 4, overflow: "hidden", marginBottom: 8 }}>
        {chart.map((r, i) => {
          const rt = (r.fiyat_tl_mwh - minP) / Math.max(maxP - minP, 1);
          const col = rt > 0.66 ? TK.danger : rt > 0.33 ? TK.solar : TK.battery;
          return <div key={i} onClick={() => setSaat(i)}
            style={{ flex: 1, background: i === saat ? "#fff" : col + "b0", cursor: "pointer", transition: "background .15s" }} />;
        })}
      </div>
      {/* range slider */}
      <input type="range" min="0" max="23" value={saat} onChange={(e) => setSaat(+e.target.value)}
        style={{ width: "100%", accentColor: TK.grid, cursor: "pointer", height: 4 }} />
      {/* saat etiketleri */}
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: TK.faint,
        marginTop: 3, fontVariantNumeric: "tabular-nums" }}>
        {["00:00", "06:00", "12:00", "18:00", "23:00"].map((l) => <span key={l}>{l}</span>)}
      </div>
      {/* alt satır: seçili saat + fiyat + lejant */}
      <div style={{ marginTop: 9, display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 18, fontWeight: 800, color: TK.fg, fontVariantNumeric: "tabular-nums", fontFamily: TK.mono }}>
          {String(saat).padStart(2, "0")}:00
        </span>
        {cur && (
          <span style={{ fontSize: 11.5, color: TK.muted }}>
            {t("s2.ch.price")}: <b style={{ color: TK.solar }}>{fmtFiyat ? fmtFiyat(cur.fiyat_tl_mwh) : cur.fiyat_tl_mwh?.toFixed(0)}</b>
          </span>
        )}
        {cur?.karar === "şarj" && (
          <span style={{ fontSize: 10, color: TK.battery, border: `1px solid ${TK.battery}44`, borderRadius: 5, padding: "2px 9px" }}>
            {t("s2.tl.charging")}
          </span>
        )}
        {cur?.karar === "deşarj" && (
          <span style={{ fontSize: 10, color: TK.danger, border: `1px solid ${TK.danger}44`, borderRadius: 5, padding: "2px 9px" }}>
            {t("s2.tl.discharging")}
          </span>
        )}
        {/* fiyat lejantı */}
        <span style={{ marginLeft: "auto", display: "flex", gap: 12, fontSize: 10, color: TK.faint }}>
          {[[TK.battery, t("s2.leg.low")], [TK.solar, t("s2.leg.mid")], [TK.danger, t("s2.leg.high")]].map(([c, l]) => (
            <span key={l} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 7, height: 7, borderRadius: 2, background: c }} />{l}
            </span>
          ))}
        </span>
      </div>
    </div>
  );
}

/* ══════════════════ Ana Bileşen ════════════════════════════════ */
export default function Simulasyon() {
  const { cfg, setCfg, saat, setSaat, ay, setAy } = useApp();
  const { t, dil, fmtFiyat, fmtPara, paraCevir, fiyatBirimi } = useI18n();
  const [sim, setSim] = useState(null);
  const [err, setErr] = useState(null);
  const [selectedSys, setSelectedSys] = useState(null);
  const [activeScenario, setActiveScenario] = useState("normal");
  const [cfgOpen, setCfgOpen] = useState(false);
  const locale = dil === "ar" ? "ar" : dil === "en" ? "en-US" : "tr-TR";

  const cfgRef = useRef(cfg);
  cfgRef.current = cfg;
  const tarih = `${new Date().getFullYear()}-${String(ay).padStart(2, "0")}-15`;

  useEffect(() => {
    let ok = true;
    setSim(null);
    api.simulate({ config: cfg, tarih })
      .then((d) => ok && (setSim(d), setErr(null)))
      .catch((e) => ok && setErr(e.message));
    return () => { ok = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(cfg), tarih]);

  const set = (k, v) => setCfg({ ...cfg, [k]: v });
  const handleScenario = (s) => { setActiveScenario(s.id); if (s.ay) setAy(s.ay); };

  if (err) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh",
      color: TK.danger, fontSize: 14 }}>API unavailable: {err}</div>
  );

  const r = sim?.rows?.[saat];
  const chart = sim?.rows?.map((x) => ({
    ...x,
    soc_pct: +(x.soc * 100).toFixed(0),
    sarj_f: x.karar === "şarj" ? x.fiyat_tl_mwh : null,
    desarj_f: x.karar === "deşarj" ? x.fiyat_tl_mwh : null,
  }));
  const maxSolar = sim?.rows ? Math.max(0.01, ...sim.rows.map((x) => x.gunes_kw || 0)) : 1;
  const maxLoad = sim?.rows ? Math.max(0.01, ...sim.rows.map((x) => x.talep_kw || 0)) : 1;
  const toplam = cfg.kat * cfg.daire_per_kat;
  const kesinti = r?.kesinti || false;

  // Sistem tanımları — insan-dili ad + durum (mevcut veriden)
  const SYSTEMS_DEF = [
    { cat: t("s2.cat.energy"), color: TK.solar, items: [
      { id: "solar_pv", icon: "solar", name: t("s2.name.solar"), on: cfg.cati_alani > 0, accent: TK.solar,
        value: r ? `${r.gunes_kw?.toFixed(1)} kW` : "—",
        status: r ? (r.gunes_kw > 0.1 ? t("s2.sys.producing") : t("s2.sys.idle")) : "—" },
      { id: "battery", icon: "battery", name: t("s2.name.battery"), on: true, accent: TK.battery,
        value: r ? `${Math.round(r.soc * 100)}%` : "—",
        status: r ? (r.karar === "şarj" ? t("s2.sys.charging") : r.karar === "deşarj" ? t("s2.sys.discharging") : t("s2.sys.idle")) : "—" },
      { id: "jenerator", icon: "generator", name: t("sys.generator"), on: cfg.jenerator, accent: TK.danger,
        value: r && r.jenerator_kwh > 0 ? `${r.jenerator_kwh?.toFixed(1)} kW` : "0 kW",
        status: r && r.jenerator_kwh > 0 ? t("s2.sys.running") : t("s2.sys.standby") },
    ]},
    { cat: t("s2.cat.building"), color: TK.grid, items: [
      { id: "hvac", icon: "hvac", name: t("sys.hvac"), on: cfg.hvac, accent: TK.grid,
        value: cfg.hvac ? t("s2.sys.auto") : t("s2.sys.off"), status: t("s2.sys.smart") },
      { id: "asansor", icon: "elevator", name: t("sys.elevator"), on: cfg.asansor, accent: TK.grid,
        value: cfg.asansor ? t("s2.sys.active") : t("s2.sys.off"), status: cfg.asansor ? t("s2.sys.on") : t("s2.sys.off") },
      { id: "su_pompasi", icon: "pump", name: t("sys.pump"), on: cfg.su_pompasi, accent: TK.grid,
        value: cfg.su_pompasi ? t("s2.sys.active") : t("s2.sys.off"), status: cfg.su_pompasi ? t("s2.sys.on") : t("s2.sys.off") },
    ]},
    { cat: t("s2.cat.other"), color: TK.ai, items: [
      { id: "ev_sarj", icon: "ev", name: t("sys.ev"), on: cfg.ev_sarj, accent: TK.ai,
        value: `0/${cfg.aktif_daire}`, status: t("s2.sys.smart") },
      { id: "kamera", icon: "camera", name: t("sys.camera"), on: cfg.kamera, accent: TK.battery,
        value: cfg.kamera ? t("s2.sys.active") : t("s2.sys.off"), status: cfg.kamera ? t("s2.sys.connected") : t("s2.sys.off") },
      { id: "gunes_isitici", icon: "heater", name: t("sys.solarheat"), on: cfg.gunes_isitici, accent: "#fb923c",
        value: cfg.gunes_isitici ? t("s2.sys.active") : t("s2.sys.off"), status: cfg.gunes_isitici ? t("s2.sys.on") : t("s2.sys.off") },
    ]},
  ];

  const CFG_SLIDERS = [
    { label: t("s2.cfg.floors"), key: "kat", min: 1, max: 10, val: cfg.kat },
    { label: t("s2.cfg.unitsPer"), key: "daire_per_kat", min: 1, max: 4, val: cfg.daire_per_kat },
    { label: `${t("s2.cfg.activeUnits")} (${Math.min(cfg.aktif_daire, toplam)}/${toplam})`, key: "aktif_daire", min: 0, max: toplam, val: Math.min(cfg.aktif_daire, toplam) },
    { label: t("s2.cfg.rooms"), key: "oda", min: 1, max: 6, val: cfg.oda },
  ];

  const inputStyle = { width: "100%", background: "rgba(255,255,255,.05)", color: TK.fg,
    border: `1px solid ${TK.line2}`, borderRadius: 7, padding: "7px 9px", fontSize: 12.5, fontFamily: "inherit" };

  const cfgPresets = {
    "Müstakil Ev": { kat: 1, daire_per_kat: 1, aktif_daire: 1, oda: 4, cati_alani: 60, asansor: false, hvac: true, su_pompasi: false, ev_sarj: true, kamera: true, gunes_isitici: true, jenerator: false },
    Villa:         { kat: 2, daire_per_kat: 1, aktif_daire: 1, oda: 5, cati_alani: 100, asansor: false, hvac: true, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: true, jenerator: true },
    Apartman:      { kat: 5, daire_per_kat: 3, aktif_daire: 12, oda: 3, cati_alani: 140, asansor: true, hvac: false, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: false, jenerator: true },
    "Ofis Binası": { kat: 6, daire_per_kat: 2, aktif_daire: 10, oda: 6, cati_alani: 200, asansor: true, hvac: true, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: false, jenerator: true },
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
      className="sim-outer" style={{ color: TK.fg }}>

      {/* ── Sayfa başlığı ───────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, letterSpacing: "-.02em", color: "#fff" }}>{t("sim.title")}</h1>
        <p style={{ margin: "6px 0 0", fontSize: 13.5, color: TK.muted }}>{t("sim.ccSub")}</p>
      </div>

      {/* ── KPI kartları ─────────────────────────────────────── */}
      <KpiCards r={r} cfg={cfg} saat={saat} maxSolar={maxSolar} maxLoad={maxLoad}
        paraCevir={paraCevir} fiyatBirimi={fiyatBirimi} locale={locale} t={t} />

      {/* ── Ana iki sütun: Sol kontroller | Sağ 3D + slider ── */}
      <div className="sim-main-grid">

        {/* SOL: kontroller */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <SeasonPanel ay={ay} saat={saat} locale={locale} t={t} />

          <div style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 12, padding: "13px 15px" }}>
            <Lab style={{ marginBottom: 8 }}>{t("s2.sec.scenario")}</Lab>
            <div style={{ marginTop: 8 }}>
              <ScenarioBar active={activeScenario} onSelect={handleScenario} t={t} />
            </div>
          </div>

          {/* Bina yapılandırması — katlanabilir */}
          <div style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 12, overflow: "hidden" }}>
            <button onClick={() => setCfgOpen((o) => !o)}
              style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "12px 14px",
                background: "none", border: "none", cursor: "pointer", color: TK.muted, fontFamily: "inherit" }}>
              <span style={{ color: TK.grid, display: "flex" }}><I d={ICO.building} size={14} /></span>
              <span style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: ".05em", textTransform: "uppercase", flex: 1, textAlign: "left" }}>
                {t("s2.cfg.title")}
              </span>
              <motion.span animate={{ rotate: cfgOpen ? 180 : 0 }} style={{ display: "flex", color: TK.faint }}>
                <I d={ICO.chevron} size={14} />
              </motion.span>
            </button>
            <AnimatePresence initial={false}>
              {cfgOpen && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                  style={{ overflow: "hidden" }}>
                  <div style={{ padding: "0 14px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
                    <div>
                      <Lab>{t("s2.cfg.type")}</Lab>
                      <select value={cfg.bina_tipi} style={{ ...inputStyle, marginTop: 4 }}
                        onChange={(e) => { const p = cfgPresets[e.target.value] || {}; setCfg({ bina_tipi: e.target.value, ...p }); }}>
                        {["Müstakil Ev", "Villa", "Apartman", "Ofis Binası"].map((tip) => (
                          <option key={tip} value={tip}>{t(`btype.${tip}`)}</option>
                        ))}
                      </select>
                    </div>
                    {CFG_SLIDERS.map(({ label, key, min, max, val }) => (
                      <div key={key}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <Lab>{label}</Lab>
                          <span style={{ fontSize: 11, fontWeight: 700, color: TK.fg, fontFamily: TK.mono }}>{val}</span>
                        </div>
                        <input type="range" min={min} max={max} value={val} onChange={(e) => set(key, +e.target.value)}
                          style={{ width: "100%", accentColor: TK.grid, height: 3 }} />
                      </div>
                    ))}
                    <div>
                      <Lab>{t("s2.cfg.roof")}</Lab>
                      <input type="number" min="10" max="1000" step="10" value={cfg.cati_alani}
                        onChange={(e) => set("cati_alani", +e.target.value || 10)} style={{ ...inputStyle, marginTop: 4 }} />
                    </div>
                    <div>
                      <Lab>{t("s2.cfg.month")}</Lab>
                      <select value={ay} onChange={(e) => setAy(+e.target.value)} style={{ ...inputStyle, marginTop: 4 }}>
                        {(AYLAR_FULL[locale === "en-US" ? "en" : locale === "ar" ? "ar" : "tr"] || AYLAR_FULL.en || []).map((m, i) => (
                          <option key={i} value={i + 1}>{m}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* SAĞ: 3D bina + timeline slider */}
        <div style={{ display: "flex", flexDirection: "column", background: TK.bg,
          border: `1px solid ${TK.line2}`, borderRadius: 16, overflow: "hidden" }}>
          <LiveStatus r={r} maxSolar={maxSolar} maxLoad={maxLoad} t={t} />
          {/* 3D bina */}
          <div style={{ height: 500, minHeight: 500, flexShrink: 0, position: "relative" }}>
            {!sim ? (
              <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
                justifyContent: "center", color: TK.faint, fontSize: 13 }}>
                <motion.div animate={{ opacity: [.4, 1, .4] }} transition={{ repeat: Infinity, duration: 1.5 }}>
                  {t("load.profile") || "Yükleniyor…"}
                </motion.div>
              </div>
            ) : (
              <Building cfg={cfg} saat={saat} ay={ay} soc={r?.soc ?? 0.5}
                gunesKw={r?.gunes_kw ?? 0} kesinti={kesinti} height={500} dil={dil} highlight={selectedSys} />
            )}
            <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
              boxShadow: "inset 0 0 80px 20px rgba(8,11,18,.6)" }} />
          </div>
          <Timeline chart={chart} saat={saat} setSaat={setSaat} ay={ay} fmtFiyat={fmtFiyat} t={t} />
        </div>
      </div>

      {/* ── AI Enerji Ajanı — tam genişlik, öne çıkan ────────── */}
      <div style={{ marginBottom: 16 }}>
        <RLAgentPanelWide r={r} sim={sim} fmtPara={fmtPara} t={t} />
      </div>

      {/* ── Bina Sistemleri — yatay 3 grup ───────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <SectionHead>{t("s2.sec.systems")}</SectionHead>
        <div className="sim-sys-grid">
          {SYSTEMS_DEF.map(({ cat, color, items }) => (
            <div key={cat} style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 14, padding: "14px 14px 12px" }}>
              <div style={{ fontSize: 9.5, letterSpacing: ".1em", fontWeight: 700, color, textTransform: "uppercase",
                marginBottom: 12, display: "flex", alignItems: "center", gap: 7 }}>
                <div style={{ flex: 1, height: 1, background: color + "33" }} />{cat}
                <div style={{ flex: 1, height: 1, background: color + "33" }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {items.map((sys) => {
                  const cfgKey = { hvac: "hvac", asansor: "asansor", su_pompasi: "su_pompasi",
                    ev_sarj: "ev_sarj", kamera: "kamera", gunes_isitici: "gunes_isitici", jenerator: "jenerator" }[sys.id];
                  return (
                    <SysCard key={sys.id} id={sys.id} icon={sys.icon} name={sys.name} on={sys.on}
                      value={sys.value} status={sys.status} accent={sys.accent || color}
                      selected={selectedSys} onSelect={setSelectedSys}
                      onToggle={cfgKey ? () => set(cfgKey, !cfg[cfgKey]) : null}
                      toggled={cfgKey ? cfg[cfgKey] : false} t={t} />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 24 Saat Enerji Akışı ─────────────────────────────── */}
      {sim && chart && (
        <div style={{ background: TK.card, border: `1px solid ${TK.line}`, borderRadius: 14, padding: "16px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <SectionHead>{t("s2.sec.overview")}</SectionHead>
            <div style={{ display: "flex", gap: 14, fontSize: 10, color: TK.faint }}>
              {[[TK.solar, t("s2.ch.solar")], [TK.price, t("s2.ch.price")], [TK.battery, t("s2.ch.battery")]].map(([c, l]) => (
                <span key={l} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                  <span style={{ width: 12, height: 2, borderRadius: 2, background: c }} />{l}
                </span>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <ComposedChart data={chart} margin={{ top: 4, right: 6, left: 2, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,.04)" vertical={false} />
              <XAxis dataKey="saat" stroke={TK.line} tick={{ fontSize: 10, fill: TK.faint }} ticks={[0, 6, 12, 18, 23]} />
              <YAxis yAxisId="tl" stroke={TK.line} tick={{ fontSize: 10, fill: TK.faint }}
                tickFormatter={(v) => Math.round(paraCevir(v)).toLocaleString(locale)} width={46} />
              <YAxis yAxisId="pct" orientation="right" stroke={TK.line} tick={{ fontSize: 10, fill: TK.faint }} width={30} />
              <Tooltip contentStyle={{ background: TK.panelSolid, border: `1px solid ${TK.line2}`, borderRadius: 8, fontSize: 11, color: TK.fg }}
                itemStyle={{ color: TK.muted }} labelStyle={{ color: TK.faint }}
                formatter={(v, name, p) => (p?.dataKey === "soc_pct" ? [Math.round(v) + "%", name] : [typeof v === "number" ? v.toFixed(1) : v, name])} />
              <Area yAxisId="pct" dataKey="gunes_kw" name={t("s2.ch.solar")} fill={TK.solar + "1c"} stroke={TK.solar} strokeWidth={1.8} dot={false} />
              <Line yAxisId="tl" dataKey="fiyat_tl_mwh" name={t("s2.ch.price")} stroke={TK.price} strokeWidth={1.8} dot={false} />
              <Line yAxisId="pct" dataKey="soc_pct" name={t("s2.ch.battery")} stroke={TK.battery} strokeWidth={1.8} dot={false} />
              <Scatter yAxisId="tl" dataKey="sarj_f" name={t("s2.ch.charge")} fill={TK.grid} shape="triangle" />
              <Scatter yAxisId="tl" dataKey="desarj_f" name={t("s2.ch.discharge")} fill={TK.danger} shape="triangle" />
              <ReferenceLine yAxisId="tl" x={saat} stroke={TK.grid} strokeWidth={1.5} strokeDasharray="3 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  );
}
