# Staj Defteri — Gün 14

**Tarih:** 31 Temmuz 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 14 — 500k Adım Eğitim Sonuçları, EPİAŞ Veri Genişletme ve Fiyat Tahmin İyileştirmeleri

### 1. Bugün Ne Yapıldı?

Dün başlatılan SAC (Google Colab, GPU) ve TD3 (lokal, GPU) eğitimleri tamamlandı. `eval_best_vs_final.py` ile dört algoritmanın best/final model karşılaştırması yapıldı; ardından kesin model seçimleri netleştirildi ve 90 günlük tam değerlendirme çalıştırıldı. Paralelde EPİAŞ fiyat verisi 2022–2026 dönemini kapsayacak şekilde genişletildi ve fiyat tahmin modülündeki bir bellek hatası giderildi.

---

### 2. SAC ve TD3 — 500k Adım Eğitim Sonuçları

#### SAC (Google Colab, T4 GPU, ~2.5 saat)

```
ep_rew_mean     : 8.1   (rollout, normalize edilmiş)
eval/mean_reward: 11.7  (EvalCallback)
actor_loss      : -0.364 → -0.424  (negatifleşiyor — iyi)
critic_loss     : 0.00356 → 0.00403  (çok düşük, stabil)
```

SAC'ın entropi düzenlemesi Phase 3'ün hibrit aksiyon uzayında tutarlı öğrenme sağladı. Critic kaybının düşük kalması Q-fonksiyonunun yakınsadığını gösteriyor.

#### TD3 (Lokal, NVIDIA GPU)

```
Model kaydedildi: models/td3_phase3_final.zip
```

TD3, 300k → 500k adım artışıyla Phase 3'te en belirgin iyileşmeyi gösterdi (+0.96 TL/gün).

---

### 3. Best vs Final Model Karşılaştırması

`python scripts/eval/eval_best_vs_final.py` — 90 gün, seed=42:

| Algoritma | Final (TL/gün) | Best (TL/gün) | Kazanan |
|-----------|---------------|---------------|---------|
| PPO | **+3.75** | +3.43 | final |
| A2C | -3.44 | **-3.16** | best |
| TD3 | **+8.76** | +8.18 | final |
| SAC | **+8.94** | +8.30 | final |

PPO, TD3 ve SAC için final modeller best checkpoint'leri geride bıraktı. A2C'de ise best model (-3.16 TL) final'den (+0.28 TL) daha iyi — EvalCallback erken duran bir noktayı yakalamış. `eval_policy.py`'de A2C için `a2c_phase3_best/best_model.zip` kullanılıyor.

**Gözlem:** Off-policy algoritmaların (SAC, TD3) final modelleri, on-policy algoritmalara (PPO, A2C) kıyasla daha güvenilir şekilde eğitimin sonuna doğru iyileşiyor. Bu, deneyim tamponunun son adımlara kadar verimli öğrenmeyi sürdürmesiyle açıklanabilir.

---

### 4. 90 Günlük Tam Değerlendirme Sonuçları

`python scripts/eval/eval_policy.py --days 90`

#### Aşama 1 — Sadece Batarya

| Politika | Ort (TL) | Std |
|----------|---------|-----|
| Bekle (hold) | +0.00 | 0.00 |
| Rastgele | -25.34 | 13.10 |
| Eşik | -3.24 | 11.16 |
| PPO | +4.87 | 6.36 |
| A2C | -3.90 | 8.35 |
| **SAC** | **+6.95** | 4.69 |
| TD3 | +4.22 | 1.63 |

> Not: Aşama 1 değerlendirme verisi bu günden itibaren `epias_combined.csv` (2022–2026, 40.176 saat) kullanıyor. Phase 1 modelleri 2024 verisine göre eğitildiğinden 2022–2023 fiyat dağılımına (kriz dönemi, 0–4800 TL/MWh) genellemeleri sınırlı; bu nedenle Gün 13 sonuçlarına göre hafif gerileme görülüyor.

#### Aşama 2 — Güneş + Talep (değişmedi)

| Politika | Ort (TL) | Std |
|----------|---------|-----|
| Bekle | -4.67 | 12.27 |
| Eşik | -3.94 | 15.87 |
| Şebeke bilinçli | -4.39 | 15.98 |
| PPO | +4.84 | 13.05 |
| A2C | -1.43 | 13.89 |
| **SAC** | **+10.09** | 13.71 |
| **TD3** | **+9.77** | 13.90 |

#### Aşama 3 — Batarya + Ertelenebilir Cihaz (iyileşti)

| Politika | Ort (TL) | Std | Min | Maks |
|----------|---------|-----|-----|------|
| Bekle (hold) | -6.67 | 12.27 | -33.28 | +21.34 |
| Rastgele | -31.53 | 19.79 | -84.35 | +2.15 |
| Eşik | -8.42 | 17.09 | -56.30 | +18.52 |
| Öz-tüketim | -12.79 | 17.80 | -64.19 | +11.75 |
| ToU (saat blok) | -24.15 | 13.78 | -57.20 | -1.18 |
| Tahmin kullanır | -11.14 | 14.76 | -52.04 | +18.52 |
| Tepe kesme | -18.81 | 14.48 | -54.43 | +2.08 |
| Şebeke bilinçli | -8.84 | 17.23 | -56.30 | +18.52 |
| PPO | +3.75 | 13.33 | -27.40 | +28.08 |
| A2C | -3.16 | 13.97 | -28.46 | +28.08 |
| **SAC** | **+8.94** | 13.55 | -21.38 | +35.07 |
| **TD3** | **+8.76** | 14.05 | -23.91 | +34.57 |

#### Üç Aşama — RL Karşılaştırması (Gün 13 vs Gün 14)

| Algoritma | Aş. 3 — Gün 13 | Aş. 3 — Gün 14 | Fark |
|-----------|----------------|----------------|------|
| PPO | +3.05 | **+3.75** | +0.70 |
| A2C | -3.26 | **-3.16** | +0.10 |
| SAC | +8.32 | **+8.94** | +0.62 |
| TD3 | +7.80 | **+8.76** | +0.96 |

500k adım eğitim dört algoritmada da iyileştirme sağladı. TD3 en büyük kazanımı elde etti (+0.96 TL/gün). Tüm değişimler beklenen yönde.

---

### 5. EPİAŞ Veri Genişletme

Bugüne kadar kullanılan fiyat tahmini verisi yalnızca `aligned_dataset.csv` içindeki 8.784 saati (Temmuz 2025 – Temmuz 2026) kapsıyordu. EPİAŞ şeffaflık platformundan 2022, 2023, 2024, 2025 ve 2026 yıllarına ait saatlik PTF verileri indirilip işlendi.

```
epias_2022.csv : 8.760 saat | 01.01.2022 – 31.12.2022 | 0 – 4.800 TL/MWh
epias_2023.csv : 8.760 saat | 01.01.2023 – 31.12.2023 | 0 – 4.200 TL/MWh
epias_2024.csv : 8.784 saat | 01.01.2024 – 31.12.2024 | 0 – 3.000 TL/MWh
epias_2025.csv : 8.760 saat | 01.01.2025 – 31.12.2025 | 0 – 3.400 TL/MWh
epias_2026.csv : 5.112 saat | 01.01.2026 – 01.08.2026 | 0 – 4.500 TL/MWh
───────────────────────────────────────────────────────────────
Toplam (tekrarsız): 40.176 saat | 2022-01-01 → 2026-08-01
```

**`scripts/data/merge_epias.py`** ile ham dosyalar birleştirildi; çakışan zaman damgaları `drop_duplicates()` ile temizlendi. `data/epias_combined.csv` oluşturuldu.

Ham EPİAŞ formatı: noktalı virgül ayraç, nokta binde ayraç, virgül ondalık ayraç. Örnek: `01.01.2022;00:00;949,98` → 949.98 TL/MWh.

**Fiyat tahmini için etki:** `scripts/forecast/price_forecast.py` artık 4.6 kat daha fazla eğitim verisiyle çalışıyor. 2022 enerji krizi (4800 TL/MWh'e kadar ulaşan fiyatlar), 2023 enflasyon dönemi, 2024 fiyat düşüşü ve 2025 toparlanması modellere farklı piyasa rejimlerini öğretiyor.

Train/test bölümü: 2022-01-01 – 2025-09-01 (eğitim) / 2025-09-01 – 2026-08-01 (test).

---

### 6. LSTM OOM Hatası Giderimi

`price_forecast.py` 40.176 saatlik veriyle çalıştırıldığında BiLSTM modelinde CUDA bellek hatası aldı:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 19.00 GiB.
GPU 0 has a total capacity of 6.00 GiB
```

**Kök neden:** Test setindeki tüm 8.035 sekans (`X_te` shape: 8035 × 168 × 1) tek seferde GPU'ya gönderiliyordu. BiLSTM'in ara tensörleri (8035 × 168 × 256) yaklaşık 19 GB yer tutuyordu.

**Çözüm:** Inference döngüsü 512'lik batch'lere bölündü:

```python
infer_bs = 512
preds_list = []
with torch.no_grad():
    for i in range(0, len(X_te), infer_bs):
        chunk = X_te[i : i + infer_bs].to(device)
        preds_list.append(model(chunk).cpu().numpy())
preds_norm = np.concatenate(preds_list).flatten()
```

Bu değişiklikle maksimum GPU kullanımı 512 × 168 × 256 × 4 byte ≈ 90 MB düzeyine indi.

---

### 7. Git Commits (Gün 14)

```
ebda776  fix(eval): add SAC best to eval_best_vs_final, DATA_PATH → epias_combined, LSTM batch inference
c0e3355  feat(forecast): add 4.5-year EPİAŞ dataset + merge script
```

---

### 8. Teknik Öğrenimler

**Off-policy vs on-policy — eğitim adımı etkisi:** TD3 ve SAC'ın 500k adımla elde ettiği kazanım (+0.62 – +0.96 TL/gün), PPO ve A2C'ye kıyasla daha yüksek. Deneyim tamponu tekrar örnekleme sayesinde off-policy algoritmalar her adımdan daha fazla öğreniyor; on-policy algoritmalar ise toplanan veriyi yalnızca bir kez kullanıp atıyor.

**Veri dağılımı kayması (data shift) — değerlendirme tutarlılığı:** Phase 1 değerlendirme sonuçlarının hafif düşmesi, modelin eğitildiği dağılımdan farklı fiyat verisiyle test edilmesinden kaynaklandı. Gerçek dünya dağıtımında bu "distribution shift" kritik bir sorun; modelin çeşitli piyasa rejimlerine karşı test edilmesi sağlamlık açısından değerlidir.

**Bellek yönetimi — batchli inference:** Derin öğrenme modellerinde eğitim batchli yapılırken inference tek seferde yapılması hatası sıkça görülür. Büyük test setlerinde GPU belleği aşımını önlemek için inference da batchlenmeli; `torch.no_grad()` ile gradyan tampon belleği de serbest bırakılmalı.

**Tekrar üretilebilirlik:** Ham veri işleme adımları `scripts/data/merge_epias.py`'ye taşındı. Böylece yeni yıl verisi ekleneceğinde yalnızca CSV indirilip aynı script çalıştırılacak.

---

## Yarın (Gün 15)

Fiyat tahmin modülünün 40.176 saatlik veriyle yeniden çalıştırılması (tüm 9 model + Ensemble) ve sonuçların karşılaştırılması. Ardından Gün 16 planı: LightGBM Optuna tahminini RL ajanına entegre etmek — Oracle / Forecast / Naive karşılaştırması (`scripts/forecast/compare.py`).
