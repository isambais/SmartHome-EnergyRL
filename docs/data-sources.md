# Veri Kaynakları

Bu doküman, projede kullanılan/kullanılacak veri kaynaklarını, erişim yöntemlerini ve
ham veri → işlenmiş veri dönüşümünü örneklerle açıklar. Genel bağlam için bkz.
`implementation_plan.md` Bölüm 8 (Veri Kaynakları ve Ön İşleme).

---

## 1. Elektrik Fiyatı — EPİAŞ Şeffaflık Platformu (PTF)

* **Kaynak:** https://seffaflik.epias.com.tr
* **Erişim:** ELEKTRİK → ELEKTRİK PİYASALARI → Piyasa Takas Fiyatı (PTF). Hesap açmadan,
  kayıt/onay beklemeden CSV olarak indirilebiliyor.
* **Ham dosya adı formatı:** `Piyasa_Takas_Fiyati-DDMMYYYY-DDMMYYYY.csv`
* **Durum:** Tamamlandı (Gün 2, `src/data/epias_loader.py`).

### Ham format (örnek satırlar)

```
Tarih;Saat;PTF (TL/MWh);PTF (USD/MWh);PTF (EUR/MWh)
15.07.2026;00:00;3.325,00;70,88;62,03
15.07.2026;01:00;2.717,20;57,92;50,69
15.07.2026;02:00;2.153,64;45,91;40,18
```

Not: Noktalı virgülle (`;`) ayrılmış, sayılar Türkçe/Avrupa formatında (binlik ayraç nokta,
ondalık ayraç virgül) geliyor — bu yüzden `EpiasLoader._parse_turkish_number()` ile özel
olarak dönüştürülüyor.

### İşlenmiş çıktı — `EpiasLoader.load_csv()` sonrası (mockup)

| timestamp           | price_tl_mwh |
| -------------------- | ------------ |
| 2026-07-15 00:00:00  | 3325.00      |
| 2026-07-15 01:00:00  | 2717.20      |
| 2026-07-15 02:00:00  | 2153.64      |
| ...                   | ...          |

---

## 2. Güneş Üretimi — NREL/NLR PVWatts API

* **Kaynak:** https://developer.nlr.gov/docs/solar/pvwatts/v8/ (PVWatts V8)
* **Erişim:** Ücretsiz API key ile (https://developer.nlr.gov/signup/); test/prototipleme
  için herkese açık `DEMO_KEY` kullanılabilir (saatte 1000 istek limiti).
* **Durum:** Tamamlandı (Gün 3, `src/data/solar_profile.py`). Gerçek API çağrısıyla
  doğrulandı — İstanbul koordinatları (41.01, 28.98) için saatlik AC üretim verisi
  başarıyla alındı.
* **Not:** PVWatts, belirli bir takvim yılına değil, o konum için TMY (Typical
  Meteorological Year) verisine dayanır — 8760 saatlik "tipik yıl" döndürür.
  `SolarProfileGenerator.align_to_dates()` bu profili ay-gün-saat eşlemesiyle gerçek
  hedef tarihlere (ör. EPİAŞ fiyat tarihleriyle aynı günlere) hizalar.

### Örnek çıktı (İstanbul, 4kW sistem)

| timestamp_tmy        | solar_kw |
| --------------------- | -------- |
| 2001-01-01 00:00:00   | 0.0      |
| 2001-01-01 09:00:00   | 0.023    |
| 2001-01-01 10:00:00   | 0.252    |
| 2001-01-01 11:00:00   | 0.361    |

## 3. Ev Talebi — UK-DALE (gerçek veri)

* **Kaynak:** UK-DALE (UK Domestic Appliance-Level Electricity), Jack Kelly & William
  Knottenbelt, *Scientific Data* 2015, DOI: 10.1038/sdata.2015.7
* **Lisans:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **İndirme:** http://data.ukedc.rl.ac.uk/simplebrowse/edc/efficiency/residential/EnergyConsumption/Domestic/UK-DALE-2017/UK-DALE-FULL-disaggregated/ukdale.zip
  (3.5 GB — sadece dağıtılmış/disaggregated CSV verisi; 7.6 TB'lık ham 16kHz veri
  kullanılmadı, ihtiyacımız için gereksiz).
* **Kullanılan dosya:** `house_1/channel_1.dat` (evin "aggregate" / toplam güç kanalı).
  house_1, 09/11/2012 - 26/04/2017 arası kesintisiz 4.3 yıllık kayıt içeriyor (5 evin
  en uzun süreli olanı).
* **Ham format:** her satır `<unix_timestamp> <güç_watt>`, 6 saniyede bir ölçüm
  (21.8 milyon satır).
* **Durum:** Tamamlandı (Gün 3, `src/data/demand_profile.py`). Gerçek dosyayla uçtan uca
  doğrulandı:
  - 21.837.636 ham satır → 37.843 saatlik ortalama nokta
  - Ortalama günlük tüketim: **9.06 kWh** (min 0.92, max 19.48 kWh/gün)
  - Sabah/akşam tepe noktaları net: gece ~200-250 W, akşam 18-20 arası ~520-530 W

### İşleme yaklaşımı

Ham 6 saniyelik veri saatlik ortalamaya indirgenir, ardından çok yıllık veriden
haftanın günü + saat bazında (168 = 7×24 değerlik) bir **"tipik hafta" profili**
çıkarılır (`compute_typical_profile()`). Bu profil, `align_to_dates()` ile EPİAŞ
fiyat tarihleriyle aynı takvime (farklı yıl olsa da haftanın günü + saat eşlemesiyle)
hizalanır — `SolarProfileGenerator`'daki TMY hizalama mantığıyla tutarlı bir yaklaşım.

Not: `channel_1.dat` dosyası (~330 MB) repoya girmez (`.gitignore` → `data/raw/*`);
kullanmak isteyen, ZIP'i indirip `house_1/channel_1.dat`'ı `data/raw/` altına
koymalıdır.

---

## Hizalama Notu

Üç veri kaynağının aynı saatlik takvimde hizalanması ve `data/processed/` altında
birleştirilmesi Gün 4'te yapılacaktır (bkz. implementation_plan.md Bölüm 8 — bu adım
projedeki en kritik ön işleme adımı olarak işaretlenmiştir).
