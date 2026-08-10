import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../state.jsx";
import { DILLER, useI18n } from "../i18n.jsx";

/* Özel logo markası — camsı yeşil rozet + dolu şimşek (derinlikli, jenerik değil) */
export function LogoMark({ size = 34 }) {
  return (
    <svg className="logo-svg" width={size} height={size} viewBox="0 0 34 34" aria-hidden="true">
      <defs>
        <linearGradient id="lmBadge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4ade80" />
          <stop offset="0.55" stopColor="#22c55e" />
          <stop offset="1" stopColor="#059669" />
        </linearGradient>
        <linearGradient id="lmHi" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.38" />
          <stop offset="0.5" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="lmBolt" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#d1fae5" />
        </linearGradient>
      </defs>
      {/* rozet */}
      <rect x="0" y="0" width="34" height="34" rx="10" fill="url(#lmBadge)" />
      {/* üst parlama (cam efekti) */}
      <rect x="0" y="0" width="34" height="34" rx="10" fill="url(#lmHi)" />
      {/* iç kenarlık */}
      <rect x="0.7" y="0.7" width="32.6" height="32.6" rx="9.3" fill="none" stroke="#ffffff" strokeOpacity="0.28" strokeWidth="1" />
      {/* çatı çizgisi — akıllı ev ipucu */}
      <path d="M9 15 L17 9 L25 15" fill="none" stroke="#ffffff" strokeOpacity="0.55" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      {/* dolu şimşek — enerji */}
      <path d="M18.4 12 L12.6 20 H16 L15.2 26 L22 17.4 H18.2 L18.4 12 Z"
        fill="url(#lmBolt)" stroke="#065f46" strokeOpacity="0.15" strokeWidth="0.5" strokeLinejoin="round" />
    </svg>
  );
}

const APP_NAV = [
  ["/simulasyon", "nav.sim"],
  ["/epias", "nav.epias"],
  ["/yatirim", "nav.invest"],
  ["/uzman", "nav.expert"],
];

const MKT_NAV = [
  ["/#features", "nav.howitworks"],
  ["/#stats", "nav.results"],
  ["/#use-cases", "nav.whofor"],
  ["/#faq", "nav.faq"],
];

/* Dil seçici — kompakt açılır menü */
function DilSecici() {
  const { dil, setDil } = useI18n();
  const [ac, setAc] = useState(false);
  const secili = DILLER.find((d) => d.kod === dil) || DILLER[0];
  return (
    <div style={{ position: "relative" }}>
      <button onClick={() => setAc(!ac)} aria-label="Dil"
        style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--surface, rgba(255,255,255,0.06))",
                 border: "1px solid var(--border, rgba(255,255,255,0.12))", color: "var(--fg,#fff)",
                 borderRadius: 999, padding: "7px 12px", fontSize: 13.5, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", minHeight: 44 }}>
        <span>{secili.bayrak}</span>
        <span style={{ textTransform: "uppercase" }}>{secili.kod}</span>
      </button>
      {ac && (
        <>
          <div onClick={() => setAc(false)} style={{ position: "fixed", inset: 0, zIndex: 60 }} />
          <div style={{ position: "absolute", top: "115%", right: 0, zIndex: 61,
                        background: "var(--surface-solid,#111)", border: "1px solid var(--border,rgba(255,255,255,0.14))",
                        borderRadius: 12, padding: 6, minWidth: 150, boxShadow: "0 12px 30px -10px #000a" }}>
            {DILLER.map((d) => (
              <button key={d.kod} onClick={() => { setDil(d.kod); setAc(false); }}
                style={{ display: "flex", alignItems: "center", gap: 9, width: "100%", textAlign: "left",
                         background: d.kod === dil ? "var(--hover,rgba(255,255,255,0.08))" : "none",
                         border: "none", color: "var(--fg,#fff)", borderRadius: 8, padding: "9px 11px",
                         fontSize: 14, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
                <span>{d.bayrak}</span> {d.ad}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* Tek üst bar — sitenin her sayfasında aynı (Framer tarzı camsı hap + mobil çekmece). */
export default function TopNav() {
  const { user, logout } = useApp();
  const { t } = useI18n();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);

  const cikis = () => { setOpen(false); logout(); nav("/"); };
  const links = user ? APP_NAV : MKT_NAV;

  // Logoya tıklayınca: ana sayfaya git + en yukarı yumuşak kaydır
  const anaSayfa = (e) => {
    e.preventDefault();
    setOpen(false);
    nav("/");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="landing">
      <div className="nav">
        <div style={{ padding: "0 14px" }}>
          <motion.div className="nav-pill" initial={{ y: -70, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <Link to="/" className="logo" onClick={anaSayfa}>
              <span className="logo-mark"><LogoMark size={34} /></span> SmartHome Energy
            </Link>

            {/* Masaüstü linkleri */}
            {user ? (
              <nav className="nav-links" aria-label="Uygulama menüsü">
                {APP_NAV.map(([to, key]) => (
                  <NavLink key={to} to={to}
                    className={({ isActive }) => (isActive ? "active" : "")}
                    style={({ isActive }) => isActive ? { color: "#fff", background: "rgba(255,255,255,0.08)" } : undefined}>
                    {t(key)}
                  </NavLink>
                ))}
              </nav>
            ) : (
              <nav className="nav-links" aria-label="Ana menü">
                {MKT_NAV.map(([to, key]) => <a key={key} href={to}>{t(key)}</a>)}
              </nav>
            )}

            {/* Masaüstü sağ blok */}
            <div className="nav-cta-desktop" style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <DilSecici />
              {user ? (
                <>
                  <Link to="/profil" style={{ display: "flex", alignItems: "center", gap: 8, whiteSpace: "nowrap", fontSize: 13.5, fontWeight: 600, color: "#fff" }}>
                    <span style={{
                      width: 30, height: 30, borderRadius: "50%",
                      background: "linear-gradient(135deg,#34d399,#10b981)", color: "#04120c",
                      display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800,
                    }}>{(user.ad || "K").charAt(0).toUpperCase()}</span>
                    {user.ad}
                  </Link>
                  <button onClick={cikis} className="btn btn-ghost" style={{ padding: "9px 16px", fontSize: 13.5 }}>
                    {t("nav.logout")}
                  </button>
                </>
              ) : (
                <Link className="btn btn-primary" to="/kayit" style={{ padding: "11px 20px" }}>
                  {t("nav.signup")}
                </Link>
              )}
            </div>

            {/* Mobil hamburger */}
            <button className={"nav-burger" + (open ? " open" : "")} onClick={() => setOpen(!open)}
              aria-label="Menü" aria-expanded={open}>
              <span />
            </button>
          </motion.div>

          {/* Mobil çekmece */}
          <AnimatePresence>
            {open && (
              <motion.div className="nav-drawer"
                initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.28, ease: "easeOut" }}>
                <div className="inner">
                  {links.map(([to, key]) => (
                    user
                      ? <Link key={to} to={to} onClick={() => setOpen(false)}>{t(key)}</Link>
                      : <a key={key} href={to} onClick={() => setOpen(false)}>{t(key)}</a>
                  ))}
                  <div style={{ height: 1, background: "var(--line)", margin: "6px 4px" }} />
                  <div style={{ padding: "4px 4px 2px" }}><DilSecici /></div>
                  {user ? (
                    <>
                      <Link to="/profil" onClick={() => setOpen(false)}>{t("nav.profile")} · {user.ad}</Link>
                      <button className="drawer-link" onClick={cikis}>{t("nav.logout")}</button>
                    </>
                  ) : (
                    <Link className="btn btn-primary drawer-cta" to="/kayit" onClick={() => setOpen(false)}
                      style={{ justifyContent: "center" }}>
                      {t("nav.signup")}
                    </Link>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
