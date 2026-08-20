import { motion, useSpring, useTransform, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { useI18n } from "../i18n.jsx";

/** Sayfa başlığı — büyük başlık + alt açıklama + sağ aksiyonlar, altında ince ayraç */
export function PageHeader({ title, subtitle, right }) {
  return (
    <div className="page-header">
      <div style={{ minWidth: 0 }}>
        <h1 style={{ margin: 0 }}>{title}</h1>
        {subtitle && <p className="caption" style={{ marginTop: 7, maxWidth: 560, fontSize: 13.5 }}>{subtitle}</p>}
      </div>
      {right && <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>{right}</div>}
    </div>
  );
}

/** İkon rozetli bölüm kartı */
export function Section({ icon: Icon, title, desc, accent = "#34d399", right, children, style, i = 0 }) {
  return (
    <motion.div className="card sect"
      initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.05, duration: 0.35 }} style={style}>
      <div className="sect-head">
        <div style={{ display: "flex", gap: 11, alignItems: "center", minWidth: 0 }}>
          {Icon && <span className="sect-ico" style={{ color: accent, background: accent + "1f" }}><Icon size={16} /></span>}
          <div style={{ minWidth: 0 }}>
            <div className="sect-title">{title}</div>
            {desc && <div className="caption" style={{ marginTop: 2 }}>{desc}</div>}
          </div>
        </div>
        {right}
      </div>
      {children}
    </motion.div>
  );
}

/** Küçük bilgi çipi */
export function Chip({ icon: Icon, children, accent }) {
  return (
    <span className="ui-chip">
      {Icon && <span style={{ display: "flex", color: accent || "var(--muted)" }}><Icon size={13} /></span>}
      {children}
    </span>
  );
}

/** Sayfa geçiş animasyonu sarmalayıcısı */
export function PageWrap({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

/** Animasyonlu sayı (count-up) */
export function AnimNum({ value, decimals = 0, suffix = "", prefix = "" }) {
  const spring = useSpring(0, { stiffness: 90, damping: 20 });
  const display = useTransform(spring, (v) =>
    `${prefix}${v.toLocaleString("tr-TR", { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}${suffix}`
  );
  useEffect(() => { spring.set(value ?? 0); }, [value, spring]);
  return <motion.span>{display}</motion.span>;
}

/** Metrik kartı — opsiyonel ikon + aksan rengi */
export function Metric({ label, value, decimals = 0, suffix = "", prefix = "", delta, icon: Icon, accent = "#34d399", i = 0, para = false }) {
  const { paraCevir, paraSuffix, parabirimi } = useI18n();
  let val = value, sfx = suffix, dec = decimals;
  if (para) {
    val = paraCevir(value);
    sfx = paraSuffix;
    dec = parabirimi === "USD" ? (Math.abs(val) < 100 ? 1 : 0) : 0;
  }
  return (
    <motion.div
      className="card metric-card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.07, duration: 0.35 }}
      whileHover={{ y: -3 }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div className="metric-label">{label}</div>
        {Icon && <span className="metric-ico" style={{ color: accent, background: accent + "1f" }}><Icon size={15} /></span>}
      </div>
      <div className="metric-value">
        <AnimNum value={val} decimals={dec} suffix={sfx} prefix={prefix} />
      </div>
      {delta && <div className="metric-delta">{delta}</div>}
    </motion.div>
  );
}

/** Öneri kutusu listesi (staggered) */
export function Oneriler({ items }) {
  return (
    <AnimatePresence mode="popLayout">
      {(items || []).map((o, idx) => (
        <motion.div
          key={o}
          className="oneri"
          layout
          initial={{ opacity: 0, x: -18 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 18 }}
          transition={{ delay: idx * 0.06 }}
        >
          {o}
        </motion.div>
      ))}
    </AnimatePresence>
  );
}

/** Basit yükleniyor animasyonu */
export function Loading({ text = "Simülasyon çalışıyor…" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 30, color: "var(--muted)" }}>
      <motion.div
        style={{ width: 18, height: 18, border: "3px solid #e5e1da", borderTopColor: "#3b82f6", borderRadius: "50%" }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
      />
      {text}
    </div>
  );
}

/** Debounce hook — slider'lar API'yi boğmasın */
export function useDebounced(value, ms = 400) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
