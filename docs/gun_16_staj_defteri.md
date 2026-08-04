# Staj Defteri — Gün 16

**Tarih:** 5 Ağustos 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 16 — Streamlit BMS Dashboard & Landing Page

### 1. Bugün Ne Yapıldı?

Projenin kullanıcıya yönelik katmanı tamamlandı: Streamlit tabanlı tam bir **Bina Yönetim Sistemi (BMS) dashboard**'u ve projeyi tanıtan bir **landing page** geliştirildi. Gereksiz klasörler (`frontend/`, `backend/`) proje ağacından temizlendi; `.gitignore`'a `node_modules/` eklendi.

---

### 2. Dashboard Mimarisi

#### 2.1 Klasör Yapısı

```
dashboard/
├── app.py                          ← Ana sayfa (4 sayfa bağlantısı)
├── core/
│   ├── config.py                   ← BinaConfig dataclass + tüketim formülleri
│   ├── theme.py                    ← Dark CSS (#0d1117) + Plotly şablonu
│   ├── agent.py                    ← SAC yükleme + HeuristicAgent fallback
│   ├── simulate.py                 ← 24 saatlik fizik simülasyonu
│   ├── data.py                     ← EPİAŞ API → CSV → sentetik fallback zinciri
│   ├── threejs.py                  ← Three.js 3D bina HTML (9.6 kB)
│   └── ui.py                       ← Sidebar konfigüratör + gunu_simule_et()
└── pages/
    ├── 1_🏠_Bina_Simulasyonu.py    ← 3D + Plotly grafik + metrik kartlar + öneriler
    ├── 2_⚡_Canli_EPIAS.py         ← EPİAŞ fiyat çubuğu + kesinti simülasyonu
    ├── 3_💰_Yatirim_ve_Cevre.py    ← Amorti + CO₂ + fiyat duyarlılık analizi
    └── 4_📊_Uzman_Modu.py          ← Algoritma karşılaştırması + ısı haritası + mevsimsel
```

#### 2.2 Veri Akışı

```
EPİAŞ API (TGT auth)
    ↓ başarısız
arşiv CSV (data/epias_combined.csv)
    ↓ yok
Sentetik (EPİAŞ deseni, ±gürültü)
    ↓
gun_fiyati() → saatlik 24 TL/MWh dizisi
    ↓
gunu_simule_et(cfg) → simulate_day(fiyat, güneş, talep, batarya, ajan)
    ↓
DataFrame (24 satır × 20 sütun) → Plotly + Three.js + metrik kartlar
```

---

### 3. BinaConfig Tasarımı

`config.py`'deki `BinaConfig` dataclass projenin tüm bina parametrelerini tutar:

| Parametre | Açıklama | Varsayılan (Apartman) |
|---|---|---|
| `kat` | Kat sayısı | 5 |
| `daire_per_kat` | Kat başına daire | 3 |
| `aktif_daire` | Gerçekten oturulan daire | 12 |
| `oda` | Daire başına oda | 3 |
| `cati_alani` | Panel kurulum alanı (m²) | 140 |
| `asansor/hvac/su_pompasi/ev_sarj/...` | Sistem varlığı | tip'e göre |

**Türetilmiş değerler** (property):
- `gunluk_tuketim_kwh` = `aktif_daire × oda × 1.8 + asansör×8 + hvac×kat×3 + ...`
- `batarya_kwh` = `gunluk_tuketim × 0.4`
- `batarya_guc_kw` = `batarya_kwh / 2` (C/2 şarj hızı)
- `panel_sayisi` = `cati_alani / 1.7 m²`
- `panel_kw` = `panel_sayisi × 0.45 kW`

---

### 4. Simülasyon Fiziği (`simulate.py`)

24 saatlik döngüde her saat için:

1. **Gözlem vektörü** (106 boyut) `build_obs()` ile oluşturulur — `energy_env.py` ile birebir aynı düzen
2. **Ajan kararı**: `act(obs)` → aksiyon ∈ [-1, 1] (deşarj ↔ şarj)
3. **Batarya fiziği**: `verim=0.95`, `satis_orani=0.60`, `min_soc=0.10`, `oz_desarj=0.0005/h`
4. **Kesinti senaryosu**: grid yoksa önce batarya, sonra opsiyonel jeneratör (12 TL/kWh)
5. **Taban maliyet** hesaplanır (şebekeden tam çekseydi ne öderdi?) → tasarruf = taban − net

**Ölçekleme**: Ajan 10 kWh ev sistemi için eğitilmiş. Bina `k = bina_batarya / 10` katsayısıyla ajan ölçeğine indirilir, kararlar gerçek ölçeğe çevrilir.

---

### 5. Three.js 3D Görselleştirme (`threejs.py`)

`building_html(cfg, saat, soc, gunes_kw, outage)` fonksiyonu ~9.6 kB tek HTML çıktısı üretir:

- Bina yüksekliği kat sayısına göre dinamik
- Pencereler: aktif daire + gece saati kombinasyonuna göre aydınlık/karanlık
- Güneş panelleri: `gunes_kw` değerine göre parlama yoğunluğu
- Batarya ünitesi: SOC değerine göre yeşil→sarı→kırmızı renk geçişi
- Asansör: gündüz saatlerinde animasyonlu hareket
- EV aracı + şarj direği
- Kesinti modu: kırmızı yanıp sönen alarm
- Gün/gece gökyüzü döngüsü, güneş/ay pozisyonu
- Mouse drag: döndür; scroll: yakınlaştır
- HUD overlay: saat, batarya %, güneş kW, aktif daire

---

### 6. Sayfa İçerikleri

**Sayfa 1 — Bina Simülasyonu:**  
3D bina animasyonu + 4 metrik kart (tasarruf TL, batarya SOC, güneş kW, toplam tüketim) + dual-axis Plotly grafiği (fiyat + SOC + güneş + şarj/deşarj kararları) + doğal dil önerileri.

**Sayfa 2 — Canlı EPİAŞ:**  
EPİAŞ oturum bilgisi girişi + saatlik fiyat çubuğu (şu anki saat sarı, kesinti saatleri kırmızı) + kesinti simülasyonu toggle + saatlik karar tablosu.

**Sayfa 3 — Yatırım & Çevre:**  
Batarya + panel yatırım maliyeti girişi → yıllık tasarruf tahmini (4 mevsim × temsilci gün simülasyonu) → amorti süresi → CO₂ ton tasarrufu (450 gCO₂/kWh Türkiye faktörü) → ağaç/araba eşdeğeri. Fiyat duyarlılık analizi grafiği.

**Sayfa 4 — Uzman Modu:**  
Tab 1: `logs/forecast_comparison.csv`'den SAC/TD3/PPO/A2C Oracle performans bar grafiği.  
Tab 2: Politika × Fiyat modu ısı haritası (Oracle/Forecast/Naive).  
Tab 3: aligned_dataset'ten aylık fiyat profili + Yaz vs Kış saatlik fiyat & güneş karşılaştırması.

---

### 7. Tasarım Kararları — Kullanıcı Merkezli Yaklaşım

**Algoritma adları gizlendi:** SAC/TD3/PPO/A2C isimleri normal kullanıcıya bir şey ifade etmiyor. Dashboard "Yapay Zekâ Ajanı" olarak sunar; algoritma detayları yalnızca Uzman Modu'nda görünür.

**Fallback zinciri:** API → CSV → Sentetik. Kullanıcı hiçbir zaman hata ekranı görmez.

**HeuristicAgent:** Model yüklenemezse (SB3 kurulu değilse) eşik tabanlı kural politikası otomatik devreye girer, dashboard çökmez.

---

### 8. Landing Page (`landing/`)

Proje tanıtım sayfası FintechX template'inden SmartHome-EnergyRL için tamamen yeniden yazıldı:

- **Nav**: SmartHome Energy RL logo + Türkçe menü + "Dashboard'u Aç" CTA
- **Hero**: Sahtesi olmayan EPİAŞ fiyat grafiği mockup'ı, şarj/deşarj karar üçgenleri
- **Bina tipleri**: Müstakil Ev / Villa / Apartman / Ofis Binası kartları
- **Önce/Sonra**: FintechX'ten SmartHome RL farkı (toggle animasyonu)
- **Özellikler**: 3D görselleştirme, SAC/TD3, EPİAŞ API fallback, batarya fiziği, kesinti koruması
- **Nasıl çalışır**: 3 adım interactive panel (Bina Tanımla → Simüle Et → Sonuçları İncele)
- **İstatistikler**: Gerçek proje sonuçları (SAC +14.4 TL/gün, ±0.2 TL robustluk, %29.93 sMAPE)
- **SSS**: EPİAŞ bağlantısı, eğitim detayları, batarya boyutu formülü
- **Footer**: GitHub bağlantıları, proje bilgisi

---

### 9. Temizlenen Gereksiz Klasörler

| Klasör | Durum | Neden |
|---|---|---|
| `frontend/` | Silindi (kaynak) | React dashboard, Streamlit ile değiştirildi |
| `backend/` | Silindi | FastAPI backend, Streamlit ile değiştirildi |
| `node_modules/` | `.gitignore`'a eklendi | `npm install` ile yeniden oluşturulabilir |

---

### 10. Git Commits (Gün 16)

```
PR #39: feat/gun16-streamlit-dashboard → feat/gun15-forecast-comparison
[commit hash] feat(dashboard): add Streamlit BMS dashboard — 4 pages + core modules + Three.js
[commit hash] feat(landing): rewrite landing page for SmartHome-EnergyRL (FintechX → BMS)
[commit hash] chore: remove frontend/ and backend/ folders, add node_modules to .gitignore
[commit hash] docs: add Gün 16 staj defteri
```

---

### 11. Teknik Öğrenimler

**`st.cache_resource` vs `st.cache_data`:** Model yükleme (`get_agent()`) `@st.cache_resource` ile — nesne tüm kullanıcı oturumlarında paylaşılır, her request'te yeniden yüklenmez. DataFrame sonuçları `@st.cache_data` ile — immutable serileştirilebilir veri.

**Streamlit multi-page:** `pages/` klasörü Streamlit 1.20+ ile otomatik algılanır. Dosya adı prefix'i sayfa sıralamasını (`1_`, `2_`, ...) ve sidebar görünümünü belirler. Emoji dosya adında doğrudan çalışır.

**Three.js `st.components.v1.html()`:** Three.js render'ı `components.html()` içine gömülüyor. iframe sandbox nedeniyle dış CDN yüklenmesi için `allow-scripts` gerekli — Streamlit bunu varsayılan olarak açar.

**Ajan ölçekleme sorunu:** SAC 10 kWh ev için eğitildi, bina 40 kWh bataryaya sahip. Çözüm: tüm büyüklükler `k = bina_kwh / 10` katsayısıyla ajan ölçeğine indirilip kararlar gerçek ölçeğe çevrildi. Bu yaklaşım fizik doğrusallığı varsaydığı için gerçek dünyada ancak yaklaşık doğru; tam doğruluk için binaya özel yeniden eğitim gerekir.

**`.gitignore` ve `node_modules`:** `node_modules/` klasörü binlerce küçük dosya içerdiğinden git repolarına kesinlikle eklenmemeli. `npm install` ile saniyeler içinde yeniden oluşturulur.

---

### Yarın (Gün 17)

Landing page deploy (Vercel/Netlify) ve Streamlit dashboard deploy (Streamlit Cloud). `requirements.txt` güncelleme, `CLAUDE.md` proje dokümantasyonu.
