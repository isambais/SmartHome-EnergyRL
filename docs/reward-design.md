# Ödül Fonksiyonu Tasarımı

## Curriculum Aşama 1 — Saf Batarya Arbitrajı

### Formül

reward = revenue_tl - cost_tl

- **cost_tl**: Şebekeden çekilen enerji × o saatin fiyatı (TL/kWh)
- **revenue_tl**: Deşarj edilen enerji × o saatin fiyatı × deşarj verimliliği

### Neden Bu Formül?

Ajanın öğrenmesi gereken davranış basit: gece elektrik ucuzken şarj et,
akşam pahalıyken deşarj et (arbitraj). Bu formül doğrudan bunu ödüllendiriyor:
- Pahalı saatte deşarj → yüksek pozitif ödül
- Ucuz saatte şarj → küçük negatif ödül (kabul edilebilir maliyet)
- Yanlış zamanda işlem → negatif net ödül (ceza)

### Verimlilik Kaybı

Şarj maliyeti: Şebekeden çekilen × fiyat
Batarya : Batarya verimliği x Şebekeden çekilen
Deşarj geliri: Bataryadan çıkan × fiyat 
Net: Ödediğimiz - Kazandığımız

Diyelim fiyat = 2 TL/kWh. Bataryaya 5 kWh şarj etmek istiyoruz.

Şarj:

Şebekeden 5 kWh çekiyoruz. Ama batarya %100 verimli değil — bir kısmı ısıya dönüşüp kayboluyor.

Şebekeden çekilen:     5 kWh
Bataryaya giren:       5 × √0.9 = 4.74 kWh
Ödediğin para:         5 × 2 = 10 TL

Deşarj:

Bataryada 4.74 kWh var. Bunu satmak istiyorsuz. Yine kayıp var:

Bataryadan çıkan:      4.74 kWh
Şebekeye giden:        4.74 × √0.9 = 4.5 kWh
Kazandığın para:       4.5 × 2 = 9 TL

Net:

Ödediğin:   10 TL
Kazandığın:  9 TL
Kayıp:       1 TL

Bu gerçekçi bir modelleme — gerçek bataryalar da enerji kaybeder.

### Reward Hacking Riski

Bu aşamada ev talebi ve cihazlar yok, bu yüzden reward hacking riski düşük.
Ajan sadece fiyat arbitrajına odaklanıyor.

Aşama 3'te (Gün 13+) ertelenebilir cihazlar eklenince şu risk ortaya çıkar:
ajan cihazı hiç çalıştırmayarak maliyeti sıfırlayabilir. Bunu önlemek için
"cihaz gün sonuna kadar çalışmadıysa sert ceza" terimi eklenecek
(implementation_plan.md Bölüm 9).

### İlerideki Aşamalar

| Aşama | Ödül Formülü |
|-------|-------------|
| 1 (Gün 5-8)  | `revenue - cost` |
| 2 (Gün 9-12) | `revenue - cost - grid_import_cost` (güneş + talep) |
| 3 (Gün 13-16)| `revenue - cost - grid_import_cost - device_penalty` |