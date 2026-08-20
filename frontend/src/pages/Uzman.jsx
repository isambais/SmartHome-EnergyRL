import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, Cell, ErrorBar, Line, LineChart,
  Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";
import { Loading, PageWrap } from "../components/ui.jsx";
import { useApp } from "../state.jsx";
import { AYLAR_KISA, useI18n } from "../i18n.jsx";

const RENK = { SAC: "#22c55e", TD3: "#3b82f6", PPO: "#f59e0b", A2C: "#f97316" };
const AY_RENK = (m) => ([12, 1, 2].includes(m) ? "#3b82f6" : [3, 4, 5].includes(m) ? "#22c55e" : [6, 7, 8].includes(m) ? "#f59e0b" : "#f97316");

const fadeUp = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: "easeOut" },
};

function Tabs({ tabs, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)", marginBottom: 20 }}>
      {tabs.map((t) => (
        <button key={t.id} onClick={() => onChange(t.id)}
          style={{
            background: "none", border: "none", cursor: "pointer", position: "relative",
            color: active === t.id ? "var(--fg)" : "var(--muted)",
            fontSize: 15, fontWeight: 600, padding: "12px 18px", fontFamily: "inherit",
          }}>
          {t.ad}
          {active === t.id && (
            <motion.div layoutId="uzman-tab"
              style={{ position: "absolute", bottom: -1, left: 8, right: 8, height: 2.5, background: "var(--blue)", borderRadius: 2 }} />
          )}
        </button>
      ))}
    </div>
  );
}

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

export default function Uzman() {
  const { uzman, setUzman } = useApp();
  const { t, dil, fmtPara, fmtFiyat, paraCevir, paraSuffix, fiyatBirimi, parabirimi } = useI18n();
  const locale = dil === "ar" ? "ar" : dil === "en" ? "en-US" : "tr-TR";
  // Backend tablo sütunları: "(TL)" içerenleri seçili para birimine çevir
  const tlSutun = (k) => /\(TL\)/i.test(String(k));
  const sutunBaslik = (k) => (tlSutun(k) ? String(k).replace(/\(TL\)/i, "(" + paraSuffix.trim() + ")") : k);
  const huceDeger = (k, v) => {
    const n = Number(v);
    if (tlSutun(k) && Number.isFinite(n)) return parabirimi === "USD" ? paraCevir(n).toFixed(1) : v;
    return v;
  };
  const [tab, setTab] = useState("algo");
  const [cmp, setCmp] = useState(null);
  const [mev, setMev] = useState(null);
  const aylarKisa = AYLAR_KISA[dil] || AYLAR_KISA.tr;

  useEffect(() => {
    api.karsilastirma().then(setCmp).catch(() => setCmp({ algoritmalar: [], forecast: [], pivot: [] }));
    api.mevsimsel().then(setMev).catch(() => {});
  }, []);

  const oracle = cmp ? cmp.algoritmalar.filter((r) => r.Mod === "Oracle") : [];
  const enIyi = oracle.length ? oracle.reduce((a, b) => (b.mean > a.mean ? b : a)) : null;
  const TABS = [
    { id: "algo", ad: t("expert.tab.algo") },
    { id: "mod", ad: t("expert.tab.mode") },
    { id: "mevsim", ad: t("expert.tab.season") },
  ];

  return (
    <PageWrap>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>{t("expert.title")}</h1>
          <p className="caption" style={{ maxWidth: 460 }}>{t("expert.sub")}</p>
        </div>
        <label className="toggle-switch">
          <input type="checkbox" checked={uzman} onChange={(e) => setUzman(e.target.checked)} />
          <span className="track"><span className="thumb" /></span>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{t("expert.toggle")}</span>
        </label>
      </div>

      {!uzman ? (
        <motion.div {...fadeUp} className="card" style={{ marginTop: 20, textAlign: "center", padding: "48px 32px" }}>
          <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>{t("expert.gateTitle")}</div>
          <p className="caption" style={{ maxWidth: 380, margin: "0 auto 20px" }}>{t("expert.gateSub")}</p>
          <button onClick={() => setUzman(true)} className="btn-app" style={{ padding: "12px 26px", fontSize: 15 }}>
            {t("expert.gateBtn")}
          </button>
        </motion.div>
      ) : !cmp ? (
        <Loading text={t("load.analysis")} />
      ) : (
        <div style={{ marginTop: 18 }}>
          <Tabs tabs={TABS} active={tab} onChange={setTab} />

          {tab === "algo" && (
            <motion.div key="algo" {...fadeUp}>
              {enIyi && (
                <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 16 }}>
                  {oracle.map((r, i) => (
                    <motion.div key={r.Politika} className="card"
                      initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.06 }}
                      style={{ flex: 1, minWidth: 140, borderTop: `3px solid ${RENK[r.Politika]}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <b style={{ fontSize: 15 }}>{r.Politika}</b>
                        {r.Politika === enIyi.Politika && (
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#34d399", background: "rgba(52,211,153,0.15)", borderRadius: 999, padding: "2px 8px" }}>{t("expert.best")}</span>
                        )}
                      </div>
                      <div style={{ fontSize: 26, fontWeight: 800, color: RENK[r.Politika], marginTop: 6 }}>
                        {r.mean > 0 ? "+" : ""}{fmtPara(r.mean)}
                      </div>
                      <div className="caption">{t("expert.dailyAvg")} {r.std}</div>
                    </motion.div>
                  ))}
                </div>
              )}

              <div className="card">
                <CardHead renk="#22c55e" baslik={t("expert.perfTitle")} alt={t("expert.perfAlt")} />
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={oracle}>
                    <XAxis dataKey="Politika" stroke="#8a8a8a" />
                    <YAxis stroke="#8a8a8a" tickFormatter={(v) => Math.round(paraCevir(v)).toLocaleString(locale)} label={{ value: paraSuffix.trim() + " / " + t("unit.year"), angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                    <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} cursor={{ fill: "#00000008" }}
                      itemStyle={{ color: "var(--fg)" }} labelStyle={{ color: "var(--fg)" }}
                      formatter={(v) => [fmtPara(v), t("expert.dailyReward")]} />
                    <Bar dataKey="mean" name={t("expert.dailyReward")} radius={[6, 6, 0, 0]} isAnimationActive>
                      {oracle.map((r) => <Cell key={r.Politika} fill={RENK[r.Politika] || "#8a8a8a"} />)}
                      <ErrorBar dataKey="std" stroke="var(--fg)" strokeWidth={1.2} width={5} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {cmp.forecast.length > 0 && (
                <div className="card" style={{ marginTop: 16, overflowX: "auto" }}>
                  <CardHead renk="#f59e0b" baslik={t("expert.forecastTitle")} alt={t("expert.forecastAlt")} />
                  <table className="tbl">
                    <thead><tr>{Object.keys(cmp.forecast[0]).map((k) => <th key={k}>{sutunBaslik(k)}</th>)}</tr></thead>
                    <tbody>{cmp.forecast.map((r, i) => (
                      <tr key={i}>{Object.entries(r).map(([k, v], j) => <td key={j}>{huceDeger(k, v)}</td>)}</tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </motion.div>
          )}

          {tab === "mod" && (
            <motion.div key="mod" {...fadeUp} className="card" style={{ overflowX: "auto" }}>
              <CardHead renk="#3b82f6" baslik={t("expert.modeTitle")} alt={t("expert.modeAlt")} />
              <table className="tbl" style={{ marginTop: 6 }}>
                <thead><tr>
                  <th>{t("expert.policy")}</th>
                  {["Oracle", "Forecast", "Naive"].filter((m) => cmp.pivot[0] && m in cmp.pivot[0]).map((m) => <th key={m}>{m}</th>)}
                </tr></thead>
                <tbody>
                  {cmp.pivot.map((r) => {
                    const vals = ["Oracle", "Forecast", "Naive"].filter((m) => m in r).map((m) => r[m]);
                    const min = Math.min(...vals), max = Math.max(...vals);
                    return (
                      <tr key={r.Politika}>
                        <td><b>{r.Politika}</b></td>
                        {["Oracle", "Forecast", "Naive"].filter((m) => m in r).map((m) => {
                          const tt = max > min ? (r[m] - min) / (max - min) : 0.5;
                          const bg = `rgba(${Math.round(248 - tt * 185)}, ${Math.round(81 + tt * 104)}, ${Math.round(73 + tt * 7)}, 0.26)`;
                          return <td key={m} style={{ background: bg, fontWeight: 600 }}>{parabirimi === "USD" ? paraCevir(Number(r[m])).toFixed(2) : r[m]}</td>;
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginTop: 16 }}>
                {[["Oracle", t("expert.oracleDesc"), "#22c55e"],
                  ["Forecast", t("expert.forecastDesc"), "#3b82f6"],
                  ["Naive", t("expert.naiveDesc"), "#f59e0b"]].map(([b, a, c]) => (
                  <div key={b} style={{ borderLeft: `3px solid ${c}`, paddingLeft: 12 }}>
                    <b style={{ fontSize: 14 }}>{b}</b>
                    <div className="caption">{a}</div>
                  </div>
                ))}
              </div>
              <div className="oneri" style={{ marginTop: 16 }}>{t("expert.modeNote")}</div>
            </motion.div>
          )}

          {tab === "mevsim" && (mev ? (
            <motion.div key="mevsim" {...fadeUp}>
              <div className="card">
                <CardHead renk="#f97316" baslik={`${t("expert.monthlyPrice")} (${mev.yil_araligi[0]}–${mev.yil_araligi[1]})`} alt={t("expert.monthlyPriceAlt")} />
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mev.aylik_fiyat.map((v, i) => ({ ay: aylarKisa[i], fiyat: v, m: i + 1 }))}>
                    <XAxis dataKey="ay" stroke="#8a8a8a" />
                    <YAxis stroke="#8a8a8a" tickFormatter={(v) => Math.round(paraCevir(v)).toLocaleString(locale)} label={{ value: fiyatBirimi, angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                    <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} cursor={{ fill: "#00000008" }}
                      itemStyle={{ color: "var(--fg)" }} labelStyle={{ color: "var(--fg)" }}
                      formatter={(v) => [fmtFiyat(v), t("sim.price")]} />
                    <Bar dataKey="fiyat" radius={[6, 6, 0, 0]} isAnimationActive>
                      {mev.aylik_fiyat.map((_, i) => <Cell key={i} fill={AY_RENK(i + 1)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-2" style={{ marginTop: 16 }}>
                <div className="card">
                  <CardHead renk="#3b82f6" baslik={t("expert.sumWinPrice")} />
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={mev.saatlik}>
                      <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 4, 8, 12, 16, 20]} />
                      <YAxis stroke="#8a8a8a" />
                      <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} />
                      <Legend />
                      <Line dataKey="yaz_fiyat" name={t("expert.summer")} stroke="#f59e0b" strokeWidth={3} dot={false} />
                      <Line dataKey="kis_fiyat" name={t("expert.winter")} stroke="#3b82f6" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="card">
                  <CardHead renk="#22c55e" baslik={t("expert.sumWinSolar")} />
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={mev.saatlik}>
                      <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 4, 8, 12, 16, 20]} />
                      <YAxis stroke="#8a8a8a" />
                      <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} />
                      <Legend />
                      <Area dataKey="yaz_gunes" name={t("expert.summer")} stroke="#f97316" fill="#f9731633" strokeWidth={2} />
                      <Area dataKey="kis_gunes" name={t("expert.winter")} stroke="#3b82f6" fill="#3b82f633" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </motion.div>
          ) : <Loading text={t("load.analysis")} />)}
        </div>
      )}
    </PageWrap>
  );
}
