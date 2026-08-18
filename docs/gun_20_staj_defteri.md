# Staj Defteri — Gün 20

**Tarih:** 11 Ağustos 2026
**Stajyer:** Alesam Baath
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 20 — Sistem Denetimi, Kod Kalitesi & Deploy

### 1. Bugün Ne Yapıldı?

Son gün olarak projenin tümünde sistematik bir denetim yapıldı. Kod kalitesi
taraması, güvenlik kontrolü, merge çakışmalarının çözümü, README'nin yeniden
yazılması ve uygulamanın Render platformuna deploy için hazırlanması
gerçekleştirildi.

---

### 2. Merge Çakışması Çözümü

`feat/gun20-lighthouse-performance` branch'i daha önce `feat/i18n-en-ar`'ı
merge etmişti; ancak `git add .` + `git commit` çakışma işaretleri
(`<<<<<<< HEAD`, `=======`, `>>>>>>> feat/i18n-en-ar`) çözülmeden yapılmıştı.
Bu çakışma kalıntıları bugün tek tek tespit edilip giderildi.

**Etkilenen dosyalar ve alınan karar:**

| Dosya | Çakışma | Tercih edilen |
|---|---|---|
| `frontend/src/App.jsx` | lazy import vs. doğrudan import | HEAD (lazy loading — Lighthouse) |
| `frontend/src/index.css` | touch target ve kontrast | HEAD (Lighthouse düzeltmeleri) |
| `frontend/src/i18n.jsx` | 1 saatlik TTL cache vs. cache yok | HEAD (1 saatlik cache) |
| `frontend/src/pages/Landing.jsx` | canlı renkler vs. koyu renkler | HEAD (mevcut tasarımla uyumlu) |

`feat/i18n-en-ar`'dan kalan bir rebase de `git rebase --abort` ile temizlendi.

---

### 3. Kod Kalitesi Taraması (Adım 10)

Projenin tüm kaynak dosyaları aşağıdaki kategorilerde tarandı:

**Sonuçlar:**

| Kontrol | Bulgu |
|---|---|
| `<<<<<<< HEAD` çakışma işareti | App.jsx'te kalıntı bulundu → giderildi |
| `console.log()` (frontend) | Yok |
| `TODO` / `FIXME` | Yok |
| Kullanılmayan import | `backend/main.py`'de `import numpy as np` → silindi (önceki gün) |
| Hardcoded credentials | Kaynak dosyalarda yok (test dosyaları önceki gün temizlendi) |
| Duplicate bileşen | `EASE`, `AY_RENK`, `CardHead`, `ErrorPage` 5 sayfada tekrar ediyordu → `ui.jsx`'e taşındı |
| `locale` tekrarı | `useI18n()` hook'undan `locale` export edildi — 5 sayfada ayrı `_locale()` çağrısı kaldırıldı |
| Gereksiz dosya | `replacements.txt` (git filter-repo artığı, eski credentials içeriyordu) → silindi |

**Refaktör özeti:** `ui.jsx` paylaşılan bileşen deposuna dönüştürüldü.
`EASE` sabiti (Framer Motion easing), `AY_RENK` (ay renk fonksiyonu),
`CardHead` (kart başlık bileşeni) ve `ErrorPage` (hata sayfası) tek yerden
export ediliyor. Bu sayede Epias, Simulasyon, Yatirim, Uzman, Profil ve
Auth sayfalarındaki kod tekrarı ortadan kalktı.

---

### 4. GitHub Güvenlik Denetimi (Adım 11)

**`.gitignore` güncellemeleri:**

```
.env.local          # Vite yerel ortam değişkenleri
.env.*.local        # Ortam bazlı yerel dosyalar
.env.test           # Test ortamı değişkenleri
replacements.txt    # git filter-repo artığı — hassas veri içerebilir
```

Ayrıca `.gitignore`'da tekrar eden `.env` satırı temizlendi.

**`.env.example` güncellemeleri:**
`FRONTEND_URL` değişkeni eklendi — backend CORS yapılandırması için.

**Kimlik bilgisi taraması:** `isambais18@gmail.com` ve şifre kalıntısı
yalnızca `replacements.txt`'te bulundu (git filter-repo konfigürasyon dosyası).
Bu dosya hem repadan silindi hem de `.gitignore`'a eklendi.

**README:** Projenin gerçek durumunu yansıtmıyordu. Tamamen yeniden yazıldı:
üç katman mimarisi (React → FastAPI → RL çekirdeği), Phase 3 sonuç tabloları,
güncel proje yapısı, backend + frontend ayrı kurulum adımları.

---

### 5. Deploy Hazırlığı (Render)

Projenin Render platformuna deploy edilebilmesi için gerekli değişiklikler
yapıldı:

**`render.yaml`** (yeni dosya) — Blueprint olarak iki servis tanımlandı:
- `smarthome-api`: Python web servisi, `uvicorn backend.main:app`
- `smarthome-frontend`: Static site, `npm run build` → `dist/`

**`frontend/src/api.js`** — `VITE_API_URL` environment variable desteği eklendi:

```javascript
const BASE = import.meta.env.VITE_API_URL || "";
```

Development'ta boş bırakılır (Vite proxy devreye girer); production'da
Render backend URL'si set edilir.

**`backend/main.py`** — CORS `FRONTEND_URL` env var'ından dinamik olarak
okunuyor:

```python
_FRONTEND_URL = os.environ.get("FRONTEND_URL", "")
_CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000",
                  *([_FRONTEND_URL] if _FRONTEND_URL else [])]
```

Bu yapı sayesinde backend kodu değiştirilmeden herhangi bir frontend
URL'sine izin verilebiliyor.

---

### 6. Oluşturulan/Değişen Dosyalar (Gün 20)

```
frontend/src/App.jsx              — merge conflict temizlendi (lazy import)
frontend/src/index.css            — merge conflict temizlendi (touch targets)
frontend/src/i18n.jsx             — merge conflict temizlendi (TTL cache)
frontend/src/pages/Landing.jsx    — merge conflict temizlendi (renkler)
frontend/src/api.js               — VITE_API_URL desteği eklendi
frontend/src/components/ui.jsx    — EASE, AY_RENK, CardHead, ErrorPage eklendi
backend/main.py                   — CORS FRONTEND_URL dinamik, import numpy silindi
.gitignore                        — .env.local varyantları, replacements.txt eklendi
.env.example                      — FRONTEND_URL eklendi
render.yaml                       — yeni: Render Blueprint yapılandırması
README.md                         — tamamen yeniden yazıldı
replacements.txt                  — silindi (hassas veri)
docs/gun_20_staj_defteri.md       — bu defter
```

---

### 7. Teknik Öğrenimler

**Merge çakışmaları commit edilmeden önce mutlaka doğrulanmalı.**
`git add .` çalıştırmadan önce `git diff --check` veya basit bir `grep -r "<<<<<"`
kontrolü, çakışma işaretlerini erken yakalar. Aksi hâlde her dosya ayrı ayrı
onarılmak zorunda kalınıyor — bu günkü durumda dört dosyada yapıldı.

**Environment-aware API istemcisi.** `VITE_API_URL || ""` deseni çok temiz:
development'ta proxy çalışır, production'da env var set edilir, kod hiç
değişmez. Çoğu React projesinde bu örüntü standart; geç keşfedilen sıradan ama
kurtarıcı bir konvansiyon.

**CORS'u environment variable'dan yönet.** Hardcoded origin listesi yerine
`FRONTEND_URL` env var'ı hem daha güvenli (kaynak kodda URL yok) hem de
daha esnek (farklı ortamlar için farklı değer).

**`.gitignore` bakımı son güne kalmamalı.** `replacements.txt` gibi bir dosya
işlem bittikten hemen sonra `.gitignore`'a eklenmeli ya da silinmeli. Hassas
veri içeren araç çıktıları repoda beklemiyor.

---

### 8. Git Commits (Gün 20)

```
PR #42: feat/gun20-lighthouse-performance → feat/i18n-en-ar

[0ea4d03]  fix: resolve merge conflict markers in i18n.jsx, Landing.jsx, index.css
[9148e19]  docs: README güncellendi — web app mimarisi, Phase 3 sonuçları, tam proje yapısı
[9fee74d]  chore: replacements.txt gitignore'a eklendi (hassas veri), App.jsx conflict fix
[...]      feat(deploy): Render deploy yapılandırması — render.yaml, VITE_API_URL, CORS FRONTEND_URL
[...]      docs: Gün 20 staj defteri
```

---

### 9. Staj Sonu — 20 Günlük Özet

20 iş günü boyunca RL araştırma prototipi olarak başlayan proje tam yığın bir
web uygulamasına dönüştü. Önemli kilometre taşları:

| Gün | Başlık |
|---|---|
| 1–3 | Proje kurulumu, EPİAŞ veri entegrasyonu |
| 4–6 | Gymnasium ortamı (SmartHomeEnergyEnv), reward tasarımı |
| 7–8 | PPO/A2C/SAC/TD3 Phase 1 eğitimi |
| 9–11 | Phase 2 — güneş + talep, kural tabanlı baseline, Optuna HPO |
| 12 | Phase 3 — hybrid aksiyon uzayı, ertelenebilir yük |
| 13–15 | Fiyat tahmini (LightGBM), robustluk analizi, forecast comparison |
| 16–17 | Streamlit BMS dashboard — 4 sayfa, Three.js 3D bina |
| 18 | FastAPI backend + React frontend ilk sürüm |
| 19 | TR/EN/AR i18n, RTL desteği, deney kayıt defteri |
| 20 | Sistem denetimi, kod kalitesi, güvenlik, deploy |

**Nihai teknik yığın:** Gymnasium · Stable-Baselines3 · Optuna · FastAPI ·
React 18 · Vite · Framer Motion · SQLite · Streamlit · Three.js ·
LightGBM · pytest · Render

**En güçlü bulgu:** TD3 ve SAC ajanları 74 günlük test setinde Oracle/Forecast/
Ensemble/Naive modları arasında yalnızca ±0.2 TL sapmayla tahmin
belirsizliğine karşı **robust** davranıyor. Kural tabanlı FcAware politikası
aynı koşulda 9 TL oynuyor — RL'nin temel avantajı bu.
