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

export const api = {
  simulate: (body) => post("/api/simulate", body),
  yatirim: (body) => post("/api/yatirim", body),
  buildingHtml: (body) =>
    fetch("/api/building-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => r.text()),
  binaTipleri: () => fetch("/api/bina-tipleri").then(json),
  karsilastirma: () => fetch("/api/uzman/karsilastirma").then(json),
  mevsimsel: () => fetch("/api/uzman/mevsimsel").then(json),

  // ── Kimlik doğrulama + profil ──
  register: (ad, email, sifre) => post("/api/register", { ad, email, sifre }),
  login: (email, sifre) => post("/api/login", { email, sifre }),
  profile: () => fetch("/api/profile", { headers: authHeaders() }).then(json),
  binaKaydet: (bina) => put("/api/profile/bina", bina),
  gecmisEkle: (kayit) => post("/api/profile/gecmis", kayit, true),
  sifreDegistir: (eski, yeni) => put("/api/profile/sifre", { eski, yeni }),
};
