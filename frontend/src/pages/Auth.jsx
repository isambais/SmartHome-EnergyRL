import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../state.jsx";
import { Arrow, Bolt, Brain, Check, Cube, Gauge, Lock, Mail, User } from "../icons.jsx";
import { LogoMark } from "../components/TopNav.jsx";
import { useI18n } from "../i18n.jsx";

const EASE = [0.22, 1, 0.36, 1];

/* Dile göre küçük metinler (i18n anahtarı olmayan mikro kopya) */
const PILL  = { tr: "Ücretsiz · kart gerekmez", en: "Free · no card needed", ar: "مجانًا · بدون بطاقة" };
const PUNCH = { tr: "kendiliğinden.", en: "on autopilot.", ar: "تلقائيًا." };
const TRUST = { tr: "Açık kaynak · gerçek piyasa verisi", en: "Open source · real market data", ar: "مفتوح المصدر · بيانات سوق حقيقية" };
const SHOW  = { tr: ["Göster", "Gizle"], en: ["Show", "Hide"], ar: ["إظهار", "إخفاء"] };
const STR   = {
  tr: ["Çok zayıf", "Zayıf", "Orta", "İyi", "Güçlü"],
  en: ["Very weak", "Weak", "Fair", "Good", "Strong"],
  ar: ["ضعيفة جدًا", "ضعيفة", "متوسطة", "جيدة", "قوية"],
};

/* Basit ama gerçek şifre gücü (0–4) */
function pwScore(pw) {
  let s = 0;
  if (pw.length >= 6) s++;
  if (pw.length >= 10) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(s, 4);
}

/* Kayıt + Giriş — aurora glassmorphism */
export default function Auth({ mode = "kayit" }) {
  const kayit = mode === "kayit";
  const { register, login } = useApp();
  const { t, dil } = useI18n();
  const lang = dil === "ar" ? "ar" : dil === "en" ? "en" : "tr";
  const nav = useNavigate();
  const [ad, setAd] = useState("");
  const [email, setEmail] = useState("");
  const [sifre, setSifre] = useState("");
  const [goster, setGoster] = useState(false);
  const [hata, setHata] = useState(null);
  const [bekliyor, setBekliyor] = useState(false);
  const score = pwScore(sifre);

  const submit = async (e) => {
    e.preventDefault();
    setBekliyor(true);
    setHata(null);
    const err = kayit ? await register(ad.trim() || "Kullanıcı", email.trim(), sifre)
                      : await login(email.trim(), sifre);
    setBekliyor(false);
    if (err) setHata(err);
    else nav("/");
  };

  const trust = [[Bolt, "EPİAŞ"], [Brain, "PPO"], [Cube, "React"], [Gauge, "FastAPI"]];

  return (
    <div className="au-root">
      <div className="au-aurora" />
      <div className="au-grain" />

      {/* ── Ortada marka — ana sayfaya dönüş (kutusuz) ────── */}
      <Link to="/" className="au-topbrand">
        <LogoMark size={36} />
        <span className="au-grad-text">SmartHome Energy</span>
      </Link>

      {/* ── Hero: pitch + kart ────────────────────────────── */}
      <main className="au-shell">
        <div className="au-grid">
          {/* Sol — pazarlama */}
          <motion.div className="au-pitch"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE }}>
            <span className="au-chip"><span className="au-dot" />{PILL[lang]}</span>
            <h1 className="au-head">
              {t("lp.hero.titleFull")}<br />
              <span className="au-grad-text">{PUNCH[lang]}</span>
            </h1>
            <p className="au-lead">{t("lp.hero.sub")}</p>
            <div className="au-points">
              {["lp.hero.chip1", "lp.hero.chip2", "lp.hero.chip3"].map((k, i) => (
                <motion.div className="au-point" key={k}
                  initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.25 + i * 0.08, duration: 0.45, ease: EASE }}>
                  <span className="ic"><Check size={18} /></span>{t(k)}
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Sağ — buzlu cam kart */}
          <motion.div className="au-card au-glass au-sheen au-cardglow"
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: EASE, delay: 0.05 }}>
            <div className="au-card-h">{kayit ? t("auth.register.title") : t("auth.login.title")}</div>
            <div className="au-card-sub">{kayit ? t("auth.register.sub") : t("auth.login.sub")}</div>

            <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {kayit && (
                <div className="au-field-wrap">
                  <span className="au-field-icon"><User size={18} /></span>
                  <input className="au-field" value={ad} onChange={(e) => setAd(e.target.value)} placeholder={t("auth.name.ph")} />
                </div>
              )}
              <div className="au-field-wrap">
                <span className="au-field-icon"><Mail size={18} /></span>
                <input className="au-field" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ornek@eposta.com" />
              </div>
              <div className="au-field-wrap">
                <span className="au-field-icon"><Lock size={18} /></span>
                <input className="au-field" type={goster ? "text" : "password"} required minLength={4}
                  value={sifre} onChange={(e) => setSifre(e.target.value)} placeholder={t("auth.password")} />
                <button type="button" className="au-toggle" onClick={() => setGoster((v) => !v)}>
                  {SHOW[lang][goster ? 1 : 0]}
                </button>
              </div>

              {kayit && sifre && (
                <div className="au-meter">
                  {[0, 1, 2, 3].map((i) => <span key={i} className={"bar" + (i < score ? " on" : "")} />)}
                  <span className="lbl">{STR[lang][score]}</span>
                </div>
              )}

              {hata && <div className="au-err">{hata}</div>}

              <motion.button whileTap={{ scale: 0.985 }} type="submit" disabled={bekliyor} className="au-btn">
                {bekliyor ? t("auth.wait") : (kayit ? t("auth.register.btn") : t("auth.login.btn"))}
                {!bekliyor && <Arrow size={16} />}
              </motion.button>
            </form>

            <div className="au-foot">
              {kayit
                ? <>{t("auth.haveAccount")} <Link to="/giris" className="au-grad-text" style={{ fontWeight: 700 }}>{t("auth.goLogin")}</Link></>
                : <>{t("auth.noAccount")} <Link to="/kayit" className="au-grad-text" style={{ fontWeight: 700 }}>{t("auth.goRegister")}</Link></>}
            </div>
          </motion.div>
        </div>
      </main>

      {/* ── Trust strip (gerçek teknoloji rozetleri) ──────── */}
      <section className="au-trust">
        <div className="au-trust-inner">
          <div className="au-trust-label">{TRUST[lang]}</div>
          <div className="au-trust-row">
            {trust.map(([Ic, name]) => (
              <div className="au-trust-item" key={name}><Ic size={18} /> {name}</div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
