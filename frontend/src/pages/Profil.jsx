import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Loading, Metric, PageWrap } from "../components/ui.jsx";
import { useApp } from "../state.jsx";
import { useI18n } from "../i18n.jsx";

function CardHead({ renk, baslik, alt }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ width: 4, height: 18, borderRadius: 2, background: renk }} />
        <b style={{ fontSize: 15.5 }}>{baslik}</b>
      </div>
      {alt && <div className="caption" style={{ marginTop: 4, marginLeft: 14 }}>{alt}</div>}
    </div>
  );
}

const inpStil = {
  width: "100%", background: "var(--bg3)", border: "1px solid var(--border)",
  color: "var(--fg)", borderRadius: 8, padding: "9px 11px", fontSize: 14, fontFamily: "inherit",
};

export default function Profil() {
  const { user } = useApp();
  const { t, dil } = useI18n();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [yatirim, setYatirim] = useState(null);
  const [eski, setEski] = useState("");
  const [yeni, setYeni] = useState("");
  const [sifreMsj, setSifreMsj] = useState(null);
  const locale = dil === "ar" ? "ar" : dil === "en" ? "en-US" : "tr-TR";

  const yukle = () => api.profile().then(setData).catch((e) => setErr(e.message));
  useEffect(() => { yukle(); }, []);
  useEffect(() => {
    const bina = data?.user?.bina;
    if (bina) api.yatirim({ config: bina }).then(setYatirim).catch(() => {});
  }, [JSON.stringify(data?.user?.bina)]);

  if (err) return <PageWrap><h1>{t("profile.title")}</h1><div className="kesinti-uyari">{t("common.apidown")} ({err})</div></PageWrap>;
  if (!data) return <PageWrap><h1>{t("profile.title")}</h1><Loading text={t("load.profile")} /></PageWrap>;

  const bina = data.user.bina;

  const sifreGonder = async (e) => {
    e.preventDefault();
    setSifreMsj(null);
    try {
      await api.sifreDegistir(eski, yeni);
      setSifreMsj({ ok: true, txt: t("profile.pwUpdated") });
      setEski(""); setYeni("");
    } catch (er) { setSifreMsj({ ok: false, txt: er.message }); }
  };

  return (
    <PageWrap>
      <h1>{t("profile.title")}</h1>
      <p className="caption" style={{ marginBottom: 16 }}>{t("profile.sub")}</p>

      <div className="split wide-r">
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <motion.div className="card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 4 }}>
              <div style={{ width: 52, height: 52, borderRadius: "50%", flexShrink: 0,
                background: "linear-gradient(135deg,#34d399,#10b981)", color: "#04120c",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 22, fontWeight: 800, boxShadow: "0 0 22px -4px #34d39988" }}>
                {(data.user.ad || "K").charAt(0).toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>{data.user.ad}</div>
                <div className="caption">{data.user.email}</div>
              </div>
            </div>
            <div className="caption" style={{ marginTop: 8 }}>
              {t("profile.member")}: {new Date(data.user.created_at).toLocaleDateString(locale)}
            </div>
          </motion.div>

          <motion.div className="card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
            <CardHead renk="#f59e0b" baslik={t("profile.changePw")} />
            <form onSubmit={sifreGonder}>
              <label className="fld">{t("profile.currentPw")}</label>
              <input type="password" style={inpStil} value={eski} onChange={(e) => setEski(e.target.value)} required />
              <label className="fld">{t("profile.newPw")}</label>
              <input type="password" style={inpStil} value={yeni} onChange={(e) => setYeni(e.target.value)} minLength={4} required />
              {sifreMsj && (
                <div style={{ marginTop: 10, fontSize: 13.5, color: sifreMsj.ok ? "#34d399" : "#fca5a5" }}>{sifreMsj.txt}</div>
              )}
              <button type="submit" className="btn-app" style={{ marginTop: 14, width: "100%", padding: "12px 0", fontSize: 14.5 }}>
                {t("profile.updatePw")}
              </button>
            </form>
          </motion.div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <motion.div className="card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
            <CardHead renk="#3b82f6" baslik={t("profile.savedBuilding")} alt={t("profile.savedBuilding.alt")} />
            {bina ? (
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap", fontSize: 14 }}>
                <span><b>{t(`btype.${bina.bina_tipi}`)}</b></span>
                <span>{bina.kat} {t("profile.floors")}</span>
                <span>{bina.aktif_daire} {t("profile.activeFlats")}</span>
                <span>{bina.cati_alani} {t("profile.roof")}</span>
              </div>
            ) : (
              <div className="caption">{t("profile.noBuilding")}</div>
            )}
          </motion.div>

          {yatirim && (
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
              <CardHead renk="#22c55e" baslik={t("profile.savingsSummary")} />
              <div className="grid grid-4">
                <Metric i={0} label={t("m.yearlySaving")} value={yatirim.yillik_tasarruf} suffix=" TL" />
                <Metric i={1} label={t("m.payback")} value={yatirim.amorti_yil} decimals={1} suffix={" " + t("unit.year")} />
                <Metric i={2} label={t("m.co2")} value={yatirim.co2_ton} decimals={1} suffix={" " + t("unit.ton")} />
                <Metric i={3} label={t("invest.solarProd")} value={yatirim.yillik_uretim_kwh} suffix=" kWh" />
              </div>
            </motion.div>
          )}

          <motion.div className="card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }}>
            <CardHead renk="#f97316" baslik={t("profile.history")} />
            {data.gecmis.length === 0 ? (
              <div className="caption">{t("profile.noHistory")}</div>
            ) : (
              <table className="tbl">
                <thead><tr><th>{t("epias.col.hour")}</th><th>{t("cfg.type")}</th><th>{t("m.yearlySaving")}</th><th>{t("m.solar")}</th></tr></thead>
                <tbody>
                  {data.gecmis.map((g) => (
                    <tr key={g.id}>
                      <td>{new Date(g.tarih).toLocaleDateString(locale)}</td>
                      <td>{t(`btype.${g.bina_tipi}`)}</td>
                      <td>{Math.round(g.tasarruf_tl)} TL</td>
                      <td>{Math.round(g.gunes_kwh)} kWh</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </motion.div>
        </div>
      </div>
    </PageWrap>
  );
}
