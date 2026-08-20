import { Link } from "react-router-dom";
import { ArrowUp, Bolt, Github, Mail } from "../icons.jsx";
import { useI18n } from "../i18n.jsx";

const REPO = "https://github.com/isambais/SmartHome-EnergyRL";

const isDis = (h) => h.startsWith("http");

export default function Footer() {
  const { t } = useI18n();
  const yukari = () => window.scrollTo({ top: 0, behavior: "smooth" });
  const COLS = [
    [t("foot.dashboard"), [
      [t("nav.sim"), "/simulasyon"], [t("nav.epias"), "/epias"],
      [t("nav.invest"), "/yatirim"], [t("nav.expert"), "/uzman"],
    ]],
    [t("foot.project"), [
      [t("foot.features"), "/#features"], [t("nav.howitworks"), "/#features"],
      [t("nav.results"), "/#stats"], [t("nav.faq"), "/#faq"],
    ]],
    [t("foot.links"), [
      ["GitHub", REPO], ["Issues", REPO + "/issues"], ["Pull Requests", REPO + "/pulls"],
    ]],
  ];
  return (
    <div className="landing">
      <footer className="site-footer">
        <div className="container">
          {/* Üst: marka + linkler */}
          <div className="foot-grid" style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr 1fr 1fr", gap: 40 }}>
            <div>
              <div className="logo" style={{ marginBottom: 14 }}>
                <span className="logo-mark"><Bolt size={17} /></span> SmartHome Energy
              </div>
              <p className="sub" style={{ fontSize: 14, maxWidth: 280, lineHeight: 1.65 }}>
                {t("foot.tagline")}
              </p>
              <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
                <a className="foot-social" href={REPO} target="_blank" rel="noreferrer" aria-label="GitHub"><Github size={17} /></a>
                <a className="foot-social" href="mailto:test@example.com" aria-label="E-posta"><Mail size={17} /></a>
              </div>
              <div style={{ display: "inline-flex", alignItems: "center", gap: 8, marginTop: 18, fontSize: 12.5, color: "var(--muted)" }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px #34d399" }} />
                {t("foot.online")}
              </div>
            </div>

            {COLS.map(([title, links]) => (
              <div key={title}>
                <h3>{title}</h3>
                {links.map(([ad, href]) => (
                  isDis(href)
                    ? <a key={ad + href} href={href} target="_blank" rel="noreferrer">{ad}</a>
                    : <Link key={ad + href} to={href}>{ad}</Link>
                ))}
              </div>
            ))}
          </div>

          {/* Alt bar */}
          <div className="foot-bottom">
            <span>© {new Date().getFullYear()} SmartHome-EnergyRL · {t("foot.rights")}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <span className="foot-tech">Gaziantep Teknopark</span>
              <span className="foot-dot" />
              <span className="foot-tech">SAC + EPİAŞ + Three.js</span>
              <button className="foot-top" onClick={yukari} aria-label={t("foot.top")}>
                {t("foot.top")} <ArrowUp size={14} />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
