import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Chip, Loading, Metric, PageHeader, PageWrap, Section } from "../components/ui.jsx";
import { Arrow, Chart, Coins, Gauge, Home, Shield, Star, Sun } from "../icons.jsx";
import { useApp } from "../state.jsx";

const inpStil = {
  width: "100%", background: "var(--bg3)", border: "1px solid var(--border)",
  color: "var(--fg)", borderRadius: 8, padding: "9px 11px", fontSize: 14, fontFamily: "inherit",
};

export default function Profil() {
  const { user, cfg, setCfg } = useApp();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [yatirim, setYatirim] = useState(null);

  // Şifre değiştirme
  const [eski, setEski] = useState("");
  const [yeni, setYeni] = useState("");
  const [sifreMsj, setSifreMsj] = useState(null);

  const yukle = () => api.profile().then(setData).catch((e) => setErr(e.message));

  useEffect(() => { yukle(); }, []);

  // Kayıtlı binaya göre tasarruf özeti
  useEffect(() => {
    const bina = data?.user?.bina;
    if (bina) api.yatirim({ config: bina }).then(setYatirim).catch(() => {});
  }, [JSON.stringify(data?.user?.bina)]);

  if (err) return <PageWrap><h1>Profil</h1><div className="kesinti-uyari">Yüklenemedi ({err})</div></PageWrap>;
  if (!data) return <PageWrap><h1>Profil</h1><Loading text="Profil yükleniyor…" /></PageWrap>;

  const bina = data.user.bina;

  const sifreGonder = async (e) => {
    e.preventDefault();
    setSifreMsj(null);
    try {
      await api.sifreDegistir(eski, yeni);
      setSifreMsj({ ok: true, t: "Şifre güncellendi." });
      setEski(""); setYeni("");
    } catch (er) { setSifreMsj({ ok: false, t: er.message }); }
  };

  return (
    <PageWrap>
      <PageHeader
        title="Profil"
        subtitle="Hesabın, kayıtlı binan ve simülasyon geçmişin. Yaptığın her değişiklik otomatik kaydedilir."
        right={<Chip icon={Star} accent="#34d399">Hesap aktif</Chip>}
      />

      {/* Profil bandı */}
      <motion.div className="card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
        style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap", padding: 22 }}>
        <div style={{
          width: 62, height: 62, borderRadius: "50%", flexShrink: 0,
          background: "linear-gradient(135deg,#34d399,#10b981)", color: "#04120c",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 26, fontWeight: 800, boxShadow: "0 0 26px -4px #34d399aa",
        }}>{(data.user.ad || "K").charAt(0).toUpperCase()}</div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>{data.user.ad}</div>
          <div className="caption" style={{ fontSize: 13.5 }}>{data.user.email}</div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Chip icon={Star}>Üyelik {new Date(data.user.created_at).toLocaleDateString("tr-TR")}</Chip>
          {bina && <Chip icon={Home} accent="#60a5fa">{bina.bina_tipi}</Chip>}
          <Chip icon={Chart} accent="#fb923c">{data.gecmis.length} simülasyon</Chip>
        </div>
      </motion.div>

      {/* KPI'lar */}
      {yatirim && (
        <div className="grid grid-4" style={{ marginTop: 16 }}>
          <Metric i={0} icon={Coins}  accent="#34d399" label="Yıllık tasarruf" value={yatirim.yillik_tasarruf} suffix=" TL" />
          <Metric i={1} icon={Gauge}  accent="#60a5fa" label="Amorti süresi"   value={yatirim.amorti_yil} decimals={1} suffix=" yıl" />
          <Metric i={2} icon={Shield} accent="#a78bfa" label="Yıllık CO₂"       value={yatirim.co2_ton} decimals={1} suffix=" ton" />
          <Metric i={3} icon={Sun}    accent="#fbbf24" label="Panel üretimi"    value={yatirim.yillik_uretim_kwh} suffix=" kWh" />
        </div>
      )}

      {/* Alt: bina + geçmiş | şifre */}
      <div className="split wide-l" style={{ marginTop: 16, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Section i={0} icon={Home} accent="#60a5fa" title="Kayıtlı binam"
            desc="Ayarların otomatik kaydedilir; her girişte hazır gelir."
            right={<Link to="/simulasyon" className="btn-app ghost" style={{ padding: "8px 14px", fontSize: 13 }}>Düzenle <Arrow size={13} /></Link>}>
            {bina ? (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Chip icon={Home} accent="#60a5fa">{bina.bina_tipi}</Chip>
                <Chip>{bina.kat} kat</Chip>
                <Chip>{bina.aktif_daire} aktif daire</Chip>
                <Chip>{bina.cati_alani} m² çatı</Chip>
              </div>
            ) : (
              <div className="caption">Henüz bina ayarı yok — Bina Simülasyonu'na gidip ayarla, otomatik kaydedilir.</div>
            )}
          </Section>

          <Section i={1} icon={Chart} accent="#fb923c" title="Simülasyon geçmişi">
            {data.gecmis.length === 0 ? (
              <div className="caption">Henüz kayıt yok. Simülasyon çalıştırıp kaydedebilirsin.</div>
            ) : (
              <table className="tbl">
                <thead><tr><th>Tarih</th><th>Bina</th><th>Tasarruf</th><th>Güneş</th></tr></thead>
                <tbody>
                  {data.gecmis.map((g) => (
                    <tr key={g.id}>
                      <td>{new Date(g.tarih).toLocaleDateString("tr-TR")}</td>
                      <td>{g.bina_tipi}</td>
                      <td>{Math.round(g.tasarruf_tl)} TL</td>
                      <td>{Math.round(g.gunes_kwh)} kWh</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>
        </div>

        <Section i={2} icon={Shield} accent="#fbbf24" title="Güvenlik" desc="Şifreni güncelle.">
          <form onSubmit={sifreGonder}>
            <label className="fld">Mevcut şifre</label>
            <input type="password" style={inpStil} value={eski} onChange={(e) => setEski(e.target.value)} required />
            <label className="fld">Yeni şifre</label>
            <input type="password" style={inpStil} value={yeni} onChange={(e) => setYeni(e.target.value)} minLength={4} required />
            {sifreMsj && (
              <div style={{ marginTop: 10, fontSize: 13.5, color: sifreMsj.ok ? "#34d399" : "#fca5a5" }}>{sifreMsj.t}</div>
            )}
            <button type="submit" className="btn-app" style={{ marginTop: 16, width: "100%", padding: "12px 0", fontSize: 14.5 }}>
              Şifreyi güncelle
            </button>
          </form>
        </Section>
      </div>
    </PageWrap>
  );
}
