# Staj Defteri — Gün 19

**Tarih:** 8 Ağustos 2026
**Stajyer:** Alesam Baath
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 19 — Uçtan Uca Test (Sıfırdan Kurulum) & Deney Kayıt Defteri

### 1. Bugün Ne Yapıldı?

İki hedef vardı: (1) projeyi **sıfırdan kurulumla** baştan sona çalıştırıp
uçtan uca doğrulamak, (2) proje boyunca üretilen tüm değerlendirme sonuçlarını
tek bir izlenebilir kayıt dosyasında toplamak — `docs/experiments/results-log.md`.

Temiz bir sanal ortam kuruldu, bağımlılıklar yüklenmeye başlandı, test paketinin
ve değerlendirme scriptlerinin yapısı incelendi ve tüm faz sonuçları (Faz 1, 2, 3
ve tahmin robustluğu) kaynaklarıyla birlikte tek bir deney defterine işlendi.

---

### 2. Uçtan Uca Kurulum — Adımlar

Kurulum, README'deki resmi akış izlenerek yapıldı:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/eval/eval_policy.py --days 30
python scripts/forecast/compare.py
```

**Kurulum gözlemi.** Bağımlılıklar iki kategoride değerlendirildi:

- **Hafif paketler** (numpy, pandas, gymnasium, statsmodels, pytest, plotly):
  sorunsuz kuruldu. Ortam fiziği, veri hizalama ve kural tabanlı politikalar
  bu paketlerle torch olmadan çalışabiliyor.
- **PyTorch + Stable-Baselines3:** güncel `torch` PyPI tekerleği tek başına
  ~527 MB, üstüne gigabaytlarca `nvidia-*` CUDA bağımlılığı çekiyor. CPU-only
  tekerleğin geldiği `download.pytorch.org` indeksi kısıtlı ortamda erişime
  kapalıydı. Bu yüzden RL model yükleme gerektiren eval'lar **bu kısıtlı ortamda
  yeniden koşulmadı**; bunun yerine defterdeki sayılar projenin daha önce
  yerel makinede/Colab'da üretip repoya işlediği **gerçek** çıktılardan derlendi
  ve her tablonun kaynağı açıkça belirtildi.

**Öğrenim:** RL projelerinde "sıfırdan kurulum" testinin en kırılgan noktası
derin öğrenme kütüphanelerinin (torch) platform/GPU'ya bağlı devasa ikili
bağımlılıklarıdır. Bir E2E test planı, bu ağır adımı ayrı bir "GPU/Colab ortamı"
ön koşulu olarak açıkça işaretlemeli; hafif doğrulamalar (ortam, veri, baseline,
API katmanı) ise torch'suz koşabilecek şekilde ayrık tutulmalı. Bu, hızlı CI için
de doğru mimari.

---

### 3. Deney Kayıt Defteri — `docs/experiments/results-log.md`

Bugüne kadar sonuçlar README, `training-notes.md` ve günlük staj defterlerine
dağılmıştı. Hepsi tek bir izlenebilir dosyada toplandı. Her bölüm şunu içeriyor:
**hangi komut**, **hangi veri**, **hangi ortam parametreleri** ve **kaynak dosya**.

Toplanan bölümler:

1. **Değerlendirme ortamı** — `SmartHomeEnergyEnv` parametreleri ve veri kapsamı.
2. **Faz 1** — 30 günlük net kazanç (SAC +8.98, PPO +7.67, A2C +3.19) ve ilk PPO
   eğitimi notları.
3. **Faz 2** — kural tabanlı baseline'ların Optuna öncesi/sonrası (ThresholdPolicy
   −2.57 → **+2.53 TL**).
4. **Faz 3** — 74 günlük test setinde tahmin belirsizliğine robustluk tablosu
   (TD3 +14.72, SAC +14.38 Oracle) + cihaz çalıştırma oranı (reward-hacking kontrolü).
5. **Fiyat tahmin modelleri** — LightGBM+Optuna %29.93 sMAPE, Ensemble %32.10.
6. **Test paketi** — 7 dosya, ~24 test; torch gerektiren/gerektirmeyen ayrımı.
7. **Yeniden üretim** — sıfırdan kurulum komutları ve ortam notu.
8. **Özet çıkarımlar**.

---

### 4. Sonuçların Kısa Yorumu

- **En iyi ajanlar TD3 ve SAC:** 74 günlük test setinde +14–15 TL/gün ve dört
  fiyat-bilgisi modunda ±0.2 TL içinde kalarak tahmin belirsizliğine **robust**.
- **Off-policy > on-policy:** SAC/TD3, sürekli batarya kontrol probleminde
  PPO/A2C'yi belirgin geçiyor; A2C bu problemde negatif.
- **Kural tabanlı politikalar** Optuna ile pozitife çekilebiliyor ama RL'in
  dağılımdan bağımsız kararlılığına ulaşamıyor (FcAware modlar arası 9 TL oynuyor).
- **Reward-hacking kontrolü:** PPO cihazı her modda tam kapasitede (0.083)
  çalıştırırken SAC (0.053) seçici davranıyor — ödül değeri tek başına yeterli
  metrik değil; `device_activation_rate` şart.

---

### 5. Oluşturulan/Değişen Dosyalar (Gün 19)

Günün asıl planı (uçtan uca test + deney defteri):

```
docs/experiments/results-log.md   (yeni)  — birleşik deney kayıt defteri
docs/gun_19_staj_defteri.md       (yeni)  — bu defter
```

Aynı gün tamamlanıp aynı PR'da taşınan çok dilli (i18n) çalışma:

```
frontend/src/i18n.jsx                     — TR/EN/AR sözlük + LangProvider + RTL
frontend/src/main.jsx, TopNav, ConfigPanel, Footer, pages/*.jsx
frontend/src/landing.css                  — before/after toggle stili
frontend/src/pages/Landing.jsx            — dil-değişimi donması düzeltmesi
dashboard/core/simulate.py                — oneriler_kodlu (dile bağımsız öneri)
dashboard/core/threejs.py                 — 3D HUD unit_label parametresi
backend/main.py                           — öneri + HUD etiketi dile göre
frontend/src/components/Building.jsx       — 3D bina dil parametresi
```

---

### 6. Teknik Öğrenimler

**İzlenebilirlik (reproducibility) bir dosya değil, bir disiplindir.** Sonuç
tablosuna değeri yazmak yetmiyor; o değeri üreten komut, veri kesiti ve ortam
parametreleri olmadan sayı tekrar üretilemez. `results-log.md` bu üçlüyü her
satırda zorunlu kıldı.

**Ağır bağımlılıkları izole et.** Torch gibi platform bağımlı, gigabaytlık
bağımlılıklar E2E akışının en kırılgan halkası. Hafif doğrulamaları (env, veri,
baseline, API) torch'tan ayırmak hem hızlı geri bildirim hem de dayanıklı CI
sağlar.

**Kaynak dürüstlüğü.** Bir ortamda taze koşulamayan sonuçlar "taze koşuldu" gibi
sunulmamalı. Defterde her tablo, üretildiği koşuma atıfla ve yeniden üretim
komutuyla birlikte verildi.

---

### 7. Git Commits (Gün 19)

```
PR #XX: feat/i18n-en-ar → main

[hash]  feat(i18n): TR/EN/AR çevirisi — landing + uygulama, RTL desteği
         - i18n.jsx sözlük + LangProvider, TopNav dil seçici
         - tüm sayfalar + ConfigPanel + Footer t() ile
[hash]  fix(landing): AnimatePresence dil-değişimi donması + toggle/hero düzeltmeleri
         - showcase kartları key={i} (IntersectionObserver kopması giderildi)
         - mode="wait" kilidi kaldırıldı, before/after toggle CSS, hero AI rozeti
[hash]  feat(i18n): backend önerileri ve 3D bina HUD etiketi dile göre
         - simulate.oneriler_kodlu (kod+parametre), Simulasyon.formatOneri
         - threejs.building_html unit_label, backend /api/building-html dil
[hash]  docs: deney kayıt defteri (results-log.md) — tüm faz eval sonuçları
[hash]  docs: Gün 19 staj defteri
```

> Not: `#XX` ve `[hash]` yer tutucularını gerçek PR numarası ve commit
> hash'leriyle değiştir (`git log --oneline -5`).

---

### 8. Yarın (Gün 20)

Torch/GPU'lu bir ortamda (yerel veya Colab) `results-log.md`'deki tüm eval
komutlarını bire bir yeniden koşup çıktıları tazeleme; ardından README Sonuçlar
bölümüyle deney defteri arasında birebir tutarlılık denetimi.
