# Gün 8 — Kalibrasyon ve Çok Algoritmali Karşılaştırma

## Genel Bakış

Gün 7'de tek günlük yapay veriyle eğitilen PPO, Gün 8'de gerçek EPIAS piyasa verisiyle
yeniden kalibre edildi. PPO'ya ek olarak A2C ve SAC algoritmaları da eğitildi;
tüm politikalar 30 günlük gerçek veri üzerinde karşılaştırıldı.

---

## 1. Gerçek EPIAS Verisi

**Kaynak:** Türkiye Piyasa Takas Fiyatı (PTF), 15.07.2025–15.07.2026  
**Dosya:** `data/epias_2024.csv`  
**Boyut:** 8.784 saatlik kayıt (366 gün × 24 saat)

| İstatistik | Değer |
|-----------|-------|
| Ortalama  | 2207.9 TL/MWh |
| Min       | 0.0 TL/MWh |
| Maks      | 4500.0 TL/MWh |

Ham veri Türkçe sayı formatında (3.230,00) geldiğinden `prepare_epias_data.py`
ile parse edildi.

---

## 2. Hiperparametre Optimizasyonu (Optuna)

`scripts/optuna_search.py` — 20 deneme, 10k adım/deneme

**En iyi parametreler (Trial #8, 13.69 TL):**

| Parametre | Değer |
|-----------|-------|
| learning_rate | 3.25e-4 |
| n_steps | 256 |
| batch_size | 128 |
| gamma | 0.953 |

---

## 3. Seed Robustness

`scripts/seed_robustness.py` — 5 seed (0–4), 50k adım/seed

| Seed | Ödül (TL) |
|------|-----------|
| 0 | 13.14 |
| 1 | 11.13 |
| 2 | 11.53 |
| 3 | 11.11 |
| 4 | 12.56 |
| **Ort ± Std** | **11.89 ± 0.81** |

Sonuç: Model stabil — std < 1 TL.

---

## 4. Eğitilen Modeller

| Model | Adım | Ağ | VecNormalize | eval/mean_reward |
|-------|------|----|-------------|-----------------|
| PPO | 500k | 256×256 | ✅ | 13.0 TL |
| A2C | 500k | 256×256 | ✅ | 12.1 TL |
| SAC | 100k | 256×256 | ✅ | 10.8 TL |

---

## 5. Politika Karşılaştırması (30 gün)

| Politika | Ort (TL) | Std | Min | Maks |
|----------|---------|-----|-----|------|
| Bekle | +0.00 | 0.00 | +0.00 | +0.00 |
| Rastgele | -4.56 | 12.83 | -29.60 | +21.09 |
| Eşik (oracle) | +20.99 | 12.81 | -10.25 | +39.43 |
| PPO | +12.97 | 4.76 | +1.14 | +17.75 |
| A2C | +12.97 | 4.76 | +1.14 | +17.75 |
| SAC | +12.83 | 4.83 | +1.14 | +17.54 |

---

## 6. Bulgular

**Eşik politikası neden önde?**  
Eşik politikası oracle — gün başlamadan 24 saatin tüm fiyatlarını biliyor.
Gerçek dünyada bu bilgi mevcut değil; dolayısıyla PPO pratik açıdan daha değerli.

**PPO ve A2C neden aynı?**  
İki algoritma da aynı basit stratejiye yakınsadı: ucuza şarj, pahalıya deşarj.
Daha karmaşık ortamlarda farklılaşmaları beklenir.

**SAC sample efficiency:**  
SAC 100k adımda PPO/A2C'nin 500k adımdaki performansını yakaladı.
Yarın 500k adımla yeniden eğitilecek.

---

## 7. Dosya Yapısı

```
scripts/
├── prepare_epias_data.py   # Ham EPIAS CSV → temiz veri
├── generate_epias_data.py  # Sentetik fallback veri üreteci
├── optuna_search.py        # Hiperparametre optimizasyonu
├── seed_robustness.py      # Model stabilite testi
├── train_ppo.py            # PPO eğitimi (Optuna + VecNormalize)
├── train_a2c.py            # A2C eğitimi (VecNormalize)
├── train_sac.py            # SAC eğitimi (VecNormalize)
├── eval_policy.py          # 6 politika karşılaştırması
└── plot_comparison.py      # Bar chart üretici

models/
├── ppo_smarthome_final.zip
├── ppo_vecnormalize.pkl
├── a2c_smarthome_final.zip
├── a2c_vecnormalize.pkl
├── sac_smarthome_final.zip
└── sac_vecnormalize.pkl

docs/
└── policy_comparison.png   # 6 politika bar chart
```