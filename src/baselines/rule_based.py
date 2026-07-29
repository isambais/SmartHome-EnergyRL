"""Kural tabanlı (rule-based) baseline politikalar.

Üç politika tek bir modülde, aynı Gymnasium arayüzüyle çalışır:

  HoldPolicy              — her zaman bekle (aksiyon = 0).
                            "Batarya yok" senaryosunun davranışsal karşılığı:
                            ortam fizik modelinden bağımsız olarak hiçbir
                            şarj/deşarj eylemi gerçekleşmez.

  ThresholdPolicy         — Aşama 1 (saf arbitraj):
                            Fiyat 30. persantil altındaysa şarj (aksiyon = +1),
                            70. persantil üstündeyse deşarj (aksiyon = −1),
                            arada bekle.

  SelfConsumptionPolicy   — Aşama 2 (güneş + talep):
                            Güneş fazlası varsa önce bataryayı şarj et,
                            akşam/gece fiyat yüksekken deşarj et.
                            "Önce öz-tüketim, sonra arbitraj" hiyerarşisi.

Kullanım::

    from src.baselines.rule_based import ThresholdPolicy

    policy = ThresholdPolicy()
    action = policy(obs, env)          # np.ndarray, shape (1,)

    # Tüm politikalar aynı imzayı paylaşır:
    #   __call__(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray

Gözlem indeksleri (energy_env.py'den):
    [0]     soc              Şarj durumu [0, 1]
    [1]     soh              Pil sağlığı [0.5, 1.0]
    [2:6]   zaman özellikleri (sin/cos saat + haftanın günü)
    [6]     grid_available
    [7]     dr_signal
    [8:32]  bugünkü fiyatlar (24 saat)
    [32:56] yarınki fiyat tahmini (24 saat)
    [56:80] güneş profili    (Aşama 2, yoksa sıfır)
    [80:104] talep profili   (Aşama 2, yoksa sıfır)
"""

from __future__ import annotations

import numpy as np

Policy = "Callable[[np.ndarray, Any], np.ndarray]"


class HoldPolicy:
    """Her zaman bekle — 'batarya yok' senaryosunun davranışsal eşdeğeri.

    Batarya kapasitesi sıfır olarak ayarlanmış bir ortamla aynı sonucu
    üretir; ancak tek bir kod yolunda çalışır (ayrı ortam gerektirmez).
    """

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:  # noqa: ARG002
        return np.array([0.0], dtype=np.float32)

    def __repr__(self) -> str:
        return "HoldPolicy(aksiyon=0 — batarya yok senaryosu)"


class ThresholdPolicy:
    """Fiyat eşiği tabanlı arbitraj — Aşama 1 için kural tabanlı baseline.

    Mantık:
      - Fiyat, 24 saatlik dağılımın alt %`low_pct` dilimindeyse → şarj et (+1)
      - Fiyat, üst %`high_pct` dilimindeyse → deşarj et (−1)
      - Arada → bekle (0)

    Bu, "gece ucuzu şarj et, akşam pahalısını sat" sezgisel kuralını
    sayısal olarak ifade eder; öğrenme gerektirmez.

    Parameters
    ----------
    low_pct:
        Şarj eşiği persantili (varsayılan 30).
    high_pct:
        Deşarj eşiği persantili (varsayılan 70).
    """

    def __init__(self, low_pct: float = 30.0, high_pct: float = 70.0) -> None:
        self.low_pct = low_pct
        self.high_pct = high_pct

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        # obs[8:32] → bugünkü 24 saatlik fiyatlar
        prices = obs[8:32]
        low = np.percentile(prices, self.low_pct)
        high = np.percentile(prices, self.high_pct)

        current_price = float(env._current_day_prices[env.t])

        if current_price <= low:
            return np.array([1.0], dtype=np.float32)   # şarj
        if current_price >= high:
            return np.array([-1.0], dtype=np.float32)  # deşarj
        return np.array([0.0], dtype=np.float32)        # bekle

    def __repr__(self) -> str:
        return (
            f"ThresholdPolicy(şarj<P{self.low_pct:.0f}, "
            f"deşarj>P{self.high_pct:.0f})"
        )


class SelfConsumptionPolicy:
    """Öz-tüketim öncelikli kural — Aşama 2 için kural tabanlı baseline.

    Hiyerarşi (her saat başı):
      1. Güneş fazlası varsa (solar > demand) → bataryayı şarj et.
         Fazla enerjiyi önce depola; fiyat ne olursa olsun.
      2. Güneş yoksa veya yetersizse + fiyat yüksekse → bataryadan karşıla.
      3. Gece düşük fiyat saatlerinde → şebekeden şarj et (arbitraj fırsatı).
      4. Diğer tüm durumlarda → bekle.

    Parameters
    ----------
    low_pct:
        Gece şarjı eşiği persantili (varsayılan 30).
    high_pct:
        Öz-tüketim deşarjı eşiği persantili (varsayılan 60).
    solar_surplus_threshold:
        Güneş fazlasının "anlamlı" sayılması için minimum kW değeri.
    """

    def __init__(
        self,
        low_pct: float = 30.0,
        high_pct: float = 60.0,
        solar_surplus_threshold: float = 0.1,
    ) -> None:
        self.low_pct = low_pct
        self.high_pct = high_pct
        self.solar_surplus_threshold = solar_surplus_threshold

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        prices = obs[8:32]
        low = np.percentile(prices, self.low_pct)
        high = np.percentile(prices, self.high_pct)
        current_price = float(env._current_day_prices[env.t])

        # Güneş ve talep verisi Aşama 2'de gözlemde (indeks 56-104)
        t = env.t
        solar_kw = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0
        solar_surplus = solar_kw - demand_kw

        # 1. Anlamlı güneş fazlası → şarj et
        if solar_surplus > self.solar_surplus_threshold:
            return np.array([1.0], dtype=np.float32)

        # 2. Fiyat yüksek + bataryada enerji var → deşarj et (öz-tüketim)
        soc = float(obs[0])
        if current_price >= high and soc > 0.15:
            return np.array([-1.0], dtype=np.float32)

        # 3. Gece ucuz → şebekeden şarj et (arbitraj fırsatı)
        if current_price <= low and soc < 0.90:
            return np.array([1.0], dtype=np.float32)

        # 4. Bekle
        return np.array([0.0], dtype=np.float32)

    def __repr__(self) -> str:
        return (
            f"SelfConsumptionPolicy("
            f"öz-tüketim öncelikli, şarj<P{self.low_pct:.0f}, "
            f"deşarj>P{self.high_pct:.0f})"
        )


class ToUPolicy:
    """Çok zamanlı tarife (Time-of-Use) — saate göre sabit blok kararı.

    Türkiye TEDAŞ çok zamanlı tarife yapısını modelleyen kural tabanlı politika.
    Fiyata bakmaz; sadece saat dilimine göre karar verir.

    Varsayılan bloklar (TEDAŞ T2 tarifesine yakın):
      Gece   23:00–07:00  → şarj (+1)    — en ucuz dilim
      Gündüz 07:00–17:00  → bekle (0)    — orta dilim
      Pik    17:00–22:00  → deşarj (−1)  — en pahalı dilim
      Gece   22:00–23:00  → bekle (0)    — geçiş saati

    Bu politikanın önemi: milyonlarca ev zaten bu tarifede, ama
    manuel olarak veya hiç optimize etmiyor. RL ajanının bu basit
    saat tabanlı kuraldan ne kadar iyi olduğunu kanıtlamak için kullanılır.

    Parameters
    ----------
    peak_hours:
        Pik (pahalı) dilim saat aralıkları. Liste of (başlangıç, bitiş).
    off_peak_hours:
        Gece (ucuz) dilim saat aralıkları.
    """

    def __init__(
        self,
        peak_hours: list[tuple[int, int]] | None = None,
        off_peak_hours: list[tuple[int, int]] | None = None,
    ) -> None:
        # TEDAŞ T2 varsayılan değerleri
        self.peak_hours = peak_hours or [(17, 22)]
        self.off_peak_hours = off_peak_hours or [(23, 24), (0, 7)]

    def _current_hour(self, env) -> int:
        """Ortamdan mevcut saati al."""
        return int(env.t)

    def _in_blocks(self, hour: int, blocks: list[tuple[int, int]]) -> bool:
        return any(start <= hour < end for start, end in blocks)

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:  # noqa: ARG002
        hour = self._current_hour(env)

        if self._in_blocks(hour, self.peak_hours):
            return np.array([-1.0], dtype=np.float32)   # deşarj — pik tarife

        if self._in_blocks(hour, self.off_peak_hours):
            return np.array([1.0], dtype=np.float32)    # şarj — gece tarifesi

        return np.array([0.0], dtype=np.float32)         # bekle — gündüz

    def __repr__(self) -> str:
        return (
            f"ToUPolicy(pik={self.peak_hours}, gece={self.off_peak_hours})"
        )


class ForecastAwarePolicy:
    """Yarınki fiyat tahminini kullanan ileri görüşlü politika.

    Mevcut threshold politikaları sadece bugünün 24 saatine bakar.
    Bu politika gözlemdeki yarınki tahmin verisini (obs[32:56]) de
    değerlendirerek daha iyi kararlar alır.

    Mantık:
      - Yarın bugünden belirgin ölçüde pahalıysa (fark > threshold):
          → Bugün agresif şarj et (yarınki pahalı saatler için hazırlık).
      - Yarın bugünden belirgin ölçüde ucuzsa:
          → Bugün şarj etme, yarın şarj et (daha ucuza).
      - Aksi hâlde standart threshold kuralını uygula.

    Tesla Powerwall ve SMA Sunny Home Manager gibi ticari sistemlerin
    gün öncesi piyasa entegrasyonunu modellemektedir.

    Parameters
    ----------
    low_pct:
        Bugün şarj eşiği persantili.
    high_pct:
        Bugün deşarj eşiği persantili.
    tomorrow_premium:
        Yarın ortalaması bugünden bu oran kadar yüksekse agresif şarj.
    tomorrow_discount:
        Yarın ortalaması bugünden bu oran kadar düşükse bugün bekleme.
    """

    def __init__(
        self,
        low_pct: float = 30.0,
        high_pct: float = 70.0,
        tomorrow_premium: float = 0.15,
        tomorrow_discount: float = 0.15,
    ) -> None:
        self.low_pct = low_pct
        self.high_pct = high_pct
        self.tomorrow_premium = tomorrow_premium
        self.tomorrow_discount = tomorrow_discount

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        today_prices    = obs[8:32]
        tomorrow_prices = obs[32:56]

        today_mean    = float(np.mean(today_prices))
        tomorrow_mean = float(np.mean(tomorrow_prices))

        current_price = float(env._current_day_prices[env.t])
        low  = np.percentile(today_prices, self.low_pct)
        high = np.percentile(today_prices, self.high_pct)
        soc  = float(obs[0])

        # Yarın belirgin pahalıysa → bugün doldurmaya çalış
        if tomorrow_mean > today_mean * (1 + self.tomorrow_premium):
            if current_price <= np.percentile(today_prices, 50) and soc < 0.95:
                return np.array([1.0], dtype=np.float32)

        # Yarın belirgin ucuzsa → bugün şarj etme, kapasiteyi koru
        if tomorrow_mean < today_mean * (1 - self.tomorrow_discount):
            if current_price >= high:
                return np.array([-1.0], dtype=np.float32)
            return np.array([0.0], dtype=np.float32)

        # Standart threshold mantığı
        if current_price <= low:
            return np.array([1.0], dtype=np.float32)
        if current_price >= high:
            return np.array([-1.0], dtype=np.float32)
        return np.array([0.0], dtype=np.float32)

    def __repr__(self) -> str:
        return (
            f"ForecastAwarePolicy("
            f"yarın>{self.tomorrow_premium*100:.0f}%→agresif şarj, "
            f"yarın<{self.tomorrow_discount*100:.0f}%→bekle)"
        )


class PeakShavingPolicy:
    """Tepe talebi kesme politikası — ticari binalar için.

    Türkiye'de büyük tüketiciler tüketim bedeli (kWh) + talep bedeli
    (o ay çekilen en yüksek kW × tarife) öder. Talep bedeli faturanın
    %30-40'ına ulaşabilir.

    Bu politika: anlık şebekeden çekiş `peak_threshold_kw` üzerindeyse
    bataryadan karşılar, tepeyi kesar. Fiyat optimizasyonu değil,
    güç tepe yönetimidir.

    Aşama 2 ortamında talep verisi gözlemde (obs[80:104]) mevcuttur.
    Güneş üretimi de hesaba katılarak net şebeke çekişi hesaplanır.

    Parameters
    ----------
    peak_threshold_kw:
        Bu değerin üzerindeki net şebeke çekişi → bataryadan karşıla.
    reserve_soc:
        Tepe kesme için tutulacak minimum SOC rezervi.
    low_pct:
        Gece şarjı için fiyat eşiği persantili.
    """

    def __init__(
        self,
        peak_threshold_kw: float = 2.0,
        reserve_soc: float = 0.30,
        low_pct: float = 25.0,
    ) -> None:
        self.peak_threshold_kw = peak_threshold_kw
        self.reserve_soc = reserve_soc
        self.low_pct = low_pct

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        t = env.t
        soc = float(obs[0])

        # Aşama 2: güneş ve talep gözlemde var
        solar_kw  = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0

        # Net şebeke çekişi = talep − güneş üretimi
        net_grid_kw = max(0.0, demand_kw - solar_kw)

        # Tepe aşımı → bataryadan karşıla
        if net_grid_kw > self.peak_threshold_kw and soc > self.reserve_soc:
            return np.array([-1.0], dtype=np.float32)

        # Gece ucuz → gündüz tepesine hazırlık için şarj et
        prices = obs[8:32]
        current_price = float(env._current_day_prices[t])
        low = np.percentile(prices, self.low_pct)
        if current_price <= low and soc < 0.90:
            return np.array([1.0], dtype=np.float32)

        return np.array([0.0], dtype=np.float32)

    def __repr__(self) -> str:
        return (
            f"PeakShavingPolicy("
            f"eşik={self.peak_threshold_kw}kW, "
            f"rezerv_soc={self.reserve_soc:.0%})"
        )


class GridAwarePolicy:
    """Şebeke bilinçli politika — kesinti ve talep yanıtı senaryoları.

    Gözlemdeki iki binary sinyal değerlendirilir:
      obs[6] = grid_available  (1=normal, 0=şebeke kesintisi)
      obs[7] = dr_signal       (1=talep yanıtı eventi aktif, 0=normal)

    Mevcut hiçbir baseline bu sinyallere bakmaz; gerçek dünyada ise
    bu iki durum ciddi finansal ve güvenlik sonuçları doğurur.

    Davranış:
      ┌─────────────────┬─────────────────────────────────────────────┐
      │ Durum           │ Eylem                                       │
      ├─────────────────┼─────────────────────────────────────────────┤
      │ Kesinti (grid=0)│ Deşarj etme — bataryayı acil rezerv olarak  │
      │                 │ tut. Ev kritik yükleri için koru.           │
      ├─────────────────┼─────────────────────────────────────────────┤
      │ DR sinyali=1    │ Şebekeden çekme → bataryadan karşıla.       │
      │                 │ Operatörün talep azaltma isteğine uy.       │
      ├─────────────────┼─────────────────────────────────────────────┤
      │ Normal          │ Standart threshold kuralı.                  │
      └─────────────────┴─────────────────────────────────────────────┘

    Parameters
    ----------
    emergency_reserve:
        Kesinti durumunda korunacak minimum SOC (varsayılan %40).
    low_pct / high_pct:
        Normal modda threshold eşikleri.
    """

    def __init__(
        self,
        emergency_reserve: float = 0.40,
        low_pct: float = 30.0,
        high_pct: float = 70.0,
    ) -> None:
        self.emergency_reserve = emergency_reserve
        self.low_pct = low_pct
        self.high_pct = high_pct

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        grid_available = int(obs[6])
        dr_signal      = int(obs[7])
        soc            = float(obs[0])

        # ── Kesinti modu ────────────────────────────────────────────
        if grid_available == 0:
            # Rezervin üstündeyse ev yükünü karşılamak için minimal deşarj
            if soc > self.emergency_reserve:
                return np.array([-0.3], dtype=np.float32)  # düşük güçte deşarj
            return np.array([0.0], dtype=np.float32)        # rezervi koru

        # ── Talep yanıtı modu ────────────────────────────────────────
        if dr_signal == 1:
            # Şebekeden çekme → bataryadan karşıla
            if soc > 0.20:
                return np.array([-1.0], dtype=np.float32)
            return np.array([0.0], dtype=np.float32)

        # ── Normal mod: standart threshold ──────────────────────────
        prices = obs[8:32]
        current_price = float(env._current_day_prices[env.t])
        low  = np.percentile(prices, self.low_pct)
        high = np.percentile(prices, self.high_pct)

        if current_price <= low:
            return np.array([1.0], dtype=np.float32)
        if current_price >= high:
            return np.array([-1.0], dtype=np.float32)
        return np.array([0.0], dtype=np.float32)

    def __repr__(self) -> str:
        return (
            f"GridAwarePolicy("
            f"acil_rezerv={self.emergency_reserve:.0%}, "
            f"kesinti+DR bilinçli)"
        )
