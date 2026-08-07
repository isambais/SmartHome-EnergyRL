import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../state.jsx";
import { Bolt } from "../icons.jsx";
import { useT } from "../i18n.jsx";

/* Kayıt + Giriş — landing ile aynı açık tasarım dili */
export default function Auth({ mode = "kayit" }) {
  const kayit = mode === "kayit";
  const { register, login } = useApp();
  const t = useT();
  const nav = useNavigate();
  const [ad, setAd] = useState("");
  const [email, setEmail] = useState("");
  const [sifre, setSifre] = useState("");
  const [hata, setHata] = useState(null);
  const [bekliyor, setBekliyor] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBekliyor(true);
    setHata(null);
    const err = kayit ? await register(ad.trim() || "Kullanıcı", email.trim(), sifre)
                      : await login(email.trim(), sifre);
    setBekliyor(false);
    if (err) setHata(err);
    else nav("/");   // kayıt/giriş sonrası ana sayfaya (landing) dön
  };

  const inp = {
    width: "100%", background: "var(--bg3)", border: "1px solid var(--border)",
    color: "var(--fg)", borderRadius: 10, padding: "12px 14px", fontSize: 15,
    fontFamily: "inherit",
  };

  return (
    <div style={{
      minHeight: "100vh", background: "var(--bg)", position: "relative", overflow: "hidden",
      display: "flex", alignItems: "center", justifyContent: "center", padding: 20,
    }}>
      {/* arka plan ışıması */}
      <div style={{ position: "absolute", top: "-10%", left: "50%", transform: "translateX(-50%)",
        width: "70vw", height: "60vh", background: "radial-gradient(circle, rgba(52,211,153,0.12), transparent 65%)",
        filter: "blur(40px)", pointerEvents: "none" }} />
      <motion.div
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        style={{
          background: "var(--surface-solid)", border: "1px solid var(--border)", borderRadius: 24,
          boxShadow: "0 30px 80px -30px #000000cc", padding: "38px 34px",
          width: "100%", maxWidth: 420, position: "relative", backdropFilter: "blur(8px)",
        }}>
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 18, color: "#fff", marginBottom: 22 }}>
          <span style={{ width: 32, height: 32, borderRadius: 10, background: "linear-gradient(135deg,#34d399,#10b981)", color: "#04120c", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 18px -2px #34d39988" }}><Bolt size={17} /></span>
          SmartHome Energy
        </Link>

        <h1 style={{ fontSize: 26, margin: "0 0 6px", letterSpacing: "-0.02em" }}>
          {kayit ? t("auth.register.title") : t("auth.login.title")}
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 14.5, marginBottom: 24 }}>
          {kayit ? t("auth.register.sub") : t("auth.login.sub")}
        </p>

        <form onSubmit={submit}>
          {kayit && (
            <>
              <label className="fld">{t("auth.name")}</label>
              <input style={inp} value={ad} onChange={(e) => setAd(e.target.value)} placeholder={t("auth.name.ph")} />
            </>
          )}
          <label className="fld">{t("auth.email")}</label>
          <input style={inp} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ornek@eposta.com" />
          <label className="fld">{t("auth.password")}</label>
          <input style={inp} type="password" required minLength={4} value={sifre} onChange={(e) => setSifre(e.target.value)} placeholder="••••••••" />

          {hata && (
            <div style={{ background: "rgba(248,113,113,0.12)", border: "1px solid rgba(248,113,113,0.35)", color: "#fca5a5", borderRadius: 10, padding: "9px 13px", fontSize: 13.5, marginTop: 12 }}>
              {hata}
            </div>
          )}

          <motion.button whileHover={{ scale: bekliyor ? 1 : 1.015 }} whileTap={{ scale: 0.985 }} type="submit"
            disabled={bekliyor} className="btn-app"
            style={{
              width: "100%", marginTop: 18, padding: "13px 0", fontSize: 15.5,
              cursor: bekliyor ? "default" : "pointer", opacity: bekliyor ? 0.7 : 1,
            }}>
            {bekliyor ? t("auth.wait") : (kayit ? t("auth.register.btn") : t("auth.login.btn"))}
          </motion.button>
        </form>

        <div style={{ textAlign: "center", marginTop: 18, fontSize: 14, color: "var(--muted)" }}>
          {kayit ? <>{t("auth.haveAccount")} <Link to="/giris" style={{ fontWeight: 700 }}>{t("auth.goLogin")}</Link></>
                 : <>{t("auth.noAccount")} <Link to="/kayit" style={{ fontWeight: 700 }}>{t("auth.goRegister")}</Link></>}
        </div>
      </motion.div>
    </div>
  );
}
