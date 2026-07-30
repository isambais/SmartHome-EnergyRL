# Staj Defteri — Gün 12

**Tarih:** 29 Temmuz 2026  
**Stajyer:** Alesam Baath  
**Şirket:** Trunçgil Teknoloji, Gaziantep Teknopark  
**Proje:** SmartHome-EnergyRL — Takviyeli Öğrenme Tabanlı Ev Enerji Yönetim Sistemi

---

## Gün 12 — Aşama 3: Hibrit Aksiyon Uzayı ve Ertelenebilir Yük

### 1. Bugün Ne Yapıldı?

Uygulama planının 12. günü kapsamında, `src/env/energy_env.py` dosyasına Aşama 3 desteği eklendi. Mevcut tek boyutlu sürekli aksiyon uzayı (`Box(shape=(1,))`), batarya + ertelenebilir cihaz kontrolünü birlikte barındıran iki boyutlu bir yapıya (`Box(shape=(2,))`) dönüştürüldü. Ek olarak gerçekçi multi-step cihaz çalışma modeli, günlük aktivasyon sınırı ve tüm kural tabanlı politikaların Aşama 3 uyumluluğu sağlandı.

### 2. Hibrit Aksiyon Uzayı Tasarımı

```
action[0]  ∈ [-1, 1]   →  Batarya kontrolü (sürekli)
action[1]  ∈ [-1, 1]   →  Ertelenebilir yük sinyali (ayrıklaştırılır)
                           > 0  ve saat penceresi içinde  →  cihazı çalıştır
                           ≤ 0  veya pencere dışında      →  çalıştırma
```

Gymnasium `Tuple` veya `Dict` aksiyon uzayları Stable-Baselines3'ün tüm algoritmalarıyla uyumlu değildir; bu nedenle ayrık sinyali sürekli uzaya gömme (embedding) yöntemi tercih edildi. `step()` içinde `int(action[1] > 0.0 and in_window)` ile anlık ayrıklaştırma yapılmaktadır.

### 3. Gözlem Uzayı Güncellemesi

`enable_deferrable=True` olduğunda gözlemin sonuna 2 yeni eleman eklendi:

| İndeks | Alan | Açıklama |
|--------|------|----------|
| `[-2]` | `device_used_today` | 0=henüz çalıştırılmadı, 1=bugün en az bir kez çalıştı |
| `[-1]` | `device_steps_remaining_norm` | Kalan çalışma adımı / toplam adım [0,1] |

| Aşama | Gözlem Boyutu |
|-------|---------------|
| Aşama 1 | 56 |
| Aşama 2 | 104 |
| Aşama 3 (Faz 1 üstünde) | 58 |
| Aşama 3 (Faz 2 üstünde) | 106 |

### 4. Multi-Step Cihaz Çalışma Modeli

Gerçekçi cihaz davranışı: çamaşır makinesi gibi cihazlar başlatılınca `deferrable_load_hours` saat boyunca durdurulamaz biçimde çalışır.

```python
# Aktivasyon: sadece cihaz çalışmıyorsa + pencere içi + limit dolmamışsa
if action[1] > 0 and in_window and under_limit and not_running:
    device_steps_remaining = round(deferrable_load_hours)

# Her adımda: çalışıyorsa yük uygula ve geri say (durdurulamaz)
if device_steps_remaining > 0:
    device_steps_remaining -= 1
    demand += deferrable_load_power_kw
```

### 5. Reward Hacking Cezası ve Aktivasyon Limiti

**Episode sonu cezası:** Cihaz gün boyunca hiç çalıştırılmazsa `-2.0 TL` ceza.

**Günlük aktivasyon limiti (`max_activations_per_day=2`):** Ajan aynı cihazı günde 2'den fazla çalıştıramaz. Cihazı sürekli açıp kapatan politikaları engeller.

### 6. Kural Tabanlı Politikaların Aşama 3 Uyumluluğu

`src/baselines/rule_based.py` modülüne `_make_action()` yardımcı fonksiyonu eklendi. `enable_deferrable=True` ortamda tüm 7 politika otomatik olarak `(2,)` aksiyon döndürür.

| Politika | Deferrable Stratejisi |
|----------|----------------------|
| `HoldPolicy` | Hiç çalıştırma |
| `ThresholdPolicy` | Ucuz fiyat diliminde çalıştır |
| `SelfConsumptionPolicy` | Güneş fazlasında çalıştır |
| `ToUPolicy` | Gündüz orta dilimde çalıştır (pik/gece dışında) |
| `ForecastAwarePolicy` | Günün en ucuz %25'inde çalıştır |
| `PeakShavingPolicy` | Net çekiş düşükken çalıştır |
| `GridAwarePolicy` | Kesinti/DR yoksa ve fiyat ucuzsa çalıştır |

### 7. Episode Metrik Takibi

```python
"device_activation_count": int    # gün içi toplam aktivasyon sayısı
"device_activation_rate": float   # aktivasyon_sayısı / saat_sayısı
```

### 8. Geriye Dönük Uyumluluk

`enable_deferrable=False` (varsayılan) ile ortam, Aşama 1 ve Aşama 2 davranışını tam olarak korur.

### 9. Testler

| Dosya | Yeni Test | Toplam |
|-------|-----------|--------|
| `tests/test_energy_env.py` | +17 (Aşama 3) | 28 |
| `tests/test_rule_based.py` | +15 (Faz 3 deferrable) | 54 |
| **Toplam** | **+32** | **65/65 ✅** |

**Sonuç:** `pytest tests/test_energy_env.py tests/test_rule_based.py -v` → **65/65 geçti.**

### 10. Git Commits (Gün 12)

```
feat(env): add Phase 3 multi-step deferrable load with run-duration model
feat(env): add max_activations_per_day limit to prevent reward hacking
feat(baselines): add Phase 3 deferrable support to all rule-based policies
test(env): add 17 Phase 3 tests (multi-step, steps_remaining, re-activation guard)
test(baselines): add 15 Phase 3 deferrable action tests (65/65 passing)
```

### 11. Teknik Öğrenimler

**Hibrit aksiyon uzayı tasarımı**, pekiştirmeli öğrenmede sürekli ve ayrık kararların birleştirilmesinde sık karşılaşılan bir sorundur. Gymnasium `Tuple`/`Dict` uzayları teorik olarak doğru yaklaşım olsa da SB3 uyumluluk kısıtları nedeniyle "embedding" yöntemi tercih edildi.

**Multi-step device execution**, tek adım enerji uygulamasından çok daha gerçekçidir. Cihaz başlatılınca `deferrable_load_hours` kadar adım boyunca çalışır ve ajan bu süreçte müdahale edemez. Bu, zamansal planlama yeteneklerini test eden daha zengin bir karar ortamı oluşturur.

**Reward shaping** konusunda önemli bir pratik ders: RL ajanları çok boyutlu ödül fonksiyonlarında kısmi hedefleri optimize edip diğerlerini ihmal edebilir. Episode sonu cezası + günlük aktivasyon limiti birlikte "constraint as penalty" yaklaşımının katmanlı uygulamasını örneklemektedir.

---

## Yarın (Gün 13)

Aşama 3 ortamıyla PPO, A2C, SAC ve TD3 algoritmalarının yeniden eğitimi yapılacak. `device_activation_rate` metriği TensorBoard'da izlenecek. Deferrable ceza katsayısının ajan davranışına etkisi raporlanacak.
