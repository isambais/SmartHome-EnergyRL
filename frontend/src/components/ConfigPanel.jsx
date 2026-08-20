import { motion } from "framer-motion";
import { BINA_TIPLERI, useApp } from "../state.jsx";
import { AYLAR_FULL, useI18n } from "../i18n.jsx";

// Türkçe ay adları (PDF/geri uyum için sabit export)
export const AYLAR = AYLAR_FULL.tr;

const SISTEMLER = [
  ["asansor", "sys.elevator"],
  ["hvac", "sys.hvac"],
  ["su_pompasi", "sys.pump"],
  ["ev_sarj", "sys.ev"],
  ["kamera", "sys.camera"],
  ["gunes_isitici", "sys.solarheat"],
  ["jenerator", "sys.generator"],
];

export default function ConfigPanel({ showSaat = true, showAy = true }) {
  const { cfg, setCfg, saat, setSaat, ay, setAy } = useApp();
  const { t, dil } = useI18n();
  const aylar = AYLAR_FULL[dil] || AYLAR_FULL.tr;
  const set = (k, v) => setCfg({ ...cfg, [k]: v });
  const toplam = cfg.kat * cfg.daire_per_kat;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h3 style={{ margin: "4px 0 8px", fontSize: 16 }}>{t("cfg.title")}</h3>

      <label className="fld">{t("cfg.type")}</label>
      <select
        value={cfg.bina_tipi}
        onChange={(e) => setCfg({ bina_tipi: e.target.value, ...BINA_TIPLERI[e.target.value] })}
      >
        {Object.keys(BINA_TIPLERI).map((tip) => <option key={tip} value={tip}>{t("btype." + tip)}</option>)}
      </select>

      <label className="fld">{t("cfg.floors")}: <b>{cfg.kat}</b></label>
      <input type="range" min="1" max="10" value={cfg.kat}
        onChange={(e) => set("kat", +e.target.value)} />

      <label className="fld">{t("cfg.flatsPer")}: <b>{cfg.daire_per_kat}</b></label>
      <input type="range" min="1" max="4" value={cfg.daire_per_kat}
        onChange={(e) => set("daire_per_kat", +e.target.value)} />

      <label className="fld">{t("cfg.activeFlats")}: <b>{Math.min(cfg.aktif_daire, toplam)}</b> / {toplam}</label>
      <input type="range" min="0" max={toplam} value={Math.min(cfg.aktif_daire, toplam)}
        onChange={(e) => set("aktif_daire", +e.target.value)} />

      <label className="fld">{t("cfg.rooms")}: <b>{cfg.oda}</b></label>
      <input type="range" min="1" max="6" value={cfg.oda}
        onChange={(e) => set("oda", +e.target.value)} />

      <label className="fld">{t("cfg.roof")}</label>
      <input type="number" min="10" max="1000" step="10" value={cfg.cati_alani}
        onChange={(e) => set("cati_alani", +e.target.value || 10)} />

      <label className="fld" style={{ marginTop: 14 }}>{t("cfg.systems")}</label>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
        {SISTEMLER.map(([k, key]) => (
          <label key={k} className="chk">
            <input type="checkbox" checked={!!cfg[k]} onChange={(e) => set(k, e.target.checked)} />
            {t(key)}
          </label>
        ))}
      </div>

      {showAy && (
        <>
          <label className="fld" style={{ marginTop: 14 }}>{t("cfg.month")}: <b>{aylar[ay - 1]}</b></label>
          <select value={ay} onChange={(e) => setAy(+e.target.value)}>
            {aylar.map((a, i) => <option key={i} value={i + 1}>{a}</option>)}
          </select>
        </>
      )}

      {showSaat && (
        <>
          <label className="fld" style={{ marginTop: 14 }}>{t("cfg.hour")}: <b>{String(saat).padStart(2, "0")}:00</b></label>
          <input type="range" min="0" max="23" value={saat} onChange={(e) => setSaat(+e.target.value)} />
        </>
      )}
    </motion.div>
  );
}
