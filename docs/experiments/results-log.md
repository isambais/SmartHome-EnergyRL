# Deney Kayıt Defteri (Results Log)

**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi
**Son güncelleme:** 8 Ağustos 2026 (Gün 19)

Bu dosya, proje boyunca çalıştırılan tüm değerlendirme (eval) deneylerinin
sonuçlarını tek bir yerde toplar. Amaç: her sonucu **hangi komutla**, **hangi
veriyle** ve **hangi ortam parametreleriyle** üretildiğine dair izlenebilir
(reproducible) bir kayıt tutmak.

> **Kaynak ve doğruluk notu.** Aşağıdaki sayılar projenin daha önceki
> günlerde çalıştırılıp repoya işlenmiş **gerçek** eval çıktılarından
> derlenmiştir (kaynak her tablonun altında belirtilmiştir). Sıfırdan yeniden
> koşum (Gün 19 uçtan uca testi) için gerekli komutlar her bölümde verilmiştir.
> RL modelleri PyTorch + Stable-Baselines3 gerektirdiğinden, eğitim ve model
> yükleme adımları proje konvansiyonu gereği yerel makinede veya Colab'da
> (`notebooks/`) çalıştırılır.

---

## 1. Değerlendirme Ortamı

`SmartHomeEnergyEnv` — `src/env/energy_env.py`

| Parametre | Değer |
|---|---|
| Batarya kapasitesi | 10 kWh |
| Maks şarj/deşarj gücü | 5 kW |
| Şarj verimliliği | %88–98 (C-rate'e bağlı) |
| Öz-deşarj | %0.05 / saat |
| Min SoC rezervi | %10 |
| SoH aralığı | 0.70–1.00 (episode başında rastgele) |
| Satış (geri besleme) fiyatı | Alış × 0.60 |
| Şebeke kesinti olasılığı | %0.2 / saat |
| Episode uzunluğu | 24 saat |
| Aksiyon uzayı | sürekli [-1, +1] (-1=deşarj, 0=bekle, +1=şarj) |
| Gözlem boyutu | 56 (Faz 1) / 104 (Faz 2–3) |

Değerlendirme verisi:

| Veri | Dosya | Kapsam |
|---|---|---|
| Ham EPİAŞ PTF (birleşik) | `data/epias_combined.csv` | ~40.176 saat (2022–2026) |
| Hizalanmış fiyat + güneş + talep | `data/processed/aligned_dataset.csv` | 8.784 saat (1 yıl) |
| Faz 3 test seti | aligned_dataset son %20 | 74 gün |

---

## 2. Faz 1 — Saf Batarya Arbitrajı (gözlem = 56)

**Komut:** `python scripts/eval/eval_policy.py --days 30`

### 2a. 30 günlük net kazanç (birleşik EPİAŞ verisi)

| Model | 30 Günlük Net Kazanç (TL) |
|---|---|
| SAC | +8.98 |
| PPO | +7.67 |
| A2C | +3.19 |
| TD3 | *(o an eğitim sürüyordu — Faz 2/3'te tamamlandı)* |
| HoldPolicy (baseline) | 0.00 |

*Kaynak: `README.md` → Sonuçlar; `scripts/eval/eval_policy.py`.*

### 2b. İlk PPO eğitimi — tek gün fallback veri (günlük ortalama kazanç)

| Politika | Ort. Günlük Kazanç |
|---|---|
| Eşik (threshold) | +31.52 TL |
| PPO (eğitilmiş, 50k adım) | +15.32 TL |
| Bekle (hold) | 0.00 TL |
| Rastgele | −6.49 TL |

Not: Eşik politikası tek günlük fallback veriyi "ezberliyor" (std=0.00). PPO
genelleme yaptığı için tek günde eşiği geçemiyor; gerçek 8.784 saatlik veriyle
eğitildiğinde tablo tersine dönüyor (bkz. Faz 3).

*Kaynak: `docs/training-notes.md`. Eğitim: PPO, 50.000 adım, 4 paralel ortam,
lr=3e-4, batch=64, ~1.5 dk (CPU).*

---

## 3. Faz 2 — Kural Tabanlı Baseline (Optuna Öncesi/Sonrası)

**Komut:** `python scripts/hpo/rule_based_optuna.py` (50 deneme/politika) →
`python scripts/eval/eval_policy.py --days 30`

| Politika | Varsayılan | Optuna Sonrası |
|---|---|---|
| ThresholdPolicy | −2.57 TL | **+2.53 TL** |
| ForecastAwarePolicy | — | +1.66 TL |
| GridAwarePolicy | — | +1.35 TL |
| SelfConsumptionPolicy | — | *(negatif)* |

Optuna, eşik politikasını negatiften pozitife çevirdi (Δ ≈ +5.1 TL). En büyük
kazanım hiperparametre araması olan (P30/P70 eşiklerinin veriye göre ayarlanması)
ThresholdPolicy'de.

*Kaynak: `README.md` → Sonuçlar; `logs/rule_based_optuna.db`.*

---

## 4. Faz 3 — Tahmin Belirsizliğine Robustluk (74 günlük test seti)

**Komut:** `python scripts/forecast/compare.py`
**Çıktı:** `logs/forecast_comparison.csv`, `docs/forecast_comparison.png`

Aynı eğitilmiş ajanlar dört farklı fiyat-bilgisi modunda değerlendirildi
(yeniden eğitim yok). Değerler günlük ortalama net kazanç (TL/gün):

| Ajan | Oracle | Forecast | Ensemble | Naive | Δ Forecast | Δ Ensemble | Δ Naive |
|---|---|---|---|---|---|---|---|
| **SAC** | +14.38 | +14.49 | +14.49 | +14.18 | +0.11 | +0.11 | −0.20 |
| **TD3** | +14.72 | +14.70 | +14.64 | +14.54 | −0.02 | −0.08 | −0.18 |
| **PPO** | +12.08 | +11.98 | +11.97 | +11.94 | −0.10 | −0.11 | −0.14 |
| A2C | −9.01 | −9.50 | −9.53 | −8.79 | −0.49 | −0.52 | +0.22 |
| FcAware (kural) | −3.34 | −2.30 | −2.15 | +5.73 | +1.04 | +1.19 | +9.07 |

**Bulgu:** SAC ve TD3 tüm modlarda ±0.2 TL içinde kalıyor → RL ajanları tahmin
kalitesine bağımlı değil, yani belirsizliğe karşı **robust**. Kural tabanlı
FcAware ise modlar arasında 9 TL'den fazla oynuyor (Naive'de en iyi, ML
tahmininde negatif) — kural mantığı fiyat dağılımına aşırı duyarlı.

### 4a. Cihaz çalıştırma oranı (reward-hacking kontrolü)

Maksimum oran = `max_activations_per_day=2 / 24 = 0.083`.

| Ajan | Oracle | Forecast | Ensemble | Naive |
|---|---|---|---|---|
| SAC | 0.053 | 0.054 | 0.054 | 0.049 |
| TD3 | 0.068 | 0.065 | 0.066 | 0.067 |
| PPO | 0.083 | 0.083 | 0.083 | 0.083 |
| A2C | 0.069 | 0.069 | 0.069 | 0.068 |
| FcAware | 0.083 | 0.083 | 0.083 | 0.083 |

PPO cihazı her modda tam kapasitede (0.083) çalıştırıyor — net değere
bakmaksızın. SAC (0.053) ve TD3 (0.068) üst sınırın altında, seçici karar
veriyor → daha nitelikli öğrenme.

*Kaynak: `docs/gun_15_staj_defteri.md`; `logs/forecast_comparison.csv`.*

---

## 5. Fiyat Tahmin Modelleri (sMAPE)

`scripts/forecast/price_forecast.py` — ertesi gün 24 saatlik PTF tahmini.

| Model | sMAPE | Not |
|---|---|---|
| LightGBM + Optuna | %29.93 | Forecast modunda kullanıldı |
| Ensemble (LGB+XGB+RF, ters-sMAPE ağırlıklı) | %32.10 | Ensemble modunda kullanıldı |
| Naive (bir önceki günün aynı saatleri) | — | Referans baseline |

*Kaynak: `docs/gun_15_staj_defteri.md`; `docs/forecast_comparison.png`.*

---

## 6. Test Paketi (pytest)

`conftest.py` `sys.path` düzeltmesiyle proje kökünden koşulur.

**Komut:** `pytest -q`

| Test dosyası | Kapsam | Torch gerekir mi? |
|---|---|---|
| `tests/test_energy_env.py` | Ortam fiziği, aksiyon/gözlem uzayı | Hayır |
| `tests/test_rule_based.py` | 7 baseline politika | Hayır |
| `tests/test_solar_profile.py` | Güneş üretim profili üretici | Hayır |
| `tests/test_demand_profile.py` | Ev tüketim profili üretici | Hayır |
| `tests/test_epias_loader.py` | EPİAŞ fiyat yükleyici | Hayır |
| `tests/test_build_dataset.py` | Veri hizalama / dataset kurulumu | Hayır |
| `tests/test_train_ppo.py` | PPO eğitim akışı (kısa) | Evet (SB3) |

Toplam: 7 dosya, ~24 birim testi. README rozeti: *pytest passing*. Torch
gerektirmeyen 6 dosya bağımlılık olmadan koşturulabilir; `test_train_ppo.py`
Stable-Baselines3 (PyTorch) gerektirir.

---

## 7. Yeniden Üretim (Reproduce) — Sıfırdan Kurulum

```bash
git clone https://github.com/isambais/SmartHome-EnergyRL.git
cd SmartHome-EnergyRL
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # torch + SB3 dahil

# Testler
pytest -q

# Faz 1 + Faz 2 + Faz 3 karşılaştırması (30 gün)
python scripts/eval/eval_policy.py --days 30

# Tahmin belirsizliği robustluk karşılaştırması (74 günlük test seti)
python scripts/forecast/compare.py
```

> **Ortam notu (Gün 19 uçtan uca testi).** Bağımlılık kurulumu iki parçada
> denendi: hafif paketler (numpy, pandas, gymnasium, statsmodels, pytest, plotly)
> sorunsuz kuruldu; ancak PyTorch'un PyPI üzerindeki CUDA'lı tekerleği (torch
> wheel'i tek başına ~527 MB + gigabaytlarca `nvidia-*` bağımlılığı) ve
> `download.pytorch.org` CPU indeksinin ağ allowlist'i tarafından engellenmesi
> nedeniyle bu kısıtlı ortamda torch kurulumu tamamlanamadı. Bu yüzden RL model
> yükleme gerektiren eval'lar bu ortamda yeniden koşulmadı; yukarıdaki sayılar
> projenin daha önce yerel makinede/Colab'da üretip repoya işlediği gerçek
> çıktılardır. Torch'lu tam eval, yeterli disk/GPU olan bir ortamda yukarıdaki
> komutlarla bire bir tekrar üretilebilir.

---

## 8. Özet Çıkarımlar

- **En iyi ajanlar:** TD3 ve SAC (74 günlük test setinde +14–15 TL/gün, tahmin
  belirsizliğine robust).
- **PPO** kararlı ama ~2 TL/gün geride; cihazı seçici kullanmıyor.
- **A2C** bu problemde negatif — off-policy (SAC/TD3) yöntemler bu sürekli
  kontrol probleminde on-policy'den (PPO/A2C) belirgin şekilde üstün.
- **Kural tabanlı baseline'lar** Optuna ile pozitife çekilebiliyor ama RL'in
  robustluğuna ulaşamıyor.
- **RL'in katma değeri:** gözlemden bağımsız, tahmin kalitesine dayanmayan
  strateji öğrenmesi — kural tabanlı politikaların en zayıf yanı olan dağılım
  duyarlılığını ortadan kaldırıyor.
