import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api.js";
import Building from "../components/Building.jsx";
import { Loading, Metric, PageWrap, useDebounced } from "../components/ui.jsx";
import { useApp } from "../state.jsx";

/* Kart başlığı — küçük renkli aksan + başlık + açıklama */
function CardHead({ renk, baslik, alt }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ width: 4, height: 18, borderRadius: 2, background: renk }} />
        <b style={{ fontSize: 15.5 }}>{baslik}</b>
      </div>
      {alt && <div className="caption" style={{ marginTop: 4, marginLeft: 14 }}>{alt}</div>}
    </div>
  );
}

const KARAR_ETIKET = { "şarj": "depola", "deşarj": "kullan", bekle: "" };

export default function Epias() {
  const { cfg } = useApp();
  const [kesinti, setKesinti] = useState(false);
  const [aralik, setAralik] = useState([18, 21]);
  const [tablo, setTablo] = useState(false);
  const [sim, setSim] = useState(null);
  const [err, setErr] = useState(null);

  const saat = new Date().getHours();
  const kesintiSaatleri = useMemo(
    () => (kesinti ? Array.from({ length: aralik[1] - aralik[0] + 1 }, (_, i) => aralik[0] + i) : []),
    [kesinti, aralik]
  );
  const dReq = useDebounced({ cfg, kesintiSaatleri }, 450);

  useEffect(() => {
    let ok = true;
    api.simulate({
      config: dReq.cfg,
      kesinti_saatleri: dReq.kesintiSaatleri,
    })
      .then((d) => ok && (setSim(d), setErr(null)))
      .catch((e) => ok && setErr(e.message));
    return () => { ok = false; };
  }, [JSON.stringify(dReq)]);

  if (err) return <PageWrap><h1>Canlı EPİAŞ</h1><div className="kesinti-uyari">API'ye ulaşılamadı ({err})</div></PageWrap>;
  if (!sim) return <PageWrap><h1>Canlı EPİAŞ</h1><Loading text="Fiyatlar yükleniyor…" /></PageWrap>;

  const df = sim.rows;
  const r = df[saat];
  const ort = df.reduce((s, x) => s + x.fiyat_tl_mwh, 0) / 24;
  const enUcuz = df.reduce((a, b) => (b.fiyat_tl_mwh < a.fiyat_tl_mwh ? b : a));
  const enPahali = df.reduce((a, b) => (b.fiyat_tl_mwh > a.fiyat_tl_mwh ? b : a));
  const k = df.filter((x) => x.kesinti);
  const karsilanan = k.reduce((s, x) => s + x.talep_kw - x.karsilanmayan_kwh - x.jenerator_kwh, 0);
  const jenKwh = k.reduce((s, x) => s + x.jenerator_kwh, 0);
  const jenTl = k.reduce((s, x) => s + x.maliyet_tl, 0);
  const acik = k.reduce((s, x) => s + x.karsilanmayan_kwh, 0);

  // Tarife karşılaştırması (yaklaşık konut tarifeleri, TL/kWh)
  const TEK = 2.9;
  const ucZamanli = (h) => (h >= 17 && h < 22) ? 4.5 : (h >= 6 && h < 17) ? 2.9 : 1.7;
  const gunlukTuketim = df.reduce((s, x) => s + x.talep_kw, 0);
  const maliyetTek = df.reduce((s, x) => s + x.talep_kw * TEK, 0);
  const maliyetUc = df.reduce((s, x) => s + x.talep_kw * ucZamanli(x.saat), 0);
  const maliyetAkilli = sim.ozet.net_maliyet_tl;
  const tarifeler = [
    { ad: "Tek zamanlı tarife", tl: maliyetTek, renk: "#f59e0b", not: "sabit fiyat, sistem yok" },
    { ad: "Üç zamanlı tarife", tl: maliyetUc, renk: "#f97316", not: "gece ucuz / akşam pahalı, sistem yok" },
    { ad: "Akıllı sistem", tl: maliyetAkilli, renk: "#22c55e", not: "güneş + batarya + saatlik optimizasyon" },
  ];
  const maxTarife = Math.max(maliyetTek, maliyetUc, Math.max(maliyetAkilli, 0.1));

  return (
    <PageWrap>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>Canlı EPİAŞ — Gün Öncesi Piyasası</h1>
          <p className="caption" style={{ maxWidth: 460 }}>
            Elektriğin saatlik fiyatı ve akıllı sistemin bugün her saat ne yaptığı.
          </p>
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <span className="badge">{new Date().toLocaleString("tr-TR")}</span>
          <span className="badge">Veri: {sim.kaynak}</span>
        </div>
      </div>

      <AnimatePresence>
        {kesinti && (
          <motion.div className="kesinti-uyari" style={{ marginTop: 12 }}
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            Kesinti simülasyonu aktif ({String(aralik[0]).padStart(2, "0")}:00–{String(aralik[1]).padStart(2, "0")}:00) —{" "}
            {cfg.jenerator ? "jeneratör devrede, batarya öncelikli kullanılıyor" : "jeneratör yok — yalnızca batarya + güneş"}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-4" style={{ marginTop: 14 }}>
        <Metric i={0} label="Şu anki fiyat" value={r.fiyat_tl_mwh} suffix=" TL/MWh"
          delta={`${(r.fiyat_tl_mwh - ort) >= 0 ? "+" : ""}${(r.fiyat_tl_mwh - ort).toFixed(0)} / ortalama`} />
        <Metric i={1} label="Günün en ucuz saati" value={enUcuz.saat} suffix=":00"
          delta={`${enUcuz.fiyat_tl_mwh.toFixed(0)} TL/MWh`} />
        <Metric i={2} label="Günün en pahalı saati" value={enPahali.saat} suffix=":00"
          delta={`${enPahali.fiyat_tl_mwh.toFixed(0)} TL/MWh`} />
        <Metric i={3} label="Bugünkü tasarruf" value={sim.ozet.tasarruf_tl} suffix=" TL" />
      </div>

      <div className="split epias" style={{ marginTop: 16 }}>
        <motion.div className="card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <CardHead renk="#f59e0b" baslik="Bugünün saatlik elektrik fiyatları"
            alt="Yeşil çubuk: en ucuz saatler (depolama). Kırmızı: en pahalı (kullanım). Sarı: şu an." />
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={df.map((x) => ({ ...x, et: KARAR_ETIKET[x.karar] }))}>
              <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 3, 6, 9, 12, 15, 18, 21]} interval={0} />
              <YAxis stroke="#8a8a8a" />
              <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                cursor={{ fill: "#00000008" }}
                formatter={(v) => [Math.round(v) + " TL/MWh", "Fiyat"]}
                labelFormatter={(l) => `Saat ${String(l).padStart(2, "0")}:00`} />
              <Bar dataKey="fiyat_tl_mwh" radius={[5, 5, 0, 0]} isAnimationActive>
                {df.map((x) => {
                  const p30 = enUcuz.fiyat_tl_mwh + (enPahali.fiyat_tl_mwh - enUcuz.fiyat_tl_mwh) * 0.3;
                  const p70 = enUcuz.fiyat_tl_mwh + (enPahali.fiyat_tl_mwh - enUcuz.fiyat_tl_mwh) * 0.7;
                  const renk = x.kesinti ? "#ef4444"
                    : x.saat === saat ? "#f59e0b"
                    : x.fiyat_tl_mwh <= p30 ? "#86efac"
                    : x.fiyat_tl_mwh >= p70 ? "#fca5a5" : "#e5e1da";
                  return <Cell key={x.saat} fill={renk} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {kesinti && (
            <div className="oneri">
              Kesinti boyunca batarya + güneş <b>{karsilanan.toFixed(1)} kWh</b> karşıladı
              {cfg.jenerator
                ? <> · jeneratör <b>{jenKwh.toFixed(1)} kWh</b> üretti (maliyet {jenTl.toFixed(0)} TL)</>
                : acik > 0.05
                  ? <> · <b>{acik.toFixed(1)} kWh karşılanamadı</b></>
                  : " · tüm talep karşılandı"}
            </div>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.08 }}>
          <div className="card" style={{ marginBottom: 14 }}>
            <CardHead renk="#f97316" baslik="Kesinti senaryosu"
              alt="Elektrik kesildiğinde batarya ve güneşin sizi kaç saat idare edeceğini test edin." />
            <label className="toggle-switch">
              <input type="checkbox" checked={kesinti} onChange={(e) => setKesinti(e.target.checked)} />
              <span className="track"><span className="thumb" /></span>
              <span style={{ fontSize: 14, fontWeight: 600 }}>Elektrik kesintisi simülasyonu</span>
            </label>
            <AnimatePresence>
              {kesinti && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} style={{ overflow: "hidden" }}>
                  <label className="fld">Başlangıç: <b>{aralik[0]}:00</b></label>
                  <input type="range" min="0" max="23" value={aralik[0]}
                    onChange={(e) => setAralik([Math.min(+e.target.value, aralik[1]), aralik[1]])} />
                  <label className="fld">Bitiş: <b>{aralik[1]}:00</b></label>
                  <input type="range" min="0" max="23" value={aralik[1]}
                    onChange={(e) => setAralik([aralik[0], Math.max(+e.target.value, aralik[0])])} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <Building cfg={cfg} saat={saat} soc={r.soc} gunesKw={r.gunes_kw}
            kesinti={kesintiSaatleri.includes(saat)} height={380} />
          <div className="caption" style={{ marginTop: 4 }}>Şu anki saat için bina durumu</div>
        </motion.div>
      </div>

      {/* Tarife karşılaştırması */}
      <motion.div className="card" style={{ marginTop: 16 }}
        initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4 }}>
        <CardHead renk="#22c55e" baslik="Hangi tarife size uygun?"
          alt={`Binanızın bugünkü ${gunlukTuketim.toFixed(0)} kWh tüketimi üç senaryoda (yaklaşık konut tarifeleri).`} />
        {tarifeler.map((t, i) => (
          <div key={t.ad} style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, marginBottom: 4 }}>
              <span><b>{t.ad}</b> <span className="caption">· {t.not}</span></span>
              <b style={{ color: t.renk }}>
                {t.tl < 0 ? `+${Math.abs(Math.round(t.tl))} TL kazanç` : `${Math.round(t.tl)} TL/gün`}
              </b>
            </div>
            <div style={{ height: 12, background: "var(--hover)", borderRadius: 999, overflow: "hidden" }}>
              <motion.div
                initial={{ width: 0 }} whileInView={{ width: `${Math.max(2, 100 * Math.max(t.tl, 0) / maxTarife)}%` }}
                viewport={{ once: true }} transition={{ delay: i * 0.1, duration: 0.6, ease: "easeOut" }}
                style={{ height: "100%", background: t.renk, borderRadius: 999 }} />
            </div>
          </div>
        ))}
        <div className="oneri" style={{ marginTop: 8 }}>
          Akıllı sistem, en ucuz konut tarifesine göre bile günde{" "}
          <b>{Math.round(Math.min(maliyetTek, maliyetUc) - maliyetAkilli)} TL</b> daha az —
          çünkü güneş üretimini ve saatlik fiyat farkını birlikte kullanıyor.
        </div>
      </motion.div>

      <div style={{ marginTop: 16 }}>
        <button onClick={() => setTablo(!tablo)}
          style={{ background: "var(--bg2)", border: "1px solid var(--border)", color: "var(--fg)", borderRadius: 999, padding: "9px 18px", cursor: "pointer", fontWeight: 600, fontSize: 14, fontFamily: "inherit" }}>
          Saat saat karar tablosu {tablo ? "▲" : "▼"}
        </button>
        <AnimatePresence>
          {tablo && (
            <motion.div className="card" style={{ marginTop: 10, overflowX: "auto" }}
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
              <table className="tbl">
                <thead><tr>
                  <th>Saat</th><th>Fiyat (TL/MWh)</th><th>Karar</th><th>Batarya</th>
                  <th>Güneş (kW)</th><th>Talep (kW)</th><th>Maliyet (TL)</th><th>Tasarruf (TL)</th>
                </tr></thead>
                <tbody>
                  {df.map((x) => (
                    <tr key={x.saat} style={x.saat === saat ? { background: "var(--hover)" } : undefined}>
                      <td>{String(x.saat).padStart(2, "0")}:00</td>
                      <td>{x.fiyat_tl_mwh.toFixed(0)}</td>
                      <td>{x.karar}</td>
                      <td>{Math.round(x.soc * 100)}%</td>
                      <td>{x.gunes_kw.toFixed(1)}</td>
                      <td>{x.talep_kw.toFixed(1)}</td>
                      <td>{x.net_maliyet_tl.toFixed(1)}</td>
                      <td>{x.tasarruf_tl.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageWrap>
  );
}
