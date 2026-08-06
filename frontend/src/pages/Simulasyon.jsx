import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Area, ComposedChart, Line, ResponsiveContainer, Scatter,
  Tooltip, XAxis, YAxis, Legend, ReferenceLine,
} from "recharts";
import { api } from "../api.js";
import Building from "../components/Building.jsx";
import ConfigPanel from "../components/ConfigPanel.jsx";
import { Loading, Metric, Oneriler, PageWrap, useDebounced } from "../components/ui.jsx";
import { useApp } from "../state.jsx";

const stripEmoji = (s) =>
  s.replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, "").trim();

/* Ajanın o saatteki kararı — sayfanın en görünür ögesi */
function KararBanner({ karar, saat, fiyat, soc }) {
  const stil = {
    "şarj": {
      bg: "rgba(52,211,153,0.12)", border: "#34d399", renk: "#6ee7b7", etiket: "DEPOLUYOR",
      aciklama: `Elektrik şu an ucuz (${fiyat.toFixed(0)} TL/MWh) — batarya dolduruluyor`,
    },
    "deşarj": {
      bg: "rgba(248,113,113,0.12)", border: "#f87171", renk: "#fca5a5", etiket: "KULLANIYOR",
      aciklama: `Elektrik şu an pahalı (${fiyat.toFixed(0)} TL/MWh) — depodaki ucuz elektrik devrede`,
    },
    bekle: {
      bg: "rgba(255,255,255,0.05)", border: "rgba(255,255,255,0.18)", renk: "#a1a1aa", etiket: "BEKLEMEDE",
      aciklama: "Fiyat nötr bölgede — batarya doluluğu korunuyor",
    },
  }[karar];

  return (
    <motion.div
      key={karar + saat}
      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
      style={{
        background: stil.bg, border: `2px solid ${stil.border}`, borderRadius: 16,
        padding: "16px 24px", marginBottom: 16,
        display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap",
      }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <motion.span
          animate={{ opacity: [1, 0.45, 1] }} transition={{ repeat: Infinity, duration: 1.6 }}
          style={{ width: 14, height: 14, borderRadius: "50%", background: stil.border, boxShadow: `0 0 12px ${stil.border}` }} />
        <span style={{ fontSize: 15, color: stil.renk, fontWeight: 600 }}>
          Saat {String(saat).padStart(2, "0")}:00 — ajan şu an
        </span>
        <span style={{ fontSize: 30, fontWeight: 800, letterSpacing: "0.01em", color: stil.renk }}>
          {stil.etiket}
        </span>
      </div>
      <span style={{ fontSize: 14.5, color: stil.renk, opacity: 0.9 }}>{stil.aciklama}</span>
      <span style={{ marginLeft: "auto", fontSize: 14, fontWeight: 700, color: stil.renk }}>
        Batarya %{Math.round(soc * 100)}
      </span>
    </motion.div>
  );
}

export default function Simulasyon() {
  const { cfg, saat, setSaat, ay } = useApp();
  const dCfg = useDebounced(cfg, 450);
  const [sim, setSim] = useState(null);
  const [err, setErr] = useState(null);

  const tarih = `${new Date().getFullYear()}-${String(ay).padStart(2, "0")}-15`;

  useEffect(() => {
    let ok = true;
    api.simulate({ config: dCfg, tarih })
      .then((d) => ok && (setSim(d), setErr(null)))
      .catch((e) => ok && setErr(e.message));
    return () => { ok = false; };
  }, [JSON.stringify(dCfg), tarih]);

  if (err) return <PageWrap><h1>Bina Simülasyonu</h1><div className="kesinti-uyari">API'ye ulaşılamadı ({err}) — backend çalışıyor mu?</div></PageWrap>;
  if (!sim) return <PageWrap><h1>Bina Simülasyonu</h1><Loading /></PageWrap>;

  const df = sim.rows;
  const r = df[saat];
  const d = sim.derived;
  const chart = df.map((x) => ({
    ...x,
    soc_pct: +(x.soc * 100).toFixed(0),
    sarj_f: x.karar === "şarj" ? x.fiyat_tl_mwh : null,
    desarj_f: x.karar === "deşarj" ? x.fiyat_tl_mwh : null,
  }));
  const kararTxt = {
    "şarj": "ucuz elektrik depolanıyor",
    "deşarj": "depodaki elektrik kullanılıyor",
    bekle: "hazırda — doluluk korunuyor",
  };
  const tasarrufPct = Math.round(100 * sim.ozet.tasarruf_tl / Math.max(sim.ozet.taban_maliyet_tl, 0.01));

  return (
    <PageWrap>
      <h1>Bina Simülasyonu</h1>

      {/* Kullanım rehberi */}
      <div className="oneri" style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
        <span><b>1.</b> Soldan binanızı tarif edin</span>
        <span><b>2.</b> Binanın altındaki saat çubuğuyla günü gezin</span>
        <span><b>3.</b> Sonuçlar anında güncellenir</span>
        <span style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 7, fontSize: 13, color: "#34d399", fontWeight: 700 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
          Otomatik hesaplanıyor — başlat butonuna gerek yok
        </span>
      </div>

      {/* Ajanın kararı — büyük ve net */}
      <KararBanner karar={r.karar} saat={saat} fiyat={r.fiyat_tl_mwh} soc={r.soc} />

      {/* Sol: konfigüratör · Sağ: 3D bina + saat çubuğu */}
      <div className="split cfg">
        <div className="card"><ConfigPanel showSaat={false} /></div>

        <div>
          <Building cfg={cfg} saat={saat} soc={r.soc} gunesKw={r.gunes_kw} height={440} />

          {/* BÜYÜK saat kaydırıcısı — ana kontrol */}
          <div className="card" style={{ marginTop: 12, padding: "18px 26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
              <b style={{ fontSize: 16 }}>Günün saati</b>
              <span style={{ fontSize: 30, fontWeight: 800, color: "var(--blue)", fontVariantNumeric: "tabular-nums" }}>
                {String(saat).padStart(2, "0")}:00
              </span>
            </div>
            <input
              type="range" min="0" max="23" value={saat}
              onChange={(e) => setSaat(+e.target.value)}
              style={{ width: "100%", height: 34, accentColor: "var(--blue)", cursor: "pointer" }}
              aria-label="Günün saati" />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
              <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>23:00</span>
            </div>
          </div>

          <div className="caption" style={{ marginTop: 8 }}>
            Sürükle: döndür · Tekerlek: yakınlaştır — Panel: <b>{d.panel_sayisi} adet ({d.panel_kw} kW)</b> ·
            Batarya: <b>{d.batarya_kwh} kWh</b> · Günlük tüketim: <b>{d.gunluk_tuketim_kwh} kWh</b> ·
            Veri: {sim.kaynak} · Ajan: {sim.ajan}
          </div>
        </div>
      </div>

      {/* Metrikler — tam genişlik */}
      <div className="grid grid-4" style={{ marginTop: 16 }}>
        <Metric i={0} label="Bugünkü tasarruf" value={sim.ozet.tasarruf_tl} suffix=" TL"
          delta={tasarrufPct >= 100
            ? "bugünkü fatura sıfırlandı, üstüne kazanç var"
            : `faturanın %${Math.max(tasarrufPct, 0)}'i kadar tasarruf`} />
        <Metric i={1} label="Batarya seviyesi" value={r.soc * 100} suffix="%" delta={kararTxt[r.karar]} />
        <Metric i={2} label="Güneş üretimi" value={r.gunes_kw} decimals={1} suffix=" kW"
          delta={`gün toplamı ${sim.ozet.gunes_kwh} kWh`} />
        <Metric i={3} label="Toplam tüketim" value={sim.ozet.talep_kwh} suffix=" kWh"
          delta={`şu an ${r.talep_kw.toFixed(1)} kW`} />
      </div>

      {/* Fatura karşılaştırması + batarya verimi */}
      <div className="split wide-l" style={{ marginTop: 16 }}>
        <div className="card">
          <b>Bugünkü fatura karşılaştırması</b>
          <div style={{ display: "flex", gap: 14, marginTop: 14, alignItems: "flex-end" }}>
            <div style={{ flex: 1 }}>
              <div className="caption">Sistem olmadan</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: "#fca5a5" }}>{Math.round(sim.ozet.taban_maliyet_tl)} TL</div>
              <div style={{ height: 10, background: "rgba(248,113,113,0.15)", borderRadius: 999, marginTop: 6 }}>
                <div style={{ width: "100%", height: "100%", background: "#ef4444", borderRadius: 999 }} />
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div className="caption">Akıllı sistemle</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: "#34d399" }}>
                {Math.round(sim.ozet.net_maliyet_tl)} TL
              </div>
              <div style={{ height: 10, background: "rgba(52,211,153,0.15)", borderRadius: 999, marginTop: 6 }}>
                <div style={{
                  width: `${Math.max(0, Math.min(100, 100 * sim.ozet.net_maliyet_tl / Math.max(sim.ozet.taban_maliyet_tl, 0.01)))}%`,
                  height: "100%", background: "#22c55e", borderRadius: 999,
                }} />
              </div>
            </div>
          </div>
          <div className="oneri" style={{ marginTop: 14 }}>
            {sim.ozet.net_maliyet_tl < 0
              ? <>Bu gün fatura yerine <b>{Math.abs(Math.round(sim.ozet.net_maliyet_tl))} TL kazanç</b> — güneş fazlası şebekeye satıldı.</>
              : <>Bu gün cebinizde kalan: <b>{Math.round(sim.ozet.tasarruf_tl)} TL</b> (yılda ~{Math.round(sim.ozet.tasarruf_tl * 365).toLocaleString("tr-TR")} TL)</>}
          </div>
        </div>

        <div className="card">
          <b>Batarya verimi — {sim.tarih ? new Date(sim.tarih).toLocaleDateString("tr-TR", { month: "long" }) : ""}</b>
          <div style={{ fontSize: 40, fontWeight: 800, color: "#3b82f6", marginTop: 8 }}>
            %{sim.batarya_verim_pct}
          </div>
          <div className="caption" style={{ marginTop: 4 }}>
            Lityum batarya soğukta enerjinin bir kısmını kaybeder. Kışın verim düşer,
            yazın tam kapasiteye çıkar — sol menüden ayı değiştirip farkı görebilirsiniz.
          </div>
          <div style={{ height: 8, background: "rgba(96,165,250,0.15)", borderRadius: 999, marginTop: 12 }}>
            <div style={{ width: `${sim.batarya_verim_pct}%`, height: "100%", background: "#3b82f6", borderRadius: 999 }} />
          </div>
        </div>
      </div>

      {/* Grafik — tam genişlik, geniş alan */}
      <div className="card" style={{ marginTop: 16 }}>
        <b>24 saatlik plan — fiyat, batarya ve ajan kararları</b>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chart}>
            <XAxis dataKey="saat" stroke="#8a8a8a" ticks={[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]} interval={0} />
            <YAxis yAxisId="tl" stroke="#8a8a8a" label={{ value: "TL/MWh", angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
            <YAxis yAxisId="pct" orientation="right" stroke="#8a8a8a" />
            <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }} />
            <Legend />
            <Area yAxisId="pct" dataKey="gunes_kw" name="Güneş (kW)" fill="#f9731640" stroke="#f97316" />
            <Line yAxisId="tl" dataKey="fiyat_tl_mwh" name="Elektrik fiyatı (TL/MWh)" stroke="#f59e0b" strokeWidth={2.5} dot={false} />
            <Line yAxisId="pct" dataKey="soc_pct" name="Batarya doluluğu (%)" stroke="#22c55e" strokeWidth={2.5} dot={false} />
            <Scatter yAxisId="tl" dataKey="sarj_f" name="Depolama kararı" fill="#3b82f6" shape="triangle" />
            <Scatter yAxisId="tl" dataKey="desarj_f" name="Kullanma kararı" fill="#ef4444" shape="triangle" />
            <ReferenceLine yAxisId="tl" x={saat} stroke="#8a8a8a" strokeDasharray="4 4" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <h2>Şu anki öneriler</h2>
      <Oneriler items={(sim.oneriler[saat] || []).map(stripEmoji)} />
    </PageWrap>
  );
}
