# Staj Defteri — Gün 15

**Tarih:** 4 Ağustos 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 15 — Oracle / Forecast / Ensemble / Naive Fiyat Modu Karşılaştırması

### 1. Bugün Ne Yapıldı?

Gün 14'te eğitilen RL ajanlarını (SAC, TD3, PPO, A2C) ve kural tabanlı politikaları dört farklı fiyat bilgisi modunda karşılaştıran `scripts/forecast/compare.py` scripti yazıldı, hataları düzeltildi ve iki iterasyonla iyileştirildi. Sonuçlar `logs/forecast_comparison.csv` ve `docs/forecast_comparison.png` olarak dışa aktarıldı. Bu karşılaştırma, Implementation Plan'ın Faz 3 kapsamındaki son teknik adımı tamamladı: *"ajanın tahmin belirsizliğine dayanıklılığını göstermek."*

---

### 2. Tasarım — ForecastEnv Subclass Yaklaşımı

`energy_env.py`'yi değiştirmeden forecast fiyatlarını ortama enjekte etmek için `SmartHomeEnergyEnv`'den türeyen `ForecastEnv` alt sınıfı yazıldı. `reset()` metodu override edilerek `_tomorrow_prices_obs` bloğu ML tahmin dizisiyle değiştiriliyor; ödül hesaplaması (`step()`) dokunulmadan kalıyor.

```
ForecastEnv(forecast_prices_daily=None)   → Oracle modu
ForecastEnv(forecast_prices_daily=array)  → Forecast / Ensemble / Naive modu
```

Bu yaklaşımın avantajı: aynı eğitilmiş model ağırlıkları yeniden eğitim gerektirmeden dört modda da değerlendirilebiliyor. Ortamın geri kalanı (batarya fiziği, ödül, cihaz mantığı) tamamen korunuyor.

**Dört mod:**

| Mod | Kaynak | `forecast_noise_std` |
|---|---|---|
| Oracle | Gerçek ertesi gün fiyatı | 0.05 (eğitim dağılımı korunur) |
| Forecast | LightGBM+Optuna (%29.93 sMAPE) | 0.00 |
| Ensemble | LGB+XGB+RF ağırlıklı ort. (%32.10 sMAPE) | 0.00 |
| Naive | Bir önceki günün aynı saatleri | 0.00 |

---

### 3. Düzeltilen Hatalar ve İyileştirmeler

**Hata 1 — `load_and_engineer()` TypeError:**  
İlk yazımda fonksiyon hem `Path` hem `DataFrame` kabul edecek şekilde karışık yazılmıştı; `pd.read_csv(DataFrame)` çağrısı `TypeError` verdi. Düzeltme: `engineer_features(df: DataFrame)` ve `load_and_engineer(path: Path)` olarak iki ayrı fonksiyona bölündü.

**Hata 2 — Hardcoded test tarihi:**  
`TEST_START = pd.Timestamp("2025-09-01")` sabit tarih kullanılıyordu; `price_forecast.py` ile tutarsız. Düzeltme: `TRAIN_RATIO = 0.80` ve `get_test_mask()` ile oran tabanlı bölme.

**Hata 3 — Sadece LightGBM+Optuna:**  
Karşılaştırmaya yalnızca tek model alınmıştı. Gün 14'te eğitilen XGBoost ve Random Forest modelleri de eklenerek `build_ensemble_prices()` ve Ensemble modu tamamlandı.

**v2 İyileştirmeleri:**

1. **`forecast_noise_std=0.05` Oracle için** — Ajan `forecast_noise_std=0.05` ile eğitilmişti; Oracle modunda `0.0` kullanmak ajanı dağılım dışına çıkarıyordu. `make_env()` `noise_std` parametresi alacak şekilde yeniden düzenlendi.
2. **Sadece test seti** — aligned_dataset'in son %20'si = 74 gün. `split_test()` fonksiyonu ile p_test, solar_test, demand_test ve ML tahminleri hepsi bu aralığa kırpıldı.
3. **`device_activation_rate` tablosu** — Reward hacking kontrolü için `info["episode"]["device_activation_rate"]` değerleri ayrı pivot tablo olarak yazdırıldı.
4. **Grafik temizleme** — Tüm modlarda Δ=0.00 veren Bekle/Eşik/Öz-tük./Şb.Bil. grafikten çıkarıldı; yalnızca SAC/TD3/PPO/A2C/FcAware gösteriliyor. (Bu politikalar `_tomorrow_prices_obs` gözlem özelliğini kullanmıyor.)

---

### 4. Karşılaştırma Sonuçları — 74 Gün (Test Seti)

```
Mod       Oracle  Forecast  Ensemble   Naive  Δ Forecast  Δ Ensemble  Δ Naive
─────────────────────────────────────────────────────────────────────────────
SAC       +14.38    +14.49    +14.49  +14.18       +0.11       +0.11    -0.20
TD3       +14.72    +14.70    +14.64  +14.54       -0.02       -0.08    -0.18
PPO       +12.08    +11.98    +11.97  +11.94       -0.10       -0.11    -0.14
A2C        -9.01     -9.50     -9.53   -8.79       -0.49       -0.52    +0.22
FcAware    -3.34     -2.30     -2.15   +5.73       +1.04       +1.19    +9.07
```

SAC ve TD3 tüm modlarda ±0.2 TL içinde kalıyor. Bu, RL ajanlarının tahmin kalitesine bağımlı olmadığını — yani tahmin belirsizliğine karşı **robust** eğitildiğini — gösteriyor.

---

### 5. Cihaz Çalıştırma Oranı (Reward Hacking Kontrolü)

```
Mod       Oracle  Forecast  Ensemble  Naive
─────────────────────────────────────────
SAC        0.053     0.054     0.054  0.049
TD3        0.068     0.065     0.066  0.067
PPO        0.083     0.083     0.083  0.083
A2C        0.069     0.069     0.069  0.068
FcAware    0.083     0.083     0.083  0.083
```

Maksimum oran: `max_activations_per_day=2 / 24 saat = 0.083`.

PPO her modda tam kapasitede çalışıyor (0.083) — cihazın net değerine bakmaksızın her gün 2 kez aktive ediyor. SAC (0.053) ve TD3 (0.068) ise üst sınırın altında kalıyor; fiyata ve güneş durumuna göre **seçici** karar veriyorlar. Bu, SAC/TD3'ün PPO'ya göre daha nitelikli öğrendiğinin somut kanıtı.

---

### 6. Önemli Bulgu — FcAware Anomalisi

ForecastAwarePolicy Naive modda +5.73 TL/gün (en iyi), Oracle/Forecast/Ensemble modlarında ise negatif. Bu kural tabanlı politikanın eşik mantığının dünkü fiyat kalıbıyla uyumlu olduğunu, ML tahminlerinin ise farklı bir dağılım sunarak kural mantığını "şaşırttığını" gösteriyor. RL ajanları bu davranışı sergilemiyor çünkü gözlemden bağımsız bir strateji öğrenmişler.

---

### 7. Git Commits (Gün 15)

```
PR #32: https://github.com/isambais/SmartHome-EnergyRL/pull/32
[hash]  feat(forecast): add compare.py — Oracle/Forecast/Ensemble/Naive comparison
[hash]  fix(forecast): split engineer_features / load_and_engineer, ratio-based test split
[hash]  feat(forecast): add Ensemble mode (LGB+XGB+RF weighted by inverse sMAPE)
[hash]  fix(forecast): oracle noise_std=0.05, test-set-only eval, activation_rate table
[hash]  docs: add forecast_comparison.png, forecast_comparison.csv
[hash]  docs: add Gün 15 staj defteri
```

---

### 8. Teknik Öğrenimler

**Subclass ile backward-compatible genişletme:** `energy_env.py`'yi değiştirmek yerine `ForecastEnv` subclass yazmak hem mevcut Phase 1/2 testlerini bozmuyor hem de yeni özelliği temiz bir soyutlama katmanında tutuyor. Bu, open/closed prensibinin (açık/kapalı) pratik bir uygulaması.

**`forecast_noise_std` tutarlılığı:** Değerlendirmede eğitim dağılımından sapan bir gürültü seviyesi kullanmak out-of-distribution (OOD) değerlendirmeye yol açar. Oracle modunda `0.0` yerine `0.05` kullanmak sonuçları daha güvenilir kıldı.

**Reward hacking — `act_rate` metriğinin önemi:** Ödül değeri tek başına yeterli değil. PPO, SAC ile benzer ödül aralığında olduğu hâlde cihazı her seferinde maksimum çalıştırıyor. `device_activation_rate` olmadan bu fark görünmezdi.

**Veri hizalaması:** `p_full` (40k saat, 2022) + `solar/demand` (aligned_dataset, 2025) karıştırıldığında env `min(days)` alıyor ama fiyatlar 2022'den geliyor, solar/demand 2025'ten — tamamen yanlış hizalama. Doğru yaklaşım: tüm veriyi `aligned_dataset.csv`'den almak (Phase 3 `eval_policy.py` ile tutarlı).

---

### Yarın (Gün 16)

Streamlit dashboard başlangıcı (`dashboard/app.py`) — Faz 4. Saatlik karar zaman serisi grafiği, RL ajanı vs baseline maliyet karşılaştırma paneli ve oracle/forecast/naive sekmesi.
