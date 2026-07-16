# Implementation Plan — SmartHome Energy RL

### Pekiştirmeli Öğrenme (RL) Tabanlı Akıllı Ev Enerji Yönetim Ajanı

> **Proje Adı:** SmartHome Energy RL
> **Geliştirici:** Isam (Solo Stajyer)
> **Süre:** 20 iş günü (4 hafta)
> **Alan:** AI/ML — Pekiştirmeli Öğrenme (Reinforcement Learning)
> **Dil/Framework:** Python, Gymnasium, Stable-Baselines3, Streamlit
> **Doküman Sürümü:** v1.1 (mentor geri bildirimiyle curriculum learning yaklaşımı eklendi)
> **Doküman Türü:** Implementation Plan / Tek Doğruluk Kaynağı (Single Source of Truth)

> **Bu dokümanın amacı:** Projenin problem tanımını, RL ortam tasarımını, mimarisini, veri kaynaklarını ve 20 günlük yol haritasını gri nokta bırakmadan tanımlamaktır. Geliştirme süreci bu plana birebir uyarak ilerleyecektir. Plandan sapma gerekirse önce bu doküman güncellenecek, sonra kod yazılacaktır.

---

## İçindekiler

1. Yönetici Özeti
2. Problem Tanımı ve Hedefler
3. Kapsam
4. Teknoloji Yığını
5. Proje Dizin Yapısı
6. RL Problem Formülasyonu (Ortam Tasarımı)
7. Sistem Mimarisi & Modüller
8. Veri Kaynakları ve Ön İşleme
9. Ödül Fonksiyonu ve Eğitim Stratejisi
10. Baseline Karşılaştırma ve Değerlendirme Metrikleri
11. Dashboard / Görselleştirme
12. Kodlama Standartları ve Optimizasyon
13. Test Stratejisi
14. Dokümantasyon Yapısı (docs/)
15. 20 İş Günlük Yol Haritası
16. Haftalık Sprint Özeti
17. Git Workflow & PR Süreci
18. GitHub Projects Board & Issue Yönetimi
19. Daily Standup
20. Risk Yönetimi
21. Definition of Done
22. Teslim Edilecekler

---

## 1. Yönetici Özeti

SmartHome Energy RL, güneş paneli ve batarya deposu olan bir evin/binanın enerji maliyetini minimize etmeyi öğrenen bir pekiştirmeli öğrenme (RL) ajanıdır. Ajan; saatlik elektrik fiyatı, güneş üretim tahmini, batarya doluluk seviyesi ve ev talebini gözlemleyerek bataryayı ne zaman şarj/deşarj edeceğine ve ertelenebilir cihazları (çamaşır makinesi, bulaşık makinesi gibi) ne zaman çalıştıracağına karar verir.

Çıktımız: gerçek açık veri kaynaklarıyla (EPİAŞ elektrik fiyatı, açık güneş üretim simülasyonu, açık ev tüketim profili) beslenen, "optimize edilmemiş" bir temel senaryoya (baseline) kıyasla ölçülebilir yüzde tasarruf sağlayan, eğitilmiş bir RL ajanı ve bu karşılaştırmayı görselleştiren bir Streamlit dashboard.

---

## 2. Problem Tanımı ve Hedefler

### 2.1 Çözülen Problem

Ev/bina sahipleri elektrik fiyatının saatlik değiştiğinin (gün öncesi piyasa fiyatlandırması) ve güneş üretiminin gün içinde dalgalandığının çoğunlukla farkında değil ya da bunu optimize edecek bir araçları yok. Batarya ve ertelenebilir yükler manuel/sabit kurallarla yönetildiğinde önemli bir tasarruf potansiyeli kaçırılıyor. Bu proje, bu kararı otomatikleştiren ve öğrenen bir ajan sunuyor.

### 2.2 Başarı Kriterleri (Definition of Success)

* [ ] Özel bir Gymnasium ortamı (environment) kusursuz çalışacak; saatlik state/action/reward döngüsü doğru işleyecek.
* [ ] Stable-Baselines3 (PPO) ile eğitilen ajan, "optimize edilmemiş" (batarya kullanılmayan/sabit kurallı) senaryoya kıyasla ölçülebilir bir maliyet tasarrufu sağlayacak.
* [ ] Sadece açık ve ücretsiz veri kaynakları kullanılacak (EPİAŞ, açık güneş/tüketim veri setleri) — özel kayıt/onay bekleyen veri seti kullanılmayacak.
* [ ] Eğitim süreci ve sonuçlar tekrarlanabilir olacak (sabit random seed, loglanmış deneyler).
* [ ] Streamlit dashboard üzerinden bir günün/haftalık periyodun simülasyonu ve maliyet karşılaştırması görselleştirilecek.
* [ ] Tüm repo ve iş akışı GitHub Projects (Kanban) ve branch/PR sistemiyle yönetilecek.
* [ ] Curriculum'un her aşaması (arbitraj, öz-tüketim, cihaz+tahmin) bir öncekinin davranışı doğrulanmadan geçilmeyecek şekilde sırayla tamamlanacak.
* [ ] Ajanın "cihaz çalıştırma oranı" metriği, reward hacking kontrolü olarak maliyet metriğinden ayrı raporlanacak.

---

## 3. Kapsam

### 3.1 Kapsam İçi (20 günde teslimi hedeflenen)

* Özel bir Gymnasium ortamı: saatlik zaman adımlı, güneş üretimi + elektrik fiyatı + batarya + ertelenebilir yük simülasyonu.
* EPİAŞ gün öncesi piyasa fiyat verisinin çekilmesi/işlenmesi.
* Açık bir güneş üretim profili (PVWatts benzeri, ya da parametrik sentetik günlük eğri) ve açık bir ev tüketim profili (ör. UK-DALE'den türetilmiş ya da sentetik, gerçekçi) entegrasyonu.
* Stable-Baselines3 (PPO) ile ajan eğitimi ve hiperparametre denemeleri.
* İki baseline karşılaştırması: (a) "batarya yok / hep şebekeden çek", (b) basit sezgisel kural (ör. "güneş fazlaysa şarj et, fiyat düşükse şarj et") — ikisi tek bir kod yolunda (batarya kapasitesi 0 = baseline 1 özel durumu) sadeleştirilerek uygulanır.
* **Kısa vadeli (24 saatlik) elektrik fiyat tahmin modülü:** basit bir zaman serisi modeliyle (XGBoost veya ARIMA — derin öğrenme değil) ertesi günün saatlik fiyatı tahmin edilir. Eğitilmiş RL ajanı yeniden eğitilmeden, üç farklı fiyat bilgisi modunda (oracle/gerçek, tahmin edilen, naive/dünün fiyatı) test edilerek "tahmin hatasının gerçek tasarrufu ne kadar etkilediği" ölçülür.
* Streamlit tabanlı bir dashboard: günlük/haftalık maliyet karşılaştırma grafiği, ajanın aldığı kararların zaman çizelgesi, oracle/tahmin/naive karşılaştırması.
* Deney sonuçlarının ve eğitim loglarının (TensorBoard veya basit CSV) düzenli tutulması.

### 3.2 Kapsam Dışı (Gelecek faz veya projeden çıkarılanlar)

* Gerçek bir eve/donanıma bağlanma (IoT entegrasyonu) — proje tamamen simülasyon ortamında kalacak.
* Çoklu bina / mahalle ölçeğinde şebeke optimizasyonu (multi-agent) — tek bir ev/bina ile sınırlı.
* Karbon emisyonu optimizasyonu (stretch goal, süre kalırsa eklenir, kapsam içi değil).
* **Tam ölçekli, üretim kalitesinde bir fiyat tahmin sistemi** (derin öğrenme tabanlı, çoklu bölge/piyasa, kendi başına bir ürün) — sadece basit, hafif bir kısa vadeli tahmin modülü çekirdek deneye ek olarak dahil edilmiştir; bu modülün amacı tahmin doğruluğunu maksimize etmek değil, RL ajanının tahmin belirsizliğine dayanıklılığını göstermektir.

---

## 4. Teknoloji Yığını

| Katman | Teknoloji | Gerekçe |
| --- | --- | --- |
| **Dil** | Python 3.11+ | RL ve veri bilimi ekosisteminin standart dili. |
| **RL Ortamı** | Gymnasium | Endüstri standardı ortam arayüzü (eski OpenAI Gym'in devamı). |
| **RL Algoritması / Kütüphane** | Stable-Baselines3 (PPO) | İyi test edilmiş, hazır ve güvenilir RL algoritmaları; sıfırdan RL yazmaktan çok daha az risk. |
| **Veri İşleme** | pandas, numpy | Zaman serisi verisi (fiyat, üretim, talep) işleme. |
| **Elektrik Fiyat Verisi** | EPİAŞ Şeffaflık Platformu (açık, gün öncesi piyasa fiyatı) | Türkiye'ye özgü, gerçek ve güncel, kayıt/onay beklemeyen açık veri. |
| **Güneş Üretim Verisi** | PVWatts (NREL, açık) veya parametrik sentetik profil | Ücretsiz, coğrafi konuma göre gerçekçi üretim eğrisi. |
| **Ev Tüketim Verisi** | UK-DALE (akademik açık veri) veya parametrik sentetik profil | İyi belgelenmiş, gerçekçi talep paternleri. |
| **Görselleştirme / Dashboard** | Streamlit + Plotly | Hızlı kurulum, Python'da native, solo geliştirme için en az altyapı riski. |
| **Deney Takibi** | TensorBoard (Stable-Baselines3 entegre) | Eğitim eğrilerini (reward, loss) izlemek için standart araç. |
| **Fiyat Tahmini** | XGBoost veya statsmodels (ARIMA) | Hafif, hızlı kurulan, iyi belgelenmiş klasik zaman serisi yöntemleri — ayrı bir derin öğrenme projesi açmaya gerek yok. |
| **Versiyon Kontrol** | Git + GitHub | Main dalı korumalı, PR bazlı geliştirme. |
| **Proje Yönetimi** | GitHub Projects (Kanban) | To Do / In Progress / Review / Done akışı. |

---

## 5. Proje Dizin Yapısı

```
SmartHome-EnergyRL/
├── src/
│   ├── env/
│   │   └── energy_env.py         # Özel Gymnasium ortamı (SmartHomeEnergyEnv)
│   ├── data/
│   │   ├── epias_loader.py       # EPİAŞ fiyat verisi çekme/işleme
│   │   ├── solar_profile.py      # Güneş üretim profili üretici
│   │   └── demand_profile.py     # Ev tüketim profili üretici
│   ├── agents/
│   │   └── train_ppo.py          # PPO eğitim scripti (Stable-Baselines3)
│   ├── baselines/
│   │   └── rule_based.py         # Sezgisel kural (batarya kapasitesi=0 → "batarya yok" özel durumu)
│   ├── forecasting/
│   │   └── price_forecast.py     # Kısa vadeli (24 saatlik) fiyat tahmin modeli (XGBoost/ARIMA)
│   ├── evaluation/
│   │   └── compare.py            # Ajan vs baseline + oracle/tahmin/naive fiyat karşılaştırması
│   └── dashboard/
│       └── app.py                # Streamlit dashboard
├── data/
│   ├── raw/                      # Ham veri (EPİAŞ CSV, vb.)
│   └── processed/                # İşlenmiş, ortam-hazır veri
├── models/                       # Eğitilmiş model checkpoint'leri
├── notebooks/                    # Keşif / prototipleme not defterleri
├── tests/                        # Birim testleri
├── docs/                         # GDD tarzı tasarım notları, deney sonuçları
├── .gitignore
├── requirements.txt
└── implementation_plan.md        # BU DOSYA
```

---

## 6. RL Problem Formülasyonu (Ortam Tasarımı)

**Zaman adımı:** 1 saat. Bir bölüm (episode) 24 saat (1 gün) veya 168 saat (1 hafta) olarak tanımlanır.

**Curriculum (aşamalı) yaklaşım — mentor geri bildirimiyle eklendi:** Ortam tek seferde tam karmaşıklığıyla kurulmuyor; RL'de en büyük risk olan yakınsama (convergence) sorununu ve ödül fonksiyonu açıklarının sömürülmesini (reward hacking) önlemek için üç aşamada inşa edilip her aşamada ayrı eğitilip doğrulanıyor. Bir sonraki aşamaya, mevcut aşamanın beklenen davranışı gözlemlenmeden geçilmez.

**Curriculum Aşama 1 — Saf Batarya Arbitrajı:**
* Gözlem: sadece batarya SOC'si + 24 saatlik elektrik fiyatı (güneş, ev talebi, cihazlar yok).
* Aksiyon: `battery_action` ∈ [-1, 1] (tek boyutlu, sürekli).
* Beklenti: ajanın gece ucuzken şarj edip akşam pahalıyken deşarj etmeyi (arbitraj) kusursuz öğrenmesi.

**Curriculum Aşama 2 — Pasif Tüketim ve Güneş Entegrasyonu:**
* Gözlem'e eklenir: kontrol edilemeyen sabit ev talebi (Load, kW) ve güneş üretimi (PV, kW).
* Aksiyon uzayı aynı kalır (hâlâ sadece batarya).
* Ödül fonksiyonu güncellenir: güneş varken şebekeden çekmemeyi, bataryayı önce ev ihtiyacı için kullanmayı (şebekeye satmadan önce) önceliklendirecek şekilde.
* Beklenti: ajanın öz-tüketim önceliğini (self-consumption) ve maliyet/konfor dengesini öğrenmesi.

**Curriculum Aşama 3 — Ertelenebilir Cihazlar ve Tahmin Dayanıklılığı:**
* Aksiyon uzayı genişler: sürekli `battery_action` + ayrık (discrete) `deferrable_load_action` (çamaşır makinesi gibi cihazın o saat çalıştırılıp çalıştırılmayacağı).
* Gözleme cihazın o gün içinde henüz çalıştırılıp çalıştırılmadığı (binary flag) eklenir.
* Kusursuz (oracle) fiyat verisi kaldırılır, yerine gürültülü kısa vadeli tahmin verisi konur (bkz. 6.1).
* Beklenti: sistemin belirsizlik altında ne kadar dayanıklı kaldığının ve cihazları en ucuz/güneşli saatlere kaydırıp kaydıramadığının ölçülmesi.

**Ödül (Reward, genel form):** `reward = -(saatlik_şebeke_maliyeti) - ceza_terimleri`
* Şebeke maliyeti = (şebekeden çekilen kWh) × (o saatin fiyatı)
* Ceza terimleri: batarya sınırlarını zorlamak (aşırı şarj/deşarj), ertelenebilir yükün gün sonuna kadar hiç çalıştırılmaması (gün sonunda büyük ceza — bkz. 9. bölümdeki reward hacking notu).

**Bölüm sonu (episode termination):** 24 veya 168 saat dolunca bölüm biter, ortam sıfırlanır (yeni bir gün/hafta verisiyle).

### 6.1 Fiyat Bilgisi Modları (Oracle / Tahmin / Naive)

Ortam, gözlemdeki "elektrik fiyatı" alanını üç farklı modda besleyebilecek şekilde parametrize edilir:

* **Oracle:** O saatin gerçek/bilinen fiyatı (üst sınır — ajanın olabilecek en iyi performansı).
* **Tahmin (forecast):** `price_forecast.py` modülünün ürettiği 24 saatlik tahmin (gerçekçi senaryo).
* **Naive:** Bir önceki günün aynı saatteki fiyatı (en basit olası tahmin, alt sınır kıyaslaması).

Ajan yalnızca oracle modunda eğitilir; diğer iki mod sadece **test/değerlendirme aşamasında** kullanılır (yeniden eğitim gerekmez). Bu, "tahmin hatası gerçek tasarrufu ne kadar azaltıyor" sorusuna ekstra bir RL eğitim döngüsü gerektirmeden cevap verir.

---

## 7. Sistem Mimarisi & Modüller

* `SmartHomeEnergyEnv` (Gymnasium `Env` alt sınıfı): `reset()` ve `step()` metotlarıyla standart RL arayüzünü uygular. İçeride batarya fizik modeli (basit doğrusal şarj/deşarj verimliliği, ör. %90 round-trip efficiency) bulunur.
* `EpiasLoader`: EPİAŞ Şeffaflık Platformu'ndan (veya önceden indirilmiş CSV'den) saatlik piyasa takas fiyatını (PTF) çeker ve ortamın beklediği formata normalize eder.
* `SolarProfileGenerator` / `DemandProfileGenerator`: Gerçekçi ama basitleştirilmiş, mevsimsel ve günlük döngüsü olan üretim/talep eğrileri üretir (açık veri setinden türetilmiş parametrelerle).
* `train_ppo.py`: Stable-Baselines3 `PPO` sınıfını `SmartHomeEnergyEnv` üzerinde eğitir, checkpoint kaydeder, TensorBoard loglar.
* `baselines/rule_based.py`: Aynı ortamda çalışan, öğrenmeyen sezgisel strateji (batarya kapasitesi 0 verilirse "batarya yok" özel durumuna döner).
* `forecasting/price_forecast.py`: Geçmiş EPİAŞ verisiyle eğitilen, ertesi günün 24 saatlik fiyatını tahmin eden hafif bir model (XGBoost/ARIMA) ve tahmin doğruluğu (MAPE) raporu.
* `evaluation/compare.py`: Eğitilmiş ajanı ve baseline'ı aynı test verisi (görülmemiş günler) üzerinde çalıştırıp toplam maliyet/tasarruf metriklerini hesaplar; ayrıca aynı ajanı oracle/tahmin/naive fiyat modlarında test ederek tahmin hassasiyetinin etkisini ölçer.
* `dashboard/app.py`: Sonuçları, bir günün saatlik karar/maliyet dökümünü ve oracle/tahmin/naive karşılaştırmasını görselleştirir.

---

## 8. Veri Kaynakları ve Ön İşleme

| Veri | Kaynak | Erişim | Ön İşleme |
| --- | --- | --- | --- |
| Elektrik fiyatı (PTF) | EPİAŞ Şeffaflık Platformu | Açık, kayıt gerektirmez | Saatlik seriye normalize, eksik saatler enterpole edilir |
| Güneş üretimi | NREL PVWatts (açık) veya parametrik sentetik | Açık / üretilmiş | Konuma göre ölçeklenmiş kW eğrisi, mevsimsellik eklenir |
| Ev talebi | UK-DALE (akademik açık) veya parametrik sentetik | Açık | Ortalama bir konut profiline indirgenir, gürültü eklenir |

Bu üçünün saatlik zaman damgalarıyla hizalanması (aynı takvime oturtulması) ön işlemenin en kritik adımıdır — bu adım aksarsa ortam yanlış sinyal üretir.

---

## 9. Ödül Fonksiyonu ve Eğitim Stratejisi

* Eğitim, 6. bölümdeki curriculum sırasıyla yapılır: her aşama kendi içinde eğitilip beklenen davranış (arbitraj, öz-tüketim, cihaz zamanlama) gözlemlenmeden bir sonraki aşamaya geçilmez.
* Eğitim, farklı günler/mevsimler içeren bir veri kümesi üzerinde rastgele örneklenen bölümlerle yapılır (genelleme için).
* Ödül fonksiyonu ağırlıkları (maliyet vs ceza terimleri) küçük bir grid-search ile kalibre edilir.
* Eğitim ilerlemesi TensorBoard'da izlenir (ortalama bölüm ödülü, kayıp eğrileri).
* Aşırı öğrenmeyi (overfitting) önlemek için eğitim/test günleri ayrılır — test günleri eğitimde hiç görülmez.

**Reward hacking kontrolü (mentor uyarısı):** Ödül fonksiyonu sadece maliyeti düşürmeyi ödüllendirirse, ajan "kolay yolu" seçip ertelenebilir cihazı hiçbir zaman çalıştırmamayı öğrenebilir (fatura düşer ama gerçek ihtiyaç karşılanmaz) — bu klasik bir reward hacking örneğidir. Bunu önlemek için Curriculum Aşama 3'te cihazın gün sonuna kadar hiç çalıştırılmamasına sert bir ceza eklenir ve eğitim sonunda ajanın "cihazı çalıştırma oranı" metriği ayrıca raporlanır (sadece maliyet metriğine güvenilmez).

---

## 10. Baseline Karşılaştırma ve Değerlendirme Metrikleri

* **Metrikler:** toplam şebeke maliyeti (TL), baseline'a göre % tasarruf, batarya kullanım verimliliği, ertelenebilir yükün gün içinde başarıyla çalıştırılma oranı, fiyat tahmin doğruluğu (MAPE).
* **Karşılaştırma 1 (ajan kalitesi):** RL ajanı vs sezgisel kural vs "batarya yok" özel durumu, aynı test günlerinde (oracle fiyatla).
* **Karşılaştırma 2 (tahmin dayanıklılığı):** aynı eğitilmiş RL ajanının oracle / tahmin edilen / naive fiyat girdisiyle test edildiğinde ne kadar tasarruf kaybettiği.
* Sonuçlar en az 10 farklı test günü üzerinde ortalanır (tek bir günlük sonuç yanıltıcı olabilir).

---

## 11. Dashboard / Görselleştirme

* **Ana Sayfa:** Seçilen bir test günü için saatlik fiyat, güneş üretimi, batarya SOC ve ajanın kararlarının üst üste çizildiği bir zaman serisi grafiği.
* **Karşılaştırma Paneli:** RL ajanı / Baseline 1 / Baseline 2 için toplam maliyet çubuk grafiği ve % tasarruf göstergesi.
* **Deney Geçmişi:** Farklı eğitim koşularının (hyperparametre setlerinin) sonuçlarını karşılaştıran basit bir tablo.

---

## 12. Kodlama Standartları ve Optimizasyon

* İsimlendirme: `snake_case` (fonksiyon/değişken), `PascalCase` (sınıflar), PEP8 uyumlu.
* Tip ipuçları (type hints) tüm public fonksiyonlarda kullanılır.
* Ortam (`env`) kodu Gymnasium API standardına (`reset`, `step`, `observation_space`, `action_space`) birebir uyar.
* Rastgelelik kontrolü: tüm deneyler sabit `seed` ile başlatılır, sonuçlar tekrarlanabilir olur.
* `black` + `ruff` ile otomatik formatlama/lint.

---

## 13. Test Stratejisi

* **Birim testleri:** `SmartHomeEnergyEnv.step()` fonksiyonunun batarya sınırlarını (0-1 SOC) asla aşmadığını, ödülün beklenen aralıkta olduğunu doğrulayan testler.
* **Sağlamlık testi:** Ortamın Gymnasium `check_env()` yardımcı fonksiyonundan hatasız geçmesi.
* **Deney doğrulama:** Eğitilen ajanın rastgele bir politikadan (random baseline) anlamlı ölçüde iyi performans gösterdiğinin doğrulanması.

---

## 14. Dokümantasyon Yapısı (docs/)

```
docs/
├── design/
│   └── reward-function-notes.md   # Ödül fonksiyonu tasarım gerekçeleri
├── experiments/
│   └── results-log.md             # Her deney koşusunun özeti ve sonuçları
└── data-sources.md                 # Kullanılan veri kaynaklarının detayları ve erişim notları
```

---

## 15. 20 İş Günlük Yol Haritası

Her gün en az 1 anlamlı commit atılması **zorunludur**.

### 🟦 Faz 0 — Kurulum ve Veri Keşfi (Gün 1-4)

* **Gün 1:** GitHub repository oluşturulması, Projects (Kanban) board kurulumu, Python ortamı (venv), `.gitignore`, ilk commit olarak bu `implementation_plan.md`.
* **Gün 2:** EPİAŞ Şeffaflık Platformu'ndan örnek fiyat verisinin çekilmesi ve formatının incelenmesi (`EpiasLoader` iskeletinin yazılması).
* **Gün 3:** Güneş üretim ve ev talebi için açık veri kaynaklarının (PVWatts, UK-DALE) araştırılması; erişilemezse parametrik sentetik profil planının netleştirilmesi.
* **Gün 4:** Üç veri kaynağının saatlik takvimde hizalanması ve `data/processed/` altında birleşik bir veri seti oluşturulması.

### 🟩 Faz 1 — Curriculum Aşama 1: Saf Batarya Arbitrajı (Gün 5-8)

* **Gün 5:** Minimal `SmartHomeEnergyEnv` iskeleti — sadece SOC + 24 saatlik fiyat gözlemi, tek boyutlu `battery_action`; batarya fizik modeli (şarj/deşarj verimliliği, SOC sınırları) `step()` içine eklenir.
* **Gün 6:** İlk ödül fonksiyonu (sadece maliyet), Gymnasium `check_env()` ile doğrulama, birim testlerinin yazılması.
* **Gün 7:** Stable-Baselines3 PPO ile ilk eğitim denemesi, TensorBoard entegrasyonu.
* **Gün 8:** Kalibrasyon checkpoint — ajan gece ucuzken şarj edip akşam pahalıyken deşarj etmeyi öğrenene kadar bu aşamadan çıkılmaz (mentorun vurguladığı en kritik nokta).

### 🟨 Faz 2 — Curriculum Aşama 2: Pasif Tüketim ve Güneş (Gün 9-12)

* **Gün 9:** Ortama sabit ev talebi (Load) ve güneş üretimi (PV) gözlemlerinin eklenmesi; `SolarProfileGenerator`/`DemandProfileGenerator` entegrasyonu.
* **Gün 10:** Ödül fonksiyonunun öz-tüketim önceliğini (önce ev ihtiyacı, sonra satış) yansıtacak şekilde güncellenmesi, yeniden eğitim.
* **Gün 11:** Faz 1 politikasıyla karşılaştırma (yeni karmaşıklığın eski arbitraj davranışını bozup bozmadığının kontrolü).
* **Gün 12:** Sezgisel baseline'ın (`rule_based.py`, "batarya yok" durumu dahil tek kod yolunda) bu genişletilmiş ortamda kodlanması.

### 🟧 Faz 3 — Curriculum Aşama 3: Ertelenebilir Cihazlar ve Tahmin Dayanıklılığı (Gün 13-16)

* **Gün 13:** Ayrık `deferrable_load_action` ve cihaz-çalıştı flag'inin ortama eklenmesi (hibrit sürekli+ayrık aksiyon uzayı), reward hacking'e karşı ceza teriminin kalibrasyonu.
* **Gün 14:** Yeniden eğitim + "cihaz çalıştırma oranı" metriğinin ayrıca izlenmesi (sadece maliyete güvenilmez).
* **Gün 15:** Uzun dönem EPİAŞ geçmiş verisiyle `price_forecast.py` modelinin (XGBoost/ARIMA) eğitilmesi ve tahmin doğruluğunun (MAPE) değerlendirilmesi.
* **Gün 16:** Eğitilmiş ajanın oracle/tahmin/naive fiyat modlarında test edilip `evaluation/compare.py` ile karşılaştırılması; genel ara değerlendirme.

### 🟪 Faz 4 — Dashboard ve Polish (Gün 17-18)

* **Gün 17:** Streamlit dashboard iskeleti, ana zaman serisi grafiği, curriculum aşamaları arası karşılaştırma paneli.
* **Gün 18:** Oracle/tahmin/naive karşılaştırma paneli, kod optimizasyonu, `requirements.txt` finalize.

### 🟥 Faz 5 — Test, Dokümantasyon ve Teslim (Gün 19-20)

* **Gün 19:** Uçtan uca test (sıfırdan kurulumla çalıştırma), `docs/experiments/results-log.md` doldurulması.
* **Gün 20:** README, sunum hazırlığı, hocalara son projenin ve GitHub reposunun teslimi.

---

## 16. Haftalık Sprint Özeti

| Hafta | Günler | Hedef | Çıktı |
| --- | --- | --- | --- |
| **1** | 1-5 | Kurulum, veri keşfi, Curriculum Aşama 1 başlangıcı | Hizalanmış veri seti + saf batarya arbitrajı öğrenen minimal ajan |
| **2** | 6-10 | Curriculum Aşama 1 tamamlanması, Aşama 2 başlangıcı | Arbitraj davranışı doğrulanmış + güneş/talep entegrasyonu |
| **3** | 11-15 | Curriculum Aşama 2 tamamlanması, Aşama 3 (cihaz+tahmin) | Öz-tüketim davranışı + ertelenebilir cihaz kararları |
| **4** | 16-20 | Tahmin dayanıklılığı, dashboard, teslim | Oracle/tahmin/naive karşılaştırması + tam çalışan dashboard |

---

## 17. Git Workflow & PR Süreci

* Asla doğrudan `main` dalına push yapılmaz.
* Her özellik için yeni branch (`feature/energy-env`, `feature/ppo-training`, `feature/dashboard`).
* PR açıklamasına ne yapıldığı yazılır, hoca reviewer olarak eklenir, onay sonrası `main`'e merge edilir.

**Commit Mesaj Standardı:**
* `feat(env): batarya fizik modeli eklendi`
* `fix(data): epias fiyat verisi eksik saat enterpolasyonu düzeltildi`
* `docs(experiments): ppo hiperparametre denemesi sonuçları eklendi`

---

## 18. GitHub Projects Board & Issue Yönetimi

* Repo'nun **Projects** sekmesindeki Kanban panosu aktif kullanılır.
* Yol haritasındaki her gün bir **Issue** olarak açılır.
* Sütunlar: **To Do** / **In Progress** / **Review** / **Done**.

---

## 19. Daily Standup

Her iş günü:
1. Dün ne yaptım?
2. Bugün hangi Task/Issue üzerinde çalışacağım?
3. Beni engelleyen bir durum var mı?

---

## 20. Risk Yönetimi

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| RL ajanı yakınsamıyor (convergence sorunu) | Orta | Yüksek | Curriculum yaklaşımı (bkz. bölüm 6): karmaşıklık aşamalı eklenir, her aşama bir öncekinden çıkmadan doğrulanır (Gün 8, 11, 14 checkpoint'leri). |
| Ajan ödül fonksiyonunu sömürüyor (reward hacking — ör. cihazı hiç çalıştırmama) | Orta | Yüksek | Curriculum Aşama 3'te sert ceza terimi + "cihaz çalıştırma oranı" metriğinin ayrıca izlenmesi (bkz. bölüm 9). |
| Veri kaynakları (EPİAŞ, PVWatts, UK-DALE) uyumsuz formatlarda | Orta | Orta | Gün 2-4 tamamen veri keşfine ayrılmış durumda; erişilemezse parametrik sentetik profile geçiş planı hazır. |
| Eğitim süresi beklenenden uzun sürüyor | Düşük | Orta | Küçük ölçekli ortam (tek ev, 24-168 saatlik bölümler) ile eğitim süresi zaten sınırlı tutuluyor. |
| Fiyat tahmin modeli düşük doğrulukta | Orta | Düşük | Model yeniden eğitim gerektirmiyor (sadece test aşamasında kullanılıyor); düşük doğruluk bile "tahmin hassasiyeti" analizinin bir parçası olarak raporlanabilir, proje başarısını tehlikeye atmaz. |
| 20 Güne sığamama | Orta | Orta | Karbon optimizasyonu ve multi-agent gibi ek hedefler kapsam dışı bırakıldı; curriculum fazları sıkı gün bütçesiyle planlandı. |

---

## 21. Definition of Done (Bitti Kriteri)

* [ ] Kod hatasız çalışıyor, `check_env()` testinden geçiyor.
* [ ] Birim testleri yazılmış ve geçiyor.
* [ ] Kod standartlara uygun yazılmış ve `feature` dalından push edilmiş.
* [ ] GitHub'da PR açılmış, onaylanmış ve `main`'e merge edilmiş.
* [ ] Kanban kartı *Done* sütununa taşınmış.

---

## 22. Teslim Edilecekler

1. **Kaynak Kod:** Temiz Python mimarisiyle, `main` branch üzerinde çalışan proje.
2. **Eğitilmiş Model:** `models/` altında checkpoint dosyası.
3. **Dashboard:** Çalışan Streamlit uygulaması.
4. **Dokümantasyon:** `docs/` klasöründeki deney kayıtları ve veri kaynağı notları.
5. **Git ve Kanban Geçmişi:** Günlük commitler, onaylanmış PR'lar ve dolu bir staj defteri kanıtı.
6. **Curriculum Karşılaştırma Raporu:** Üç aşamanın (arbitraj / öz-tüketim / cihaz+tahmin) birbirine göre performans farkını ve oracle/tahmin/naive tasarruf karşılaştırmasını özetleyen sonuç tablosu.
