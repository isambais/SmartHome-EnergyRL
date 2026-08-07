# Staj Defteri — Gün 18

**Tarih:** 7 Ağustos 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 18 — FastAPI Backend & React Frontend

### 1. Bugün Ne Yapıldı?

Projenin ağ katmanı yazıldı. Streamlit prototipinin yerini üretim kalitesinde bir istemci-sunucu mimarisi aldı: FastAPI ile yazılmış bir REST API backend ve React + Vite ile yazılmış 7 sayfalık bir web uygulaması. Backend, daha önceki günlerde geliştirilen simülasyon motorunu (`dashboard/core`) yeniden kullanıyor; bu sayede hiçbir simülasyon mantığı tekrar yazılmadı.

---

### 2. Backend — FastAPI

#### 2.1 Mimari Genel Bakış

```
backend/
├── main.py       FastAPI uygulaması — tüm endpoint'ler
├── auth.py       Kimlik doğrulama (PBKDF2 + JWT-style token)
├── models.py     SQLAlchemy ORM modelleri
├── db.py         Veritabanı bağlantısı ve başlatma
├── data.py       EPİAŞ veri katmanı (backend'e özgü)
└── requirements.txt
```

`dashboard/core` modülleri `sys.path` ile içe aktarılıyor; yani `simulate_day()`, `get_agent()`, `building_html()` ve `BinaConfig` tek bir yerden geliyor.

#### 2.2 Kimlik Doğrulama

Harici JWT kütüphanesi (PyJWT, python-jose vb.) kullanılmadı; tüm token mekanizması Python standart kütüphanesiyle yazıldı.

**Şifre hash'leme:**
```python
def hash_sifre(sifre: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", sifre.encode(), salt, 200_000)
    return salt.hex() + "$" + dk.hex()
```

PBKDF2-HMAC-SHA256 ile 200.000 iterasyon — modern brute-force saldırılarına karşı yeterli maliyet. Tuz her kayıt için rastgele üretildiğinden gökkuşağı tablo saldırıları etkisiz.

**Token:**
```python
# Header.Payload.İmza — Base64URL kodlu, HMAC-SHA256 imzalı
def token_olustur(user_id: int) -> str:
    # 30 günlük geçerlilik, standart JWT yapısı
```

`Authorization: Bearer <token>` header'ından çözümleniyor; `current_user` dependency injection olarak FastAPI endpoint'lerine enjekte ediliyor.

#### 2.3 Veritabanı Modelleri

```python
class User(Base):
    id, ad, email, sifre_hash, created_at
    bina: JSON       # Kullanıcının kayıtlı bina konfigürasyonu
    gecmis: [SimKaydi]

class SimKaydi(Base):
    id, user_id (FK), tarih, bina_tipi
    tasarruf_tl, gunes_kwh, not_
```

`User.bina` sütunu JSON tipinde; kullanıcı bina konfigüratöründe ayar yaptığında `PUT /api/profile/bina` ile tek satıra kaydediliyor. Bir sonraki girişte ayarlar hazır geliyor.

#### 2.4 Veritabanı Esnekliği

```ini
# PostgreSQL (üretim)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/smarthome

# SQLite (geliştirme — docker gerektirmez)
DATABASE_URL=sqlite:///./smarthome.db
```

`db.py` içindeki `init_db()` uygulamayı açılışında tabloları oluşturuyor (migrate adımı yok, basit dev akışı).

#### 2.5 API Endpoint'leri

| Metot | Yol | Açıklama |
|---|---|---|
| POST | `/api/register` | Kayıt — token döner |
| POST | `/api/login` | Giriş — token döner |
| GET | `/api/profile` | Kullanıcı + simülasyon geçmişi |
| PUT | `/api/profile/bina` | Bina konfigürasyonunu kaydet |
| POST | `/api/profile/gecmis` | Simülasyon sonucunu geçmişe ekle |
| PUT | `/api/profile/sifre` | Şifre değiştir |
| POST | `/api/simulate` | SAC ajanıyla 24 saatlik simülasyon |
| POST | `/api/epias` | Canlı EPİAŞ verileriyle simülasyon |
| GET | `/api/yatirim` | Amorti hesabı + aylık tasarruf |
| GET | `/api/uzman` | Algoritma karşılaştırması + mevsimsel analiz |
| GET | `/api/3d` | Three.js bina HTML'i |

CORS middleware ile `http://localhost:5173` (Vite dev server) white-list'te.

---

### 3. Frontend — React + Vite

#### 3.1 Sayfa Yapısı

```
frontend/src/
├── App.jsx           React Router — korumalı + genel rotalar
├── state.jsx         Global durum (user, cfg, token) — Context API
├── api.js            Backend'e HTTP istekleri — merkezi istemci
├── i18n.jsx          Çok dil desteği — TR / EN / AR
├── icons.jsx         SVG ikon bileşenleri
├── pages/
│   ├── Auth.jsx      Kayıt / Giriş formu
│   ├── Landing.jsx   Landing sayfası (tam içerik)
│   ├── Simulasyon.jsx  24 saat SAC simülasyonu
│   ├── Epias.jsx     Canlı EPİAŞ fiyatları
│   ├── Yatirim.jsx   Amorti & çevre etkisi
│   ├── Uzman.jsx     Algoritma karşılaştırması
│   └── Profil.jsx    Hesap & geçmiş yönetimi
└── components/
    ├── TopNav.jsx    Navigasyon çubuğu
    ├── ConfigPanel.jsx  Bina konfigüratörü (sidebar)
    ├── Building.jsx  Three.js bina (iframe)
    └── ui.jsx        Paylaşılan UI bileşenleri
```

#### 3.2 Kimlik Doğrulama Akışı

```
Kullanıcı → Auth.jsx (kayıt/giriş formu)
         → POST /api/register veya /api/login
         → token + user → state.jsx (Context)
         → AppLayout (korumalı rota) — token yoksa /kayit'a yönlendir
```

Token `localStorage`'da saklanıyor; sayfa yenilenince kullanıcı oturumu kaybolmuyor.

`AppLayout` bileşeni: `const { user } = useApp(); if (!user) return <Navigate to="/kayit" />`

#### 3.3 Bina Konfigürasyon Yönetimi

`state.jsx` içindeki `useApp()` hook'u global `cfg` durumunu tutuyor. `ConfigPanel` bu durumu güncelliyor; tüm sayfalar (Simulasyon, Epias, Yatirim) aynı `cfg`'yi API isteğine ekliyor. Kullanıcı oturum açıkken her simülasyondan sonra `PUT /api/profile/bina` ile bina konfigürasyonu sunucuya kaydediliyor.

#### 3.4 Canlı EPİAŞ Sayfası

`useDebounced` hook'u: Kullanıcı kesinti aralığı slider'ını hareket ettirirken 450 ms debounce — her px harekette API çağrısı yapılmıyor.

```jsx
const dReq = useDebounced({ cfg, kesintiSaatleri }, 450);
useEffect(() => {
  api.simulate({ config: dReq.cfg, kesinti_saatleri: dReq.kesintiSaatleri })
    .then(setSim);
}, [JSON.stringify(dReq)]);
```

#### 3.5 Yatırım & Çevre Sayfası

- Aylık tasarruf (12 ay × sezonsal güneş verimliliği)
- Amorti süresi hesabı: `toplam_yatırım / yıllık_tasarruf`
- CO₂ tasarrufu → ton/yıl → eşdeğer ağaç sayısı
- **PDF rapor:** Tarayıcının `window.open()` + `document.write()` API'si kullanılıyor; dış kütüphane gerektirmiyor. Baskı stili CSS ile biçimlendiriliyor.

#### 3.6 Uzman Modu Sayfası

3 sekme:
- **Algoritma Karşılaştırması** — SAC / TD3 / PPO / A2C günlük tasarruf karşılaştırması (Recharts BarChart + ErrorBar)
- **Fiyat Bilgisi Etkisi** — Ajanın önceden kaç saatlik fiyat bilgisiyle çalıştığının etkisi
- **Mevsimsel Analiz** — 12 ay × algoritma ısı haritası

---

### 4. Çok Dil Desteği (i18n)

`i18n.jsx` bileşeni: Türkçe, İngilizce ve Arapça destekli minimal i18n sistemi.

```javascript
const S = {
  "nav.sim": { tr: "Bina Simülasyonu", en: "Building Simulation", ar: "محاكاة المبنى" },
  "auth.register.title": { tr: "Hesap oluşturun", en: "Create your account", ar: "أنشئ حسابك" },
  // ...
}
```

Arapça seçildiğinde `document.dir = "rtl"` ayarlanıyor; tüm flexbox düzeni otomatik ayna görüntüsüne dönüşüyor.

`TopNav` içindeki `DilSecici` bileşeni: Bayrak + dil adı gösteren açılır menü, localStorage'da seçim saklanıyor.

---

### 5. Altyapı

#### 5.1 Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: smarthome
    ports: ["5432:5432"]
    volumes: [smarthome_pgdata:/var/lib/postgresql/data]
```

Geliştirme ortamı: `docker compose up -d` ile PostgreSQL ayağa kalkıyor. Üretim için `DATABASE_URL` ortam değişkeni değiştiriliyor.

#### 5.2 .env.example

Projeye katılacak geliştiricilerin ihtiyaç duyduğu tüm değişkenler belgelenmiş halde `.env.example`'a eklendi. Gerçek `.env` gitignore'da.

---

### 6. Teknik Öğrenimler

**FastAPI Dependency Injection:** `Depends(current_user)` pattern'ı — her endpoint'e `user: User = Depends(current_user)` parametresi ekleniyor; FastAPI header'ı çözümleyip kullanıcıyı bulup enjekte ediyor. `HTTPException(401)` yetkisiz erişimlerde otomatik fırlatılıyor.

**SQLAlchemy JSON sütunu:** `mapped_column(JSON, nullable=True)` — ilişkisel tabloya yapılandırılmamış veri saklamanın en basit yolu. Bina konfigürasyonu için ayrı tablo açmak yerine `User.bina` sütunu tercih edildi; config şeması zamanla değişebileceğinden migration maliyeti düşük tutuluyor.

**React Context API vs Zustand:** Global durum yönetimi için Zustand/Redux yerine `createContext` + `useReducer` tercih edildi. Bağımlılık eklenmedi, bundle boyutu küçük kaldı. Durum: `{ user, token, cfg }`.

**RTL (Right-to-Left) desteği:** CSS `direction: rtl` + flexbox kendi kendine ayna görüntüsüne geçiyor. Dikkat gerektiren noktalar: margin/padding yönleri, `text-align: left` → `start`, border-left → `border-inline-start`.

**PBKDF2 vs bcrypt:** bcrypt üretim standardı olarak önerilse de Python standart kütüphanesinde `hashlib.pbkdf2_hmac` mevcut; `bcrypt` veya `passlib` gibi ek bağımlılık gerektirmiyor. 200.000 iterasyon ile hesaplama süresi ~200 ms — kullanıcı kayıt/girişinde kabul edilebilir, brute-force için pahalı.

---

### 7. Git Commits (Gün 18)

```
PR #XX: feat/gun18-react-frontend-fastapi → feat/gun17-dashboard-redesign

95a661b feat(backend+frontend): add FastAPI backend + React frontend
         - backend/: FastAPI, PBKDF2 auth, SQLAlchemy (User + SimKaydi), PostgreSQL/SQLite
         - frontend/src/: 7 sayfa, 4 bileşen, i18n TR/EN/AR
         - docker-compose.yml (postgres:16)
         - .env.example
```

---

### Yarın (Gün 19)

Deploy hazırlığı: React uygulamasını `npm run build` ile üretim bundle'ına derleme, FastAPI'yi `uvicorn --workers 4` ile ayağa kaldırma, Nginx ile statik dosya sunumu ve API proxy konfigürasyonu. Gerekirse Railway veya Render üzerinde demo yayını.
