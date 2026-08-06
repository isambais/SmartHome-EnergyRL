# Staj Defteri — Gün 17

**Tarih:** 6 Ağustos 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 17 — 3D Bina Yenileme & Dashboard UI Redesign

### 1. Bugün Ne Yapıldı?

Dün oluşturulan Streamlit dashboard'unun görsel kalitesi ve kullanıcı deneyimi köklü biçimde iyileştirildi. Three.js ile yazılmış 3D bina görselleştirmesi tamamen sıfırdan yeniden yazıldı; gerçekçi mimari detaylar, dinamik gökyüzü sistemi ve tüm bina sistemlerinin 3D yansıması eklendi. Dashboard arayüzü landing page tasarımıyla tutarlı hale getirildi.

---

### 2. Three.js 3D Bina — Tam Yeniden Yazım

#### 2.1 Temel Sorun

Önceki Three.js implementasyonunda bina gövdesi `opacity: 0.5` şeffaf malzemeyle yazılmıştı. Bu yüzden katlar üst üste pizza kutusu gibi görünüyor, çatı binadan kopuk yüzüyordu. Profesyonel görünüm için tüm geometri ve malzeme sistemi sıfırdan kuruldu.

#### 2.2 Yeni Mimari

```
Bina geometrisi:
├── Temel (koyu beton)
├── Her kat için:
│   ├── Döşeme levhası (solid, gölge atıyor)
│   ├── Kolonlar (pencereler arası dikey duvar)
│   ├── Üst kiriş + windowsill
│   ├── Pencere camları (MeshStandardMaterial, gündüz yansıma / gece sarı)
│   ├── Pencere çerçeveleri (metal profil)
│   ├── İç ışık noktaları (gece saatlerinde PointLight)
│   └── Balkon + korkuluk (her katta)
├── Çatı: parapet duvarı + güneş panelleri (eğimli, ayaklı)
└── Giriş: kapı çerçevesi + metal kapı + 3 basamak merdiven
```

#### 2.3 Işıklandırma Sistemi

| Işık türü | Renk | Açıklama |
|---|---|---|
| `HemisphereLight` | gökyüzü→toprak | Yumuşak ambient dolgu |
| `DirectionalLight` | güneş rengi | Güneş pozisyonuna göre, gölge üretir |
| `AmbientLight` | beyaz | Minimum dolgu, gece görünürlüğü |
| `PointLight` (pencere) | `#fcd34d` | Gece yanar, 5 birim yarıçap |
| `DirectionalLight` (ay) | `#8899cc` | Gece modunda aktif |

#### 2.4 Dinamik Gökyüzü

Saat değerine göre 8 farklı gökyüzü renk kademesi:

| Saat aralığı | Durum | Arka plan rengi |
|---|---|---|
| 00–05 | Derin gece | `#01060f` |
| 05–06 | Gece sonu | `#040d1e` |
| 06–07 | Şafak | `#c45c1e` |
| 07–08 | Sabah altını | `#e8955a` |
| 08–17 | Gündüz | `#4a9fd4` |
| 17–18 | Öğleden sonra | `#6ab0d8` |
| 18–19 | Gün batımı | `#e07030` |
| 19–21 | Alaca karanlık | `#8a2a10` |
| 21–24 | Gece | `#02060e` |

Güneş diski saate göre yay çizerek hareket eder; şafak/gün batımında turuncu hale, öğlende beyaz glow efekti eklendi. Gece `dayF < 0.3` olduğunda 800 noktalı yıldız sistemi aktif olur.

---

### 3. Bina Sistemlerinin 3D'ye Yansıtılması

Her sistemin checkbox durumu Three.js'e `CFG` objesi üzerinden iletilir ve sahneye karşılık gelen 3D obje eklenir ya da eklenmez:

| Sistem | 3D Görsel |
|---|---|
| **HVAC** | Çatıda klima kasaları + fan çark geometrisi |
| **Su Pompası** | Çatıda silindirik metal tank + boru bağlantısı |
| **Güneş Isıtıcı** | Kolektör plakaları (PV'den daha dik açı, ~0.5 rad) + kırmızı sıcak su borusu |
| **Jeneratör** | Sol yan tarafta metal kasa + egzoz borusu + sarı plaka; kesintide kırmızı LED + duman küre |
| **Kamera** | 4 köşede güvenlik kamerası (braket + gövde + lens); gece IR PointLight |
| **EV Şarj** | Detaylı araç (gövde + kabin + cam + 4 tekerlek + farlar) + şarj direği + yeşil ekran |
| **Asansör** | Şeffaf şaft + sinüs hareketiyle yukarı-aşağı giden kabin |

**Teknik not:** `building_html()` fonksiyonuna `hvac`, `su_pompasi`, `kamera`, `gunes_isitici`, `jenerator` parametreleri eklendi. JSON serialize edilerek JavaScript `CFG` objesine aktarılıyor.

---

### 4. Dashboard UI Yenileme

#### 4.1 Emoji Temizliği

Streamlit'in varsayılan emoji etiketleri (`🏗️ Bina Konfigüratörü`, `🛗 Asansör`, `💰 Bugünkü tasarruf` vb.) landing page tasarımıyla tutarsız bir görünüm yaratıyordu. Tüm emoji'ler kaldırıldı; yerine temiz metin ve CSS ile stilize edilmiş etiketler kullanıldı.

#### 4.2 Saat Slider'ının Taşınması

**Önceki durum:** Saat slider'ı sidebar'ın en altındaydı — scroll yapmadan görünmüyordu. Kullanıcı "Saat kaydırıcısıyla günü gezin" yönlendirmesini görüyor fakat slider'ı bulamıyordu.

**Yeni durum:** Slider, 3D binanın hemen altına "Simülasyon saati" etiketi ile taşındı. Saat değişince `st.rerun()` ile sayfa anında yenileniyor.

#### 4.3 Ajan Kararı Badge

Simülasyonun en kritik çıktısı — ajan şu an ne yapıyor — öne çıkarıldı:

```python
karar_map = {
    "şarj":   ("decision-sarj",   "Batarya şarj ediliyor",   "Ucuz saat — enerji depolanıyor"),
    "deşarj": ("decision-desarj", "Batarya deşarj ediliyor", "Pahalı saat — depo kullanılıyor"),
    "bekle":  ("decision-bekle",  "Bekleniyor",              "Şarj/deşarj için uygun fiyat değil"),
}
```

Mavi (şarj) / Kırmızı (deşarj) / Gri (bekle) renk kodlaması; üçgen ok simgesi ve kısa açıklama metni ile.

#### 4.4 Metrik Kartlar

Native `st.metric()` yerine custom HTML kartlar: beyaz arka plan, ince border, `Inter` font, landing page renk paleti. Tasarruf yüzdesi hesabı da düzeltildi — önceki `%175 daha az fatura` matematiksel olarak yanlıştı, `tasarruf / taban_maliyet * 100` formülüne çevrildi.

---

### 5. Landing Page Geliştirmeleri

#### 5.1 Parallax 3D Hero

`HeroScene` komponenti: 7 bağımsız katman, her biri farklı `translateY` hızıyla scroll'a tepki verir:

| Katman | Hız katsayısı |
|---|---|
| Gökyüzü | 0.18 |
| Güneş | 0.22 |
| Uzak bulutlar | 0.30 |
| Yakın bulutlar | 0.24 |
| Enerji partikülleri | 0.35 |
| Şehir silüeti | 0.42 |
| Yeşil zemin | 0.55 |

`useEffect` içinde `window.addEventListener('scroll', handler, { passive: true })` ile performanslı scroll tracking; `willChange: 'transform'` ile GPU katmanı zorlanıyor.

#### 5.2 Scroll-linked Sticky Showcase

`StickyShowcase` komponenti: sol taraf `position: sticky; top: 14vh` ile sabit kalıyor, sağ taraftaki özellik kartları `minHeight: 68vh` ile scroll edilebilir. `IntersectionObserver` (threshold: 0.55) her kartın görünürlüğünü izleyerek `active` state'ini güncelliyor; `BuildingViz` SVG buna göre 5 durumdan birini gösteriyor.

#### 5.3 Bina Tipleri Yenileme

Emoji ikonlar → Tip başına özel SVG bina çizimleri (MustakilSvg, VillaSvg, ApartmanSvg, OfisSvg). Hover'da bina yeşile dönüyor, güneş panelleri sarıya yanıyor. Sabit değerler (`1 kat · 4 oda`) → gerçekçi aralıklar (`1–2 kat · 3–7 oda · 60–180 m²`).

---

### 6. Teknik Öğrenimler

**Three.js MeshStandardMaterial vs MeshPhongMaterial:** `Standard` PBR tabanlı — gerçek dünya ışık davranışı, `roughness` ve `metalness` parametreleri. `Phong` daha basit, `shininess` ile parlama kontrolü. Dashboard'da `Standard` tercih edildi çünkü HDR toneMapping (`ACESFilmicToneMapping`) ile daha doğal sonuç veriyor.

**Streamlit `st.rerun()`:** Slider değeri değişince sayfa yeniden render edilmesi için. `st.experimental_rerun()` eski API'ydi, Streamlit 1.27+ ile `st.rerun()` kullanılıyor.

**CSS `position: sticky` + IntersectionObserver:** Apple ürün sayfalarındaki scroll animasyon tekniği. Sticky element viewport'ta sabit kalırken sibling container scroll edilir; IO her section'ın görünürlüğünü %55 threshold ile izler.

**Git force push:** Yanlış branch'e giden commit'i ayırmak için `git reset --hard <hash>` + `git push --force`. Takım çalışmasında riskli — kendi feature branch'inde güvenli.

---

### 7. Git Commits (Gün 17)

```
PR #XX: feat/gun17-dashboard-redesign → feat/gun16-streamlit-dashboard
18d0466 feat(dashboard): redesign 3D building + UI — realistic Three.js, remove emojis, agent badge, saat slider
         feat(landing): add parallax 3D hero, sticky showcase, custom SVG building cards
```

---

### Yarın (Gün 18)

Diğer Streamlit sayfalarının (Canlı EPİAŞ, Yatırım & Çevre, Uzman Modu) UI'larını da landing page stiliyle uyumlu hale getirme. Deploy hazırlığı: `requirements.txt` güncelleme, Streamlit Cloud konfigürasyonu.
