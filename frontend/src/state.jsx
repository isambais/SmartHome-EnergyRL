import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken } from "./api.js";

export const BINA_TIPLERI = {
  "Müstakil Ev": { kat: 1, daire_per_kat: 1, aktif_daire: 1, oda: 4, cati_alani: 60, asansor: false, hvac: true, su_pompasi: false, ev_sarj: true, kamera: true, gunes_isitici: true, jenerator: false },
  Villa: { kat: 2, daire_per_kat: 1, aktif_daire: 1, oda: 5, cati_alani: 100, asansor: false, hvac: true, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: true, jenerator: true },
  Apartman: { kat: 5, daire_per_kat: 3, aktif_daire: 12, oda: 3, cati_alani: 140, asansor: true, hvac: false, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: false, jenerator: true },
  "Ofis Binası": { kat: 6, daire_per_kat: 2, aktif_daire: 10, oda: 6, cati_alani: 200, asansor: true, hvac: true, su_pompasi: true, ev_sarj: true, kamera: true, gunes_isitici: false, jenerator: true },
};

const defaultCfg = { bina_tipi: "Apartman", ...BINA_TIPLERI["Apartman"] };

const Ctx = createContext(null);

const SESSION_KEY = "she_session";

export function AppState({ children }) {
  const [cfg, setCfg] = useState(defaultCfg);
  const [saat, setSaat] = useState(new Date().getHours());
  const [ay, setAy] = useState(new Date().getMonth() + 1);   // 1–12, seçili ay
  const [uzman, setUzman] = useState(false);
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(SESSION_KEY)); } catch { return null; }
  });

  // Tema: "light" | "dark" | null(=sistem tercihi). App/dashboard ekranlarını etkiler.
  const [tema, setTemaState] = useState(() => localStorage.getItem("she_tema"));
  useEffect(() => {
    const el = document.documentElement;
    if (tema) el.setAttribute("data-theme", tema);
    else el.removeAttribute("data-theme");
  }, [tema]);
  const setTema = (t) => {
    setTemaState(t);
    if (t) localStorage.setItem("she_tema", t);
    else localStorage.removeItem("she_tema");
  };
  const toggleTema = () => {
    const sistemKoyu = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    const suAn = tema || (sistemKoyu ? "dark" : "light");
    setTema(suAn === "dark" ? "light" : "dark");
  };

  const _kaydet = (u) => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(u));
    setUser(u);
    // Girişte hesaba kayıtlı bina varsa yükle
    if (u?.bina) setCfg({ ...defaultCfg, ...u.bina });
  };

  // Gerçek backend auth — hata mesajını (string) döndürür, başarıda null
  const register = async (ad, email, sifre) => {
    try {
      const r = await api.register(ad, email, sifre);
      setToken(r.token);
      _kaydet(r.user);
      return null;
    } catch (e) { return e.message; }
  };

  const login = async (email, sifre) => {
    try {
      const r = await api.login(email, sifre);
      setToken(r.token);
      _kaydet(r.user);
      return null;
    } catch (e) { return e.message; }
  };

  const logout = () => {
    setToken("");
    localStorage.removeItem(SESSION_KEY);
    setUser(null);
    // Çıkışta her şey sıfırlanır
    setCfg(defaultCfg);
    setAy(new Date().getMonth() + 1);
    setUzman(false);
  };

  // Oturum açıksa: bina ayarları değiştikçe otomatik hesaba kaydet (debounce)
  useEffect(() => {
    if (!user) return;
    const t = setTimeout(() => {
      api.binaKaydet(cfg).catch(() => {});
    }, 800);
    return () => clearTimeout(t);
  }, [JSON.stringify(cfg), user?.email]);

  // Sayfa yenilenince oturum varsa kayıtlı binayı geri yükle
  useEffect(() => {
    if (!user) return;
    api.profile()
      .then((p) => { if (p?.user?.bina) setCfg({ ...defaultCfg, ...p.user.bina }); })
      .catch(() => {});
    // yalnızca ilk yüklemede
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Ctx.Provider value={{ cfg, setCfg, saat, setSaat, ay, setAy, uzman, setUzman,
                           user, setUser, register, login, logout,
                           tema, setTema, toggleTema }}>
      {children}
    </Ctx.Provider>
  );
}

export const useApp = () => useContext(Ctx);
