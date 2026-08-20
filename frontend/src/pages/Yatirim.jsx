import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, Cell, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";
import { Loading, Metric, PageWrap, useDebounced } from "../components/ui.jsx";
import { useApp } from "../state.jsx";
import { AYLAR_FULL, AYLAR_KISA, useI18n } from "../i18n.jsx";

const AY_RENK = (m) => ([12, 1, 2].includes(m) ? "#3b82f6" : [3, 4, 5].includes(m) ? "#22c55e" : [6, 7, 8].includes(m) ? "#f59e0b" : "#f97316");

/* Yazdırılabilir PDF — seçili dile göre */
function raporYazdir(d, cfg, t, aylar, locale, fmtPara) {
  const w = window.open("", "_blank");
  if (!w) return;
  const satir = (a, b) => `<tr><td>${a}</td><td style="text-align:right;font-weight:700">${b}</td></tr>`;
  w.document.write(`
    <html dir="${locale === "ar" ? "rtl" : "ltr"}"><head><title>SmartHome Energy — ${t("invest.title")}</title>
    <style>
      body{font-family:system-ui,sans-serif;color:#1b1b1b;max-width:720px;margin:32px auto;padding:0 24px}
      h1{font-size:24px} h2{font-size:16px;margin-top:26px;border-bottom:2px solid #22c55e;padding-bottom:6px}
      table{width:100%;border-collapse:collapse;margin-top:10px}
      td{padding:8px 6px;border-bottom:1px solid #eee;font-size:14px}
      .big{font-size:30px;font-weight:800;color:#22c55e} .muted{color:#6b6b6b;font-size:13px}
    </style></head><body>
    <h1>SmartHome Energy — ${t("invest.title")}</h1>
    <div class="muted">${new Date().toLocaleDateString(locale)} · ${t(`btype.${cfg.bina_tipi}`)}, ${cfg.kat} ${t("profile.floors")}, ${cfg.aktif_daire} ${t("profile.activeFlats")}</div>
    <table style="margin-top:18px">
      ${satir(t("invest.total"), fmtPara(d.toplam_yatirim))}
      ${satir(t("m.yearlySaving"), fmtPara(d.yillik_tasarruf))}
      ${satir(t("m.payback"), d.amorti_yil + " " + t("unit.year"))}
      ${satir(t("invest.solarProd"), d.yillik_uretim_kwh.toLocaleString(locale) + " kWh")}
      ${satir(t("m.co2"), d.co2_ton + " " + t("unit.ton"))}
    </table>
    <h2>${t("invest.monthly")}</h2>
    <table>
      ${(d.aylik || []).map((a) => satir(aylar[a.ay - 1], fmtPara(a.tasarruf))).join("")}
    </table>
    </body></html>`);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
}

export default function Yatirim() {
  const { cfg } = useApp();
  const { t, dil, parabirimi, paraCevir, fmtPara, paraSuffix, kur } = useI18n();
  // Giriş kutuları: state TL tutar; USD seçil/görüntülenir, TL'ye çevrilerek saklanır
  const girisGoster = (tl) => (parabirimi === "USD" ? Math.round(paraCevir(tl)) : tl);
  const girisSakla = (girilen) => (parabirimi === "USD" ? Math.round((+girilen || 0) * kur) : (+girilen || 0));
  const girisAdim = parabirimi === "USD" ? 250 : 10000;
  const [bataryaTl, setBataryaTl] = useState(null);
  const [panelTl, setPanelTl] = useState(null);
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);
  const locale = dil === "ar" ? "ar" : dil === "en" ? "en-US" : "tr-TR";
  const aylar = AYLAR_FULL[dil] || AYLAR_FULL.tr;
  const aylarKisa = AYLAR_KISA[dil] || AYLAR_KISA.tr;

  const dReq = useDebounced({ cfg, bataryaTl, panelTl }, 500);

  useEffect(() => {
    let ok = true;
    api.yatirim({ config: dReq.cfg, batarya_tl: dReq.bataryaTl, panel_tl: dReq.panelTl })
      .then((x) => ok && (setD(x), setErr(null)))
      .catch((e) => ok && setErr(e.message));
    return () => { ok = false; };
  }, [JSON.stringify(dReq)]);

  if (err) return <PageWrap><h1>{t("invest.title")}</h1><div className="kesinti-uyari">{t("common.apidown")} ({err})</div></PageWrap>;
  if (!d) return <PageWrap><h1>{t("invest.title")}</h1><Loading text={t("load.invest")} /></PageWrap>;

  const amortiGoster = Math.min(isFinite(d.amorti_yil) ? d.amorti_yil : 99, 99);
  const yillar = Array.from({ length: Math.max(Math.ceil(amortiGoster) + 6, 10) }, (_, i) => ({ yil: i, kumulatif: i * d.yillik_tasarruf }));
  const kisalma30 = isFinite(d.yillik_tasarruf) && d.yillik_tasarruf > 0
    ? d.amorti_yil - d.toplam_yatirim / (d.yillik_tasarruf * 1.3)
    : 0;
  const aylikChart = (d.aylik || []).map((a) => ({ ...a, ad: aylarKisa[a.ay - 1] }));
  // Grafik eksen etiketi — TL'de "k" (bin), USD'de düz sayı. Değer TL alanında; sadece etiket çevrilir.
  const eksenFmt = (v) => (parabirimi === "USD"
    ? Math.round(paraCevir(v)).toLocaleString(locale)
    : (v / 1000).toFixed(0) + "k");

  return (
    <PageWrap>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <h1 style={{ margin: 0 }}>{t("invest.title")}</h1>
        <button onClick={() => raporYazdir(d, cfg, t, aylar, locale, fmtPara)} className="btn-app ghost" style={{ padding: "11px 20px", fontSize: 14.5 }}>
          {t("invest.pdf")}
        </button>
      </div>

      <div className="split cfg" style={{ marginTop: 14 }}>
        <div className="card">
          <b>{t("invest.costs")}</b>
          <label className="fld">{t("invest.battCost")} ({paraSuffix.trim()}) — {fmtPara(d.varsayilan_batarya_tl)}</label>
          <input type="number" step={girisAdim} min="0" max={parabirimi === "USD" ? 500000 : 20000000}
            value={girisGoster(bataryaTl ?? d.varsayilan_batarya_tl)}
            onChange={(e) => setBataryaTl(girisSakla(e.target.value))} />
          <label className="fld">{t("invest.panelCost")} ({paraSuffix.trim()}) — {fmtPara(d.varsayilan_panel_tl)}</label>
          <input type="number" step={girisAdim} min="0" max={parabirimi === "USD" ? 500000 : 20000000}
            value={girisGoster(panelTl ?? d.varsayilan_panel_tl)}
            onChange={(e) => setPanelTl(girisSakla(e.target.value))} />
          <div className="caption" style={{ marginTop: 12 }}>{t("invest.costsNote")}</div>
        </div>

        <div>
          <div className="grid grid-4">
            <Metric i={0} label={t("invest.total")} value={d.toplam_yatirim} para />
            <Metric i={1} label={t("m.yearlySaving")} value={d.yillik_tasarruf} para />
            <Metric i={2} label={t("m.payback")} value={isFinite(d.amorti_yil) ? d.amorti_yil : 99} decimals={1} suffix={" " + t("unit.year")} />
            <Metric i={3} label={t("m.co2")} value={d.co2_ton} decimals={1} suffix={" " + t("unit.ton")} />
          </div>

          <div className="oneri" style={{ marginTop: 14 }}>
            {t("invest.envNote").replace("{y}", d.amorti_yil).replace("{a}", d.agac).replace("{c}", d.araba)}
          </div>

          <div className="card" style={{ marginTop: 14 }}>
            <b>{t("invest.monthly")}</b>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={aylikChart}>
                <XAxis dataKey="ad" stroke="#8a8a8a" />
                <YAxis stroke="#8a8a8a" tickFormatter={eksenFmt} />
                <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                  itemStyle={{ color: "var(--fg)" }} labelStyle={{ color: "var(--fg)" }}
                  formatter={(v) => [fmtPara(v), t("m.yearlySaving")]}
                  labelFormatter={(l, p) => { const a = p?.[0]?.payload; return a ? aylar[a.ay - 1] : l; }} />
                <Bar dataKey="tasarruf" radius={[6, 6, 0, 0]}>
                  {aylikChart.map((a) => <Cell key={a.ay} fill={AY_RENK(a.ay)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="caption">{t("invest.monthlyNote")}</div>
          </div>

          <div className="grid grid-2" style={{ marginTop: 14 }}>
            <div className="card">
              <b>{t("invest.payChart")}</b>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={yillar}>
                  <XAxis dataKey="yil" stroke="#8a8a8a" label={{ value: t("unit.year"), position: "insideBottom", offset: -2, fill: "#8a8a8a" }} />
                  <YAxis stroke="#8a8a8a" tickFormatter={eksenFmt} />
                  <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                    itemStyle={{ color: "var(--fg)" }} labelStyle={{ color: "var(--fg)" }}
                    formatter={(v) => fmtPara(v)} />
                  <Area dataKey="kumulatif" name={t("invest.cumSaving")} stroke="#22c55e" strokeWidth={3} fill="#22c55e26" />
                  <ReferenceLine y={d.toplam_yatirim} stroke="#f59e0b" strokeDasharray="6 4"
                    label={{ value: `${t("invest.investLine")}: ${fmtPara(d.toplam_yatirim)}`, fill: "#f59e0b", fontSize: 12 }} />
                  <ReferenceLine x={d.amorti_yil} stroke="#3b82f6" strokeDasharray="2 4"
                    label={{ value: `${t("invest.paybackLine")}: ${d.amorti_yil}`, fill: "#3b82f6", fontSize: 12 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <b>{t("invest.sensitivity")}</b>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={d.duyarlilik}>
                  <XAxis dataKey="artis" stroke="#8a8a8a" label={{ value: t("invest.priceRise"), position: "insideBottom", offset: -2, fill: "#8a8a8a" }} />
                  <YAxis stroke="#8a8a8a" label={{ value: t("invest.paybackYr"), angle: -90, position: "insideLeft", fill: "#8a8a8a" }} />
                  <Tooltip contentStyle={{ background: "var(--chart-tip)", border: "1px solid var(--border)", borderRadius: 10, color: "var(--fg)" }}
                    itemStyle={{ color: "var(--fg)" }} labelStyle={{ color: "var(--fg)" }}
                    formatter={(v) => v + " " + t("unit.year")} labelFormatter={(l) => `+${l}%`} />
                  <Line dataKey="amorti" name={t("m.payback")} stroke="#f97316" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
              <div className="oneri">
                {t("invest.sensNote").replace("{x}", kisalma30.toFixed(1)).replace("{y}", (d.amorti_yil - kisalma30).toFixed(1))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrap>
  );
}
