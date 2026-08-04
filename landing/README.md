# FintechX Tarzı Landing Sitesi

FintechX (Webestica) Framer şablonunun tasarımına sadık React + framer-motion uygulaması.
Bölümler: hero + dashboard mockup, logo şeridi, Before/After anahtarı, bento özellik
kartları, platform önizleme, nasıl çalışır (adım sekmeleri), güvenlik, kullanım
senaryoları, kurucu alıntısı, istatistik satırları, yorumlar, fiyatlandırma
(aylık/yıllık anahtarı), SSS, CTA, footer.

Not: Şablonun kendi görselleri telif nedeniyle kullanılmadı; aynı estetikte serbest
lisanslı Unsplash fotoğrafları ve elle çizilmiş SVG grafikler kullanıldı.

## Çalıştırma

```powershell
cd landing
npm install
npm run dev
```

Tarayıcıda: http://localhost:5174

"Demoyu Aç" butonları asıl uygulamaya (http://localhost:5173) yönlenir — istersen
`src/App.jsx` içinde bu adresi değiştir.

## Yayınlama

`npm run build` → `dist/` klasörü oluşur; Vercel, Netlify veya GitHub Pages'e
doğrudan yüklenebilir.
