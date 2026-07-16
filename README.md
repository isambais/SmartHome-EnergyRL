# SmartHome Energy RL

Pekiştirmeli Öğrenme (Reinforcement Learning) ile bataryayı ve ertelenebilir cihazları saatlik elektrik fiyatına ve güneş üretimine göre otomatik yöneten bir akıllı ev enerji ajanı.

## Proje Hakkında

Ev ve bina sahipleri elektrik fiyatının saatlik değiştiğinin ve güneş üretiminin gün içinde dalgalandığının çoğunlukla farkında değil; batarya ve ertelenebilir cihazlar genelde sabit kurallarla ya da manuel yönetildiği için ciddi bir tasarruf potansiyeli kaçırılıyor.

Bu proje, saatlik elektrik fiyatını (EPİAŞ açık verisi), güneş üretimini ve ev talebini gözlemleyerek bataryayı ne zaman şarj/deşarj edeceğine ve cihazları ne zaman çalıştıracağına kendi kendine karar veren bir RL ajanı geliştiriyor. Ajanın performansı, batarya kullanılmayan bir senaryo ve basit bir sezgisel kuralla karşılaştırılarak somut bir tasarruf yüzdesiyle ölçülüyor.

## Özellikler

- Curriculum learning yaklaşımıyla aşamalı olarak inşa edilen özel bir Gymnasium ortamı (önce saf batarya arbitrajı, sonra güneş/talep entegrasyonu, en son ertelenebilir cihaz + tahmin dayanıklılığı)
- Stable-Baselines3 (PPO) ile eğitim
- EPİAŞ gerçek piyasa fiyatı, açık güneş üretim ve ev tüketim verisi entegrasyonu
- Kısa vadeli fiyat tahmin modülü ve oracle/tahmin/naive karşılaştırması
- Streamlit tabanlı sonuç dashboard'u

## Teknoloji Yığını

Python, Gymnasium, Stable-Baselines3, XGBoost/statsmodels, pandas, Streamlit

## Proje Yapısı

```
src/
├── env/            # Özel Gymnasium ortamı
├── data/           # Veri yükleme/işleme modülleri
├── agents/         # PPO eğitim scriptleri
├── baselines/      # Sezgisel karşılaştırma stratejisi
├── forecasting/    # Kısa vadeli fiyat tahmin modeli
├── evaluation/      # Karşılaştırma ve metrik hesaplama
└── dashboard/       # Streamlit arayüzü
```

## Kurulum

```
git clone https://github.com/isambais/SmartHome-EnergyRL.git
cd SmartHome-EnergyRL
pip install -r requirements.txt
```

## Kullanım

```
# Ajanı eğitmek için
python src/agents/train_ppo.py

# Eğitilmiş ajanı baseline'larla ve oracle/tahmin/naive modlarıyla karşılaştırmak için
python src/evaluation/compare.py

# Sonuçları görselleştiren dashboard'u açmak için
streamlit run src/dashboard/app.py
```

## Sonuçlar

_Proje tamamlandıkça bu bölüm, RL ajanının baseline'a göre elde ettiği somut tasarruf yüzdesi ve oracle/tahmin/naive karşılaştırma sonuçlarıyla güncellenecektir._

## Detaylı Plan

Projenin tam kapsamı, mimarisi, veri kaynakları ve 20 iş günlük yol haritası için bkz. [implementation_plan.md](./implementation_plan.md).

## Durum

Bu proje aktif olarak geliştirilmektedir (staj kapsamında, 20 iş günlük süre). Güncel ilerleme için commit geçmişine ve GitHub Projects panosuna bakılabilir.
