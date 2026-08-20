import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Loading, Metric, PageWrap } from "../components/ui.jsx";
import { useApp } from "../state.jsx";
import { PARALAR, useI18n } from "../i18n.jsx";
import { Building, Calendar, Chart, Coins, Home, Shield, Star } from "../icons.jsx";

const EASE = [0.22, 1, 0.36, 1];
/* Kademeli giriş animasyonu — her kart bir öncekinden hafif gecikmeyle süzülür */
const rise = (i = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: EASE, delay: 0.06 + i * 0.07 },
});

/* Renk aksanlı kart başlığı (ikon + başlık + alt yazı) */
function CardHead({ renk, Icon, baslik, alt }) {
  return (
    <div className="pf-card-head">
      <span className="pf-card-ic"><Icon size={19} /></span>
      <div>
        <div className="pf-card-title">{baslik}</div>
        {alt && <div className="pf-card-sub">{alt}</div>}
      </div>
    </div>
  );
}

export default function Profil() {
  const { user } = useApp();
  const { t, dil, parabirimi, setParaBirimi, kur, fmtPara } = useI18n();
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
      {/* ── Hero: avatar + kimlik + hızlı bilgiler ─────────── */}
      <motion.div className="pf-hero"
        initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: EASE }}>
        <div className="pf-avatar">{(data.user.ad || "K").charAt(0).toUpperCase()}</div>
        <div style={{ minWidth: 0 }}>
          <div className="pf-name">{data.user.ad}</div>
          <div className="pf-email">{data.user.email}</div>
        </div>
        <div className="pf-hero-stats">
          <span className="pf-chip"><span style={{ color: "var(--muted)", display: "flex" }}><Calendar size={14} /></span> {t("profile.member")}: {new Date(data.user.created_at).toLocaleDateString(locale)}</span>
          {bina && <span className="pf-chip"><span style={{ color: "var(--muted)", display: "flex" }}><Building size={14} /></span> {t(`btype.${bina.bina_tipi}`)}</span>}
        </div>
      </motion.div>

      <p className="caption" style={{ margin: "14px 2px 18px" }}>{t("profile.sub")}</p>

      <div className="split wide-r">
        {/* ── Sol sütun ───────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <motion.div className="pf-card" style={{ "--c": "#f59e0b", "--c-soft": "rgba(245,158,11,0.14)" }} {...rise(0)}>
            <CardHead renk="#f59e0b" Icon={Shield} baslik={t("profile.changePw")} />
            <form onSubmit={sifreGonder}>
              <label className="pf-label">{t("profile.currentPw")}</label>
              <input type="password" className="pf-input" value={eski} onChange={(e) => setEski(e.target.value)} required />
              <label className="pf-label">{t("profile.newPw")}</label>
              <input type="password" className="pf-input" value={yeni} onChange={(e) => setYeni(e.target.value)} minLength={4} required />
              {sifreMsj && (
                <div style={{ marginTop: 12, fontSize: 13.5, fontWeight: 600, color: sifreMsj.ok ? "#34d399" : "#fca5a5" }}>{sifreMsj.txt}</div>
              )}
              <button type="submit" className="btn-app" style={{ marginTop: 16, width: "100%", padding: "12px 0", fontSize: 14.5 }}>
                {t("profile.updatePw")}
              </button>
            </form>
          </motion.div>

          <motion.div className="pf-card" style={{ "--c": "#34d399", "--c-soft": "rgba(52,211,153,0.14)" }} {...rise(1)}>
            <CardHead renk="#22c55e" Icon={Coins} baslik={t("profile.currency")} alt={t("profile.currencyAlt")} />
            <div className="pf-seg">
              {PARALAR.map((p) => (
                <button key={p.kod} type="button" onClick={() => setParaBirimi(p.kod)}
                  className={parabirimi === p.kod ? "on" : ""}>
                  {p.sembol} {p.kod}
                </button>
              ))}
            </div>
            <div className="caption" style={{ marginTop: 12 }}>
              {t("profile.rate")}: <b style={{ color: "#fff" }}>{kur.toLocaleString(locale, { maximumFractionDigits: 2 })} ₺</b>
              {" · "}
              {localStorage.getItem("she_kur_manuel") === "1" ? t("profile.rateManual") : t("profile.rateLive")}
            </div>
          </motion.div>
        </div>

        {/* ── Sağ sütun ───────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <motion.div className="pf-card" style={{ "--c": "#3b82f6", "--c-soft": "rgba(59,130,246,0.14)" }} {...rise(1)}>
            <CardHead renk="#3b82f6" Icon={Home} baslik={t("profile.savedBuilding")} alt={t("profile.savedBuilding.alt")} />
            {bina ? (
              <div className="pf-info">
                <span className="pf-info-chip"><b>{t(`btype.${bina.bina_tipi}`)}</b></span>
                <span className="pf-info-chip"><b>{bina.kat}</b> {t("profile.floors")}</span>
                <span className="pf-info-chip"><b>{bina.aktif_daire}</b> {t("profile.activeFlats")}</span>
                <span className="pf-info-chip"><b>{bina.cati_alani}</b> {t("profile.roof")}</span>
              </div>
            ) : (
              <div className="caption">{t("profile.noBuilding")}</div>
            )}
          </motion.div>

          {yatirim && (
            <motion.div {...rise(2)}>
              <CardHead renk="#22c55e" Icon={Star} baslik={t("profile.savingsSummary")} />
              <div className="grid grid-4">
                <Metric i={0} label={t("m.yearlySaving")} value={yatirim.yillik_tasarruf} para />
                <Metric i={1} label={t("m.payback")} value={yatirim.amorti_yil} decimals={1} suffix={" " + t("unit.year")} />
                <Metric i={2} label={t("m.co2")} value={yatirim.co2_ton} decimals={1} suffix={" " + t("unit.ton")} />
                <Metric i={3} label={t("invest.solarProd")} value={yatirim.yillik_uretim_kwh} suffix=" kWh" />
              </div>
            </motion.div>
          )}

          <motion.div className="pf-card" style={{ "--c": "#f97316", "--c-soft": "rgba(249,115,22,0.14)" }} {...rise(3)}>
            <CardHead renk="#f97316" Icon={Chart} baslik={t("profile.history")} />
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
                      <td>{fmtPara(g.tasarruf_tl)}</td>
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
