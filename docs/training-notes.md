# İlk PPO Eğitimi — Gözlemler ve Notlar

## Eğitim Özeti

| Parametre | Değer |
|-----------|-------|
| Algoritma | PPO (Proximal Policy Optimization) |
| Toplam adım | 50.000 |
| Paralel ortam | 4 |
| Learning rate | 3e-4 |
| Batch size | 64 |
| Süre | ~1.5 dakika (CPU) |

## Sonuçlar

| Politika | Ort. Günlük Kazanç |
|----------|--------------------|
| Bekle | 0.00 TL |
| Rastgele | -6.49 TL |
| Eşik (threshold) | +31.52 TL |
| PPO (eğitilmiş) | +15.32 TL |

## TensorBoard Grafik Yorumu

**`rollout/ep_rew_mean`** — en kritik grafik:
- 0-10k adım: negatif ödül (-7.5 TL), ajan henüz rastgele davranıyor
- 10k-30k adım: hızlı öğrenme, ödül +13 TL'ye çıkıyor
- 30k-50k adım: yakınsama, +15.3 TL'de düzleşiyor

Bu eğri şekli (S-curve) sağlıklı bir RL eğitiminin göstergesi.

**`explained_variance`:**
- Başlangıç: -0.003 (model hiçbir şeyi tahmin edemiyor)
- Bitiş: 0.999 (model ortamı neredeyse mükemmel tahmin ediyor)

## Neden PPO Eşikten Düşük?

Eşik politikası +31.52 TL, PPO +15.32 TL çıktı. Bunun sebebi veri:

- **Eşik politikası**: tek günlük fallback veriyi her seferinde görüyor,
  o günü "ezberliyor" (std=0.00 — her günde aynı sonuç)
- **PPO**: genelleme yapmaya çalışıyor, tek günlük veriyle
  tam optimum stratejiyi bulamıyor

Gerçek 8784 saatlik EPİAŞ verisiyle (`data/processed/aligned_dataset.csv`)
eğitim yapılırsa PPO'nun eşiği geçmesi bekleniyor.

## Hiperparametre Seçimleri

- **`learning_rate=3e-4`**: PPO için literatürde yaygın varsayılan
- **`n_steps=512`**: her güncelleme öncesi toplanan adım sayısı;
  24 saatlik episode'larla uyumlu (512 / 24 ≈ 21 tam bölüm)
- **`gamma=0.99`**: uzun vadeli ödülleri önemsiyor;
  gece şarj edip akşam deşarj etmek için yüksek gamma gerekli
- **`n_envs=4`**: veri çeşitliliği için