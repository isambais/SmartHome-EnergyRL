import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, Cell, ErrorBar, Line, LineChart,
  Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";
import { Loading, PageWrap } from "../components/ui.jsx";
import { useApp } from "../state.jsx";

const RENK = { SAC: "#22c55e", TD3: "#3b82f6", PPO: "#f59e0b", A2C: "#f97316" };
const AY_RENK = (m) => ([12, 1, 2].includes(m) ? "#3b82f6" : [3, 4, 5].includes(m) ? "#22c55e" : [6, 7, 8].includes(m) ? "#f59e0b" : "#f97316");
const AY_KISA = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];

const fadeUp = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: "easeOut" },
};

const TABS = [
  { id: "algo", ad: "Algoritma Karşılaştırması" },
  { id: "mod", ad: "Fiyat Bilgisi Etkisi" },
  { id: "mevsim", ad: "Mevsimsel Analiz" },
];

function Tabs({ active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)", marginBottom: 20 }}>
      {TABS.map((t) => (
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

/* Kart başlığı — küçük renkli aksan + başlık + açıklama */
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
  const [tab, setTab] = useState("algo");
  const [cmp, setCmp] = useState(null);
  const [mev, setMev] = useState(null);

  useEffect(() => {
    api.karsilastirma().then(setCmp).catch(() => setCmp({ algoritmalar: [], forecast: [], pivot: [] }));
    api.mevsimsel().then(setMev).catch(() => {});
  }, []);

  const oracle = cmp ? cmp.algoritmalar.filter((r) => r.Mod === "Oracle") : [];
  const enIyi = oracle.length ? oracle.reduce((a, b) => (b.mean > a.mean ? b : a)) : null;

  return (
    <PageWrap>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>Uzman Modu</h1>
          <p className="caption" style={{ maxWidth: 460 }}>
            İşin tekniğini merak edenler için: yapay zekâ yöntemlerinin karşılaştırması,
            tahmin kalitesinin etkisi ve mevsimsel analizler.
          </p>
        </div>
        <label className="toggle-switch">
          <input type="checkbox" checked={uzman} onChange={(e) => setUzman(e.target.checked)} />
          <span className="track"><span className="thumb" /></span>
          <span style={{ fontSize: 14, fontWeight: 600 }}>Teknik detaylar</span>
        </label>
      </div>

      {!uzman ? (
        <motion.div {...fadeUp} className="card"
          style={{ marginTop: 20, textAlign: "center", padding: "48px 32px" }}>
          <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>Bu bölüm teknik detaylar içerir</div>
          <p className="caption" style={{ maxWidth: 380, margin: "0 auto 20px" }}>
            Algoritma karşılaştırmaları ve model analizleri burada. Görmek için teknik detayları açın.
          </p>
          <button onClick={() => setUzman(true)} className="btn-app" style={{ padding: "12px 26px", fontSize: 15 }}>
            Teknik detayları aç
          </button>
        </motion.div>
      ) : !cmp ? (
        <Loading text="Analizler yükleniyor…" />
      ) : (
        <div style={{ marginTop: 18 }}>
          <Tabs active={tab} onChange={setTab} />

          {/* ── Algoritma Karşılaştırması ── */}
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
                          <span style={{ fontSize: 11, fontWeight: 700, color: "#34d399", background: "rgba(52,211,153,0.15)", borderRadius: 999, padding: "2px 8px" }}>en iyi</span>
                        )}
                      </div>
                      <div style={{ fontSize: 26, fontWeight: 800, color: RENK[r.Politika], marginTop: 6 }}>
                        {r.mean > 0 ? "+" : ""}{r.mean} TL
                      </div>
                      <div className="caption">günlük ort. ± {r.std}</div>
                    </motion.div>
                  ))}
                </div>
              )}

              <div className="card">
                <CardHead renk="#22c55e" baslik="Günlük performans (Oracle fiyat bilgisiyle)"
                  alt="Her algoritmanın bir günde sağladığı ortalama net kazanç; çubuk üstü çizgi değişkenliği (±) gösterir." />
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={oracle}>
                    <XAxis dataKey="Politika" stroke="#8a8a8a" />
                    <YAxis stroke="#8a8a8a" label={{ value: "TL / gün", angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                    <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                      cursor={{ fill: "#00000008" }} />
                    <Bar dataKey="mean" name="Günlük ödül" radius={[6, 6, 0, 0]} isAnimationActive>
                      {oracle.map((r) => <Cell key={r.Politika} fill={RENK[r.Politika] || "#8a8a8a"} />)}
                      <ErrorBar dataKey="std" stroke="var(--fg)" strokeWidth={1.2} width={5} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {cmp.forecast.length > 0 && (
                <div className="card" style={{ marginTop: 16, overflowX: "auto" }}>
                  <CardHead renk="#f59e0b" baslik="Fiyat tahmin modelleri"
                    alt="Yarının elektrik fiyatını tahmin eden modellerin doğruluk karşılaştırması." />
                  <table className="tbl">
                    <thead><tr>{Object.keys(cmp.forecast[0]).map((k) => <th key={k}>{k}</th>)}</tr></thead>
                    <tbody>{cmp.forecast.map((r, i) => (
                      <tr key={i}>{Object.values(r).map((v, j) => <td key={j}>{v}</td>)}</tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </motion.div>
          )}

          {/* ── Fiyat Bilgisi Etkisi (pivot) ── */}
          {tab === "mod" && (
            <motion.div key="mod" {...fadeUp} className="card" style={{ overflowX: "auto" }}>
              <CardHead renk="#3b82f6" baslik="Tahmin kalitesi kararı ne kadar etkiliyor?"
                alt="Ajan yarının fiyatını ne kadar iyi bildikçe günlük kazanç nasıl değişiyor (TL/gün)." />
              <table className="tbl" style={{ marginTop: 6 }}>
                <thead><tr>
                  <th>Algoritma</th>
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
                          const t = max > min ? (r[m] - min) / (max - min) : 0.5;
                          const bg = `rgba(${Math.round(248 - t * 185)}, ${Math.round(81 + t * 104)}, ${Math.round(73 + t * 7)}, 0.26)`;
                          return <td key={m} style={{ background: bg, fontWeight: 600 }}>{r[m]}</td>;
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginTop: 16 }}>
                {[["Oracle", "Yarının gerçek fiyatını bilir (ideal üst sınır)", "#22c55e"],
                  ["Forecast", "LightGBM tahmini kullanır (gerçekçi senaryo)", "#3b82f6"],
                  ["Naive", "Bugünün fiyatını yarın sayar (en basit)", "#f59e0b"]].map(([b, a, c]) => (
                  <div key={b} style={{ borderLeft: `3px solid ${c}`, paddingLeft: 12 }}>
                    <b style={{ fontSize: 14 }}>{b}</b>
                    <div className="caption">{a}</div>
                  </div>
                ))}
              </div>
              <div className="oneri" style={{ marginTop: 16 }}>
                Ajan, yarının fiyatını tam bilmese bile (Naive) Oracle'a çok yakın kazanç sağlıyor —
                yani tahmine bağımlı değil, sağlam bir strateji öğrenmiş.
              </div>
            </motion.div>
          )}

          {/* ── Mevsimsel Analiz ── */}
          {tab === "mevsim" && (mev ? (
            <motion.div key="mevsim" {...fadeUp}>
              <div className="card">
                <CardHead renk="#f97316" baslik={`Aylık ortalama elektrik fiyatı (${mev.yil_araligi[0]}–${mev.yil_araligi[1]})`}
                  alt="Renkler mevsimi gösterir — kış mavi, ilkbahar yeşil, yaz sarı, sonbahar turuncu." />
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mev.aylik_fiyat.map((v, i) => ({ ay: AY_KISA[i], fiyat: v, m: i + 1 }))}>
                    <XAxis dataKey="ay" stroke="#8a8a8a" />
                    <YAxis stroke="#8a8a8a" label={{ value: "TL/MWh", angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                    <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                      cursor={{ fill: "#00000008" }} />
                    <Bar dataKey="fiyat" name="Ortalama fiyat" radius={[6, 6, 0, 0]} isAnimationActive>
                      {mev.aylik_fiyat.map((_, i) => <Cell key={i} fill={AY_RENK(i + 1)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-2" style={{ marginTop: 16 }}>
                <div className="card">
                  <CardHead renk="#3b82f6" baslik="Yaz — Kış günlük fiyat profili" />
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={mev.saatlik}>
                      <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 4, 8, 12, 16, 20]} />
                      <YAxis stroke="#8a8a8a" />
                      <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} />
                      <Legend />
                      <Line dataKey="yaz_fiyat" name="Yaz" stroke="#f59e0b" strokeWidth={3} dot={false} />
                      <Line dataKey="kis_fiyat" name="Kış" stroke="#3b82f6" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="card">
                  <CardHead renk="#22c55e" baslik="Yaz — Kış güneş üretim profili" />
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={mev.saatlik}>
                      <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 4, 8, 12, 16, 20]} />
                      <YAxis stroke="#8a8a8a" />
                      <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} />
                      <Legend />
                      <Area dataKey="yaz_gunes" name="Yaz" stroke="#f97316" fill="#f9731633" strokeWidth={2} />
                      <Area dataKey="kis_gunes" name="Kış" stroke="#3b82f6" fill="#3b82f633" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="oneri" style={{ marginTop: 16 }}>
                Yazın fiyat tepesi öğleden sonraya (klima yükü), kışın akşama kayar. Yaz güneş üretimi
                kışın yaklaşık <b>{mev.gunes_orani} katı</b> — ajan yazın öz-tüketim, kışın fiyat farkı
                ağırlıklı çalışır.
              </div>
            </motion.div>
          ) : <Loading text="Mevsimsel veriler yükleniyor…" />)}
        </div>
      )}
    </PageWrap>
  );
}
