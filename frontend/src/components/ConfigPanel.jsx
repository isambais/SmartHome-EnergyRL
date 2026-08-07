import { motion } from "framer-motion";
import { BINA_TIPLERI, useApp } from "../state.jsx";

const SISTEMLER = [
  ["asansor", "Asansör"],
  ["hvac", "HVAC (klima)"],
  ["su_pompasi", "Su Pompası"],
  ["ev_sarj", "EV Şarj"],
  ["kamera", "Kamera"],
  ["gunes_isitici", "Güneş Isıtıcı"],
  ["jenerator", "Jeneratör"],
];

export const AYLAR = [
  "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
];

export default function ConfigPanel({ showSaat = true, showAy = true }) {
  const { cfg, setCfg, saat, setSaat, ay, setAy } = useApp();
  const set = (k, v) => setCfg({ ...cfg, [k]: v });
  const toplam = cfg.kat * cfg.daire_per_kat;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h3 style={{ margin: "4px 0 8px", fontSize: 16 }}>Bina Konfigüratörü</h3>

      <label className="fld">Bina tipi</label>
      <select
        value={cfg.bina_tipi}
        onChange={(e) => setCfg({ bina_tipi: e.target.value, ...BINA_TIPLERI[e.target.value] })}
      >
        {Object.keys(BINA_TIPLERI).map((t) => <option key={t}>{t}</option>)}
      </select>

      <label className="fld">Kat sayısı: <b>{cfg.kat}</b></label>
      <input type="range" min="1" max="10" value={cfg.kat}
        onChange={(e) => set("kat", +e.target.value)} />

      <label className="fld">Kat başına daire: <b>{cfg.daire_per_kat}</b></label>
      <input type="range" min="1" max="4" value={cfg.daire_per_kat}
        onChange={(e) => set("daire_per_kat", +e.target.value)} />

      <label className="fld">Aktif daire: <b>{Math.min(cfg.aktif_daire, toplam)}</b> / {toplam}</label>
      <input type="range" min="0" max={toplam} value={Math.min(cfg.aktif_daire, toplam)}
        onChange={(e) => set("aktif_daire", +e.target.value)} />

      <label className="fld">Oda sayısı (daire başına): <b>{cfg.oda}</b></label>
      <input type="range" min="1" max="6" value={cfg.oda}
        onChange={(e) => set("oda", +e.target.value)} />

      <label className="fld">Çatı alanı (m²)</label>
      <input type="number" min="10" max="1000" step="10" value={cfg.cati_alani}
        onChange={(e) => set("cati_alani", +e.target.value || 10)} />

      <label className="fld" style={{ marginTop: 14 }}>Sistemler</label>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
        {SISTEMLER.map(([k, ad]) => (
          <label key={k} className="chk">
            <input type="checkbox" checked={!!cfg[k]} onChange={(e) => set(k, e.target.checked)} />
            {ad}
          </label>
        ))}
      </div>

      {showAy && (
        <>
          <label className="fld" style={{ marginTop: 14 }}>Ay (mevsim): <b>{AYLAR[ay - 1]}</b></label>
          <select value={ay} onChange={(e) => setAy(+e.target.value)}>
            {AYLAR.map((a, i) => <option key={a} value={i + 1}>{a}</option>)}
          </select>
        </>
      )}

      {showSaat && (
        <>
          <label className="fld" style={{ marginTop: 14 }}>Saat: <b>{String(saat).padStart(2, "0")}:00</b></label>
          <input type="range" min="0" max="23" value={saat} onChange={(e) => setSaat(+e.target.value)} />
        </>
      )}
    </motion.div>
  );
}
