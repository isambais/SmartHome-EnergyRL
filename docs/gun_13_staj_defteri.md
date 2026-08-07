# Staj Defteri — Gün 13

**Tarih:** 30 Temmuz 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 13 — Aşama 3: Değerlendirme ve Üç Aşama Karşılaştırması

### 1. Bugün Ne Yapıldı?

Faz 3'ün ilk değerlendirme günü. Dün Aşama 3 ortamıyla PPO, A2C, SAC ve TD3 eğitimlerini bitirdiğimiz için bugün `eval_policy.py`'ye Aşama 3 desteği ekleyip 90 günlük karşılaştırmalı değerlendirme çalıştırdım. Üç aşamanın (sadece batarya → güneş+talep → ertelenebilir cihaz) sonuçlarını aynı anda görmek ilginçti; karmaşıklık arttıkça hem ödüllerin hem de belirsizliğin nasıl değiştiği netleşti.

### 2. eval_policy.py — Aşama 3 Entegrasyonu

Yeni bir dosya açmak yerine mevcut `scripts/eval/eval_policy.py`'ye üç yardımcı fonksiyon eklendi, ardından `main()` içine Aşama 3 karşılaştırma bloğu yerleştirildi.

**Eklenen fonksiyonlar:**

```python
def make_phase3_env(price, solar, demand):
    return SmartHomeEnergyEnv(
        price_data=price, solar_data=solar, demand_data=demand,
        price_unit="tl_per_mwh",
        enable_deferrable=True,
        deferrable_load_power_kw=1.5,
        deferrable_load_hours=1.0,
        deferrable_window=(6, 22),
        deferrable_penalty_coef=2.0,
        max_activations_per_day=2,
        random_day=True,
    )

def evaluate_phase3(policy, prices, solar, demand, n_days=90, seed=42):
    # n_days episode döngüsü → mean/std/min/max döndürür

def make_phase3_rl_policy(algo_cls, model_path, stats_path, price, solar, demand):
    # VecNormalize istatistiklerini yükler, deterministik tahmin yapar
```

`make_phase3_rl_policy` generic tasarlandı: `PPO`, `A2C`, `SAC`, `TD3`'ün hepsi aynı fonksiyondan geçiyor, tek fark `algo_cls` argümanı. Böylece her algoritma için ayrı yükleyici yazmak gerekmedi.

### 3. Değerlendirme Sonuçları

`python scripts/eval/eval_policy.py --days 90` komutuyla üç aşama sıralı çalıştırıldı. Giriş verisi: `data/aligned_dataset.csv` (8784 saatlik EPİAŞ 2026 + PVWatts + UK-DALE).

#### Aşama 1 — Sadece Batarya

| Politika | Ort (TL) | Std | Min | Maks |
|----------|---------|-----|-----|------|
| Bekle (hold) | +0.00 | 0.00 | +0.00 | +0.00 |
| Rastgele | −25.27 | 16.41 | −60.78 | +18.91 |
| Eşik | −1.85 | 10.92 | −35.34 | +16.67 |
| **PPO** | **+8.02** | 4.64 | +1.40 | +21.58 |
| A2C | +2.21 | 6.25 | −15.70 | +7.86 |
| **SAC** | **+9.63** | 5.12 | +2.75 | +22.54 |
| TD3 | +4.71 | 1.96 | +0.30 | +7.86 |

#### Aşama 2 — Güneş + Talep

| Politika | Ort (TL) | Std | Min | Maks |
|----------|---------|-----|-----|------|
| Bekle (hold) | −4.67 | 12.27 | −31.28 | +23.34 |
| Rastgele | −25.79 | 18.73 | −73.41 | +11.78 |
| Eşik | −3.94 | 15.87 | −48.87 | +21.76 |
| Öz-tüketim | −7.50 | 16.93 | −54.29 | +19.41 |
| ToU (saat blok) | −18.15 | 11.94 | −47.00 | +4.26 |
| Tahmin kullanır | −7.35 | 14.61 | −45.09 | +21.76 |
| Tepe kesme | −12.47 | 12.80 | −44.34 | +8.95 |
| Şebeke bilinçli | −4.39 | 15.98 | −49.22 | +21.76 |
| PPO | +4.84 | 13.05 | −25.40 | +30.08 |
| A2C | −1.43 | 13.89 | −25.40 | +30.08 |
| **SAC** | **+10.09** | 13.71 | −19.76 | +37.25 |
| **TD3** | **+9.77** | 13.90 | −22.29 | +36.50 |

#### Aşama 3 — Batarya + Ertelenebilir Cihaz

| Politika | Ort (TL) | Std | Min | Maks |
|----------|---------|-----|-----|------|
| Bekle (hold) | −6.67 | 12.27 | −33.28 | +21.34 |
| Rastgele | −29.00 | 20.51 | −72.85 | +1.80 |
| Eşik | −8.42 | 17.09 | −56.30 | +18.52 |
| PPO | +3.05 | 13.46 | −27.40 | +28.15 |
| A2C | −3.26 | 13.91 | −28.46 | +28.08 |
| **SAC** | **+8.32** | 14.25 | −24.24 | +34.40 |
| **TD3** | **+7.80** | 14.75 | −25.99 | +34.12 |

### 4. Bulgular ve Yorum

**SAC, üç aşamada da en tutarlı algoritma.** Aşama 1'de +9.63, Aşama 2'de +10.09, Aşama 3'te +8.32 TL/gün ortalama sağladı. Off-policy yapısı ve entropi düzenlemesi, değişken gözlem uzaylarına iyi adapte oluyor.

**Aşama 3'te ödüller düştü ama yine de pozitif.** SAC −1.77 TL, TD3 ise Aşama 2'ye kıyasla −1.97 TL geriledi. Bu beklenen bir sonuç; ertelenebilir yük yeni bir karar boyutu ekliyor (ne zaman çalıştıracaksın?) ve deferrable_penalty_coef=2.0 TL cezası basit politikalar için kayıp üretiyor.

**Hold politikası Aşama 3'te artık sıfır değil.** Aşama 1'de hold = +0.00 (hiç aksiyon yok, kayıp yok), Aşama 3'te hold = −6.67. Fark tamamen `deferrable_penalty_coef`: cihaz hiç çalıştırılmadığında episode sonunda 2.0 TL kesildiği için "hiçbir şey yapma" stratejisi artık kötü.

**Rastgele politika Aşama 3'te çok kötü (−29 TL).** Hem batarya hem de ertelenebilir cihaz kararlarını rastgele verince enerji dengesi çok bozuluyor.

**A2C Aşama 3'te negatife döndü.** Aşama 2'de −1.43 TL zaten iyi değildi; Aşama 3'te −3.26'ya indi. PPO da +3.05 ile pozitif ama SAC/TD3'ten belirgin şekilde geride. On-policy algoritmaların bu karmaşıklıkta off-policy'e kıyasla daha zor optimize ettiği görülüyor.

**Std değerleri Aşama 3'te yüksek (~14 TL).** Aşama 1'de SAC std=5.12 iken Aşama 3'te 14.25. Bu tutarsızlık ertelenebilir cihazın zaman penceresine (06:00–22:00) ve günlük fiyat volatilitesine bağlı; mevsimsel etkiler de devreye giriyor.

### 5. Üç Aşama Karşılaştırması — RL Algoritmaları

| Algoritma | Aşama 1 (TL) | Aşama 2 (TL) | Aşama 3 (TL) | Genel Sıralama |
|-----------|-------------|-------------|-------------|----------------|
| SAC | +9.63 | +10.09 | +8.32 | 🥇 1. |
| TD3 | +4.71 | +9.77 | +7.80 | 🥈 2. |
| PPO | +8.02 | +4.84 | +3.05 | 🥉 3. |
| A2C | +2.21 | −1.43 | −3.26 | 4. |

SAC ve TD3'ün off-policy avantajı, birden fazla aksiyon boyutunda özellikle belirginleşiyor. PPO Aşama 1'de iyi performans gösterse de gözlem uzayı büyüdükçe (104 → 106 boyut) geride kalıyor. Optuna'nın PPO için bulduğu hiperparametreler eğitim çöküşüne yol açtığından Aşama 2 hiperparametrelerine geri dönüldüğü de bunda etkili olmuş olabilir.

### 6. Pull Request ve Git Commits (Gün 13)

**PR #30:** [feat: Phase 3 — hybrid action space, deferrable load & multi-algorithm evaluation](https://github.com/isambais/SmartHome-EnergyRL/pull/30)

```
5501d58  feat(eval): add Phase 3 evaluation support to eval_policy.py
```

### 7. Teknik Öğrenimler

**Generic policy loader tasarımı** kod tekrarını önledi. `algo_cls` argümanı sayesinde dört farklı SB3 algoritması tek bir fonksiyonla yüklenebildi. `VecNormalize.load()` stats dosyasının varlığını kontrol eden `Path(stats_path).exists()` koruması, model dosyaları eksik olduğunda temiz bir uyarı mesajı veriyor.

**Curriculum learning'in ödül üzerindeki etkisi** gözlemlendi. Her aşama bir öncekinin üzerine yeni bir karar boyutu ekliyor; bu da hem ortamın güçlük seviyesini artırıyor hem de eğitilmiş modellerin davranışını etkiliyor. Aşama 3'te SAC'ın hâlâ pozitif kalması, off-policy deneyim tamponunun hibrit aksiyon uzayında daha verimli öğrenmeyi desteklediğini gösteriyor.

**Yüksek standart sapma bir sorun mu?** Aşama 3'te std≈14 TL yüksek görünse de min değerleri bile (SAC: −24.24) Aşama 1 minimum'larına (SAC: +2.75) kıyasla daha kötü. Bu, ertelenebilir cihaz kararının yanlış zamanlanmasının maliyetini ve fırsatının ödülünü gösteriyor — ortam gerçekten daha zor.

---

## Yarın (Gün 14)

Aşama 3 eğitim scriptleri (`scripts/train/`) commit edilecek, ardından Faz 4'e geçişe hazırlık başlayacak. Olası bir sonraki adım: üç aşamanın sonuçlarını karşılaştıran bir görsel rapor hazırlamak.
