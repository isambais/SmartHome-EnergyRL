# SmartHome Energy — Tek Site (Landing + Uygulama)

Tanıtım sayfası ve 4 sayfalık gerçek uygulama artık tek sitede:

- `/` — Landing (tanıtım sayfası, animasyonlu)
- `/simulasyon` — 🏠 Bina Simülasyonu (3D bina + konfigüratör)
- `/epias` — ⚡ Canlı EPİAŞ (kesinti senaryosu dahil)
- `/yatirim` — 💰 Yatırım & Çevre
- `/uzman` — 📊 Uzman Modu

## Çalıştırma

İki terminal:

```powershell
# Terminal 1 — API (proje kökünde)
pip install -r backend/requirements.txt   # ilk sefer
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Site
cd frontend
npm install                                # ilk sefer
npm run dev
```

Tarayıcı: http://localhost:5173 — landing açılır, "Dashboard'u Aç" gerçek sayfalara götürür.

## Notlar

- `/api` istekleri Vite proxy'siyle 8000 portundaki FastAPI'ye gider.
- Backend, `dashboard/core`'daki simülasyon/ajan/3D kodunu kullanır — `dashboard/` klasörünü silmeyin.
- `landing/` klasörü artık gereksiz (buraya taşındı); yedek olarak durabilir veya silinebilir.
