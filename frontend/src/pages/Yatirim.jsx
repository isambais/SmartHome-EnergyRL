import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, Cell, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";
import { AYLAR } from "../components/ConfigPanel.jsx";
import { Loading, Metric, PageWrap, useDebounced } from "../components/ui.jsx";
import { useApp } from "../state.jsx";

const AY_KISA = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
const AY_RENK = (m) => ([12, 1, 2].includes(m) ? "#3b82f6" : [3, 4, 5].includes(m) ? "#22c55e" : [6, 7, 8].includes(m) ? "#f59e0b" : "#f97316");

/* Basit yazdırılabilir PDF — tarayıcının kendi yazdır/PDF diyaloğunu açar */
function raporYazdir(d, cfg) {
  const w = window.open("", "_blank");
  if (!w) return;
  const satir = (a, b) => `<tr><td>${a}</td><td style="text-align:right;font-weight:700">${b}</td></tr>`;
  w.document.write(`
    <html><head><title>SmartHome Energy — Yatırım Raporu</title>
    <style>
      body{font-family:system-ui,sans-serif;color:#1b1b1b;max-width:720px;margin:32px auto;padding:0 24px}
      h1{font-size:24px} h2{font-size:16px;margin-top:26px;border-bottom:2px solid #22c55e;padding-bottom:6px}
      table{width:100%;border-collapse:collapse;margin-top:10px}
      td{padding:8px 6px;border-bottom:1px solid #eee;font-size:14px}
      .big{font-size:30px;font-weight:800;color:#22c55e}
      .muted{color:#6b6b6b;font-size:13px}
    </style></head><body>
    <h1>SmartHome Energy — Yatırım Raporu</h1>
    <div class="muted">${new Date().toLocaleDateString("tr-TR")} · Bina: ${cfg.bina_tipi}, ${cfg.kat} kat, ${cfg.aktif_daire} aktif daire</div>
    <h2>Özet</h2>
    <div class="big">${d.amorti_yil} yılda kendini amorti eder</div>
    <table>
      ${satir("Toplam yatırım", d.toplam_yatirim.toLocaleString("tr-TR") + " TL")}
      ${satir("Yıllık tasarruf", d.yillik_tasarruf.toLocaleString("tr-TR") + " TL")}
      ${satir("Amorti süresi", d.amorti_yil + " yıl")}
      ${satir("Yıllık güneş üretimi", d.yillik_uretim_kwh.toLocaleString("tr-TR") + " kWh")}
    </table>
    <h2>Çevresel Etki</h2>
    <table>
      ${satir("Yıllık CO₂ tasarrufu", d.co2_ton + " ton")}
      ${satir("Eşdeğer ağaç", d.agac + " ağaç/yıl")}
      ${satir("Eşdeğer araç emisyonu", d.araba + " araç/yıl")}
    </table>
    <h2>Aylık Tasarruf</h2>
    <table>
      ${(d.aylik || []).map((a) => satir(AYLAR[a.ay - 1], Math.round(a.tasarruf).toLocaleString("tr-TR") + " TL  ·  batarya verimi %" + a.batarya_verim)).join("")}
    </table>
    <p class="muted" style="margin-top:24px">Bu rapor bir simülasyon tahminidir; gerçek tasarruf tüketim alışkanlıkları ve fiyat değişimlerine göre farklılık gösterebilir.</p>
    </body></html>`);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
}

export default function Yatirim() {
  const { cfg } = useApp();
  const [bataryaTl, setBataryaTl] = useState(null);
  const [panelTl, setPanelTl] = useState(null);
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);

  const dReq = useDebounced({ cfg, bataryaTl, panelTl }, 500);

  useEffect(() => {
    let ok = true;
    api.yatirim({ config: dReq.cfg, batarya_tl: dReq.bataryaTl, panel_tl: dReq.panelTl })
      .then((x) => ok && (setD(x), setErr(null)))
      .catch((e) => ok && setErr(e.message));
    return () => { ok = false; };
  }, [JSON.stringify(dReq)]);

  if (err) return <PageWrap><h1>Yatırım & Çevre Analizi</h1><div className="kesinti-uyari">API'ye ulaşılamadı ({err})</div></PageWrap>;
  if (!d) return <PageWrap><h1>Yatırım & Çevre Analizi</h1><Loading text="12 aylık simülasyon çalışıyor…" /></PageWrap>;

  const yillar = Array.from({ length: Math.max(Math.ceil(d.amorti_yil) + 6, 10) }, (_, i) => ({
    yil: i, kumulatif: i * d.yillik_tasarruf,
  }));
  const kisalma30 = d.amorti_yil - d.toplam_yatirim / (d.yillik_tasarruf * 1.3);
  const aylikChart = (d.aylik || []).map((a) => ({ ...a, ad: AY_KISA[a.ay - 1] }));

  return (
    <PageWrap>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <h1 style={{ margin: 0 }}>Yatırım & Çevre Analizi</h1>
        <button onClick={() => raporYazdir(d, cfg)} className="btn-app ghost" style={{ padding: "11px 20px", fontSize: 14.5 }}>
          Raporu indir (PDF)
        </button>
      </div>

      <div className="split cfg" style={{ marginTop: 14 }}>
        <div className="card">
          <b>Yatırım Maliyetleri</b>
          <label className="fld">Batarya maliyeti (TL) — öneri: {d.varsayilan_batarya_tl.toLocaleString("tr-TR")}</label>
          <input type="number" step="10000" min="0"
            value={bataryaTl ?? d.varsayilan_batarya_tl}
            onChange={(e) => setBataryaTl(+e.target.value || 0)} />
          <label className="fld">Panel maliyeti (TL) — öneri: {d.varsayilan_panel_tl.toLocaleString("tr-TR")}</label>
          <input type="number" step="10000" min="0"
            value={panelTl ?? d.varsayilan_panel_tl}
            onChange={(e) => setPanelTl(+e.target.value || 0)} />
          <div className="caption" style={{ marginTop: 12 }}>
            Değerler senin binana özel; 12 ayın her biri ayrı simüle edilip toplandı.
          </div>
        </div>

        <div>
          <div className="grid grid-4">
            <Metric i={0} label="Toplam yatırım" value={d.toplam_yatirim} suffix=" TL" />
            <Metric i={1} label="Yıllık tasarruf" value={d.yillik_tasarruf} suffix=" TL" />
            <Metric i={2} label="Amorti süresi" value={d.amorti_yil} decimals={1} suffix=" yıl" />
            <Metric i={3} label="Yıllık CO₂ tasarrufu" value={d.co2_ton} decimals={1} suffix=" ton" />
          </div>

          <div className="oneri" style={{ marginTop: 14 }}>
            Sisteminiz <b>{d.amorti_yil} yılda</b> kendini amorti ediyor; yılda <b>{d.agac} ağacın</b> tuttuğu
            kadar CO₂ tasarrufu sağlıyor — bu <b>{d.araba} arabanın</b> yıllık emisyonuna eşit.
          </div>

          {/* Aylık tasarruf — YENİ */}
          <div className="card" style={{ marginTop: 14 }}>
            <b>Ay ay tasarruf — hangi ay ne kadar kazandırıyor?</b>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={aylikChart}>
                <XAxis dataKey="ad" stroke="#8a8a8a" />
                <YAxis stroke="#8a8a8a" tickFormatter={(v) => (v / 1000).toFixed(0) + "k"} />
                <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                  formatter={(v, n) => n === "tasarruf"
                    ? [Math.round(v).toLocaleString("tr-TR") + " TL", "Aylık tasarruf"]
                    : [v, n]}
                  labelFormatter={(l, p) => {
                    const ay = p?.[0]?.payload;
                    return ay ? `${AYLAR[ay.ay - 1]} · batarya verimi %${ay.batarya_verim}` : l;
                  }} />
                <Bar dataKey="tasarruf" name="tasarruf" radius={[6, 6, 0, 0]}>
                  {aylikChart.map((a) => <Cell key={a.ay} fill={AY_RENK(a.ay)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="caption">
              Yazın güneş bol → tasarruf yüksek; kışın güneş az + batarya verimi düşük → tasarruf azalır.
              Renkler mevsimi gösterir (mavi kış, yeşil ilkbahar, sarı yaz, turuncu sonbahar).
            </div>
          </div>

          <div className="grid grid-2" style={{ marginTop: 14 }}>
            <div className="card">
              <b>Amorti süresi — kümülatif tasarruf vs yatırım</b>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={yillar}>
                  <XAxis dataKey="yil" stroke="#8a8a8a" label={{ value: "Yıl", position: "insideBottom", offset: -2, fill: "#8a8a8a" }} />
                  <YAxis stroke="#8a8a8a" tickFormatter={(v) => (v / 1000).toFixed(0) + "k"} />
                  <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                    formatter={(v) => Math.round(v).toLocaleString("tr-TR") + " TL"} />
                  <Area dataKey="kumulatif" name="Kümülatif tasarruf" stroke="#22c55e" strokeWidth={3} fill="#22c55e26" />
                  <ReferenceLine y={d.toplam_yatirim} stroke="#f59e0b" strokeDasharray="6 4"
                    label={{ value: `Yatırım: ${d.toplam_yatirim.toLocaleString("tr-TR")} TL`, fill: "#f59e0b", fontSize: 12 }} />
                  <ReferenceLine x={d.amorti_yil} stroke="#3b82f6" strokeDasharray="2 4"
                    label={{ value: `Amorti: ${d.amorti_yil} yıl`, fill: "#3b82f6", fontSize: 12 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <b>Fiyat duyarlılık analizi</b>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={d.duyarlilik}>
                  <XAxis dataKey="artis" stroke="#8a8a8a"
                    label={{ value: "Elektrik fiyat artışı (%)", position: "insideBottom", offset: -2, fill: "#8a8a8a" }} />
                  <YAxis stroke="#8a8a8a" label={{ value: "Amorti (yıl)", angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                  <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                    formatter={(v) => v + " yıl"} labelFormatter={(l) => `+%${l} fiyat artışı`} />
                  <Line dataKey="amorti" name="Amorti süresi" stroke="#f97316" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
              <div className="oneri">
                Elektrik fiyatları <b>%30 artarsa</b> amorti süresi <b>{kisalma30.toFixed(1)} yıl
                kısalarak {(d.amorti_yil - kisalma30).toFixed(1)} yıla</b> iner.
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrap>
  );
}
