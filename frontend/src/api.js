// Production'da VITE_API_URL env var'ı backend Render URL'sini gösterir.
// Development'ta boş bırakılır — vite proxy /api → localhost:8000 yönlendirir.
const BASE = import.meta.env.VITE_API_URL || "";

const TOKEN_KEY = "she_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY) || "";
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

const authHeaders = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};

const json = async (r) => {
  if (!r.ok) {
    let msg = `API ${r.status}`;
    try { const b = await r.json(); if (b.detail) msg = b.detail; } catch { /* yoksa geç */ }
    throw new Error(msg);
  }
  return r.json();
};

const post = (url, body, auth = false) =>
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(auth ? authHeaders() : {}) },
    body: JSON.stringify(body),
  }).then(json);

const put = (url, body) =>
  fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  }).then(json);

const get = (url) => fetch(BASE + url, { headers: authHeaders() }).then(json);

export const api = {
  simulate: (body) => post(BASE + "/api/simulate", body),
  yatirim: (body) => post(BASE + "/api/yatirim", body),
  buildingHtml: (body) =>
    fetch(BASE + "/api/building-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => r.text()),
  binaTipleri: () => get("/api/bina-tipleri"),
  karsilastirma: () => get("/api/uzman/karsilastirma"),
  mevsimsel: () => get("/api/uzman/mevsimsel"),

  // ── Kimlik doğrulama + profil ──
  register: (ad, email, sifre) => post(BASE + "/api/register", { ad, email, sifre }),
  login: (email, sifre) => post(BASE + "/api/login", { email, sifre }),
  profile: () => get("/api/profile"),
  binaKaydet: (bina) => put(BASE + "/api/profile/bina", bina),
  gecmisEkle: (kayit) => post(BASE + "/api/profile/gecmis", kayit, true),
  sifreDegistir: (eski, yeni) => put(BASE + "/api/profile/sifre", { eski, yeni }),
};
