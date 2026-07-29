"""Kural tabanlı (rule-based) baseline politikalar.

Tüm politikalar aynı Gymnasium arayüzüyle çalışır:

  HoldPolicy              — her zaman bekle (aksiyon = 0).
  ThresholdPolicy         — Aşama 1 (saf arbitraj): fiyat persantil eşiğine göre karar.
  SelfConsumptionPolicy   — Aşama 2 (güneş + talep): öz-tüketim öncelikli.
  ToUPolicy               — Saate göre sabit blok kararı (TEDAŞ T2 tarifesi modeli).
  ForecastAwarePolicy     — Yarınki tahmin fiyatını kullanan ileri görüşlü politika.
  PeakShavingPolicy       — Net şebeke çekişini bataryayla baskılayan tepe kesici.
  GridAwarePolicy         — Kesinti ve talep yanıtı sinyallerini değerlendiren politika.

Kullanım::

    from src.baselines.rule_based import ThresholdPolicy

    policy = ThresholdPolicy()
    action = policy(obs, env)   # Aşama 1/2: shape (1,) | Aşama 3: shape (2,)

    # Tüm politikalar aynı imzayı paylaşır:
    #   __call__(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray

Aşama 3 uyumluluğu:
    env.enable_deferrable=True olduğunda tüm politikalar otomatik olarak
    (2,) aksiyon döndürür. action[1] > 0 → cihazı çalıştır sinyali.
    Her politikanın _deferrable_signal() metodu kendi stratejisini uygular.

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
    [-1]    device_used_today (Aşama 3, enable_deferrable=True)
"""

from __future__ import annotations

import numpy as np

Policy = "Callable[[np.ndarray, Any], np.ndarray]"


def _make_action(battery: float, env, deferrable: float = -1.0) -> np.ndarray:
    """Ortama göre doğru boyutlu aksiyon dizisi üret.

    Parameters
    ----------
    battery:
        Batarya aksiyonu [-1, 1].
    env:
        SmartHomeEnergyEnv örneği.
    deferrable:
        Ertelenebilir yük sinyali (>0 = çalıştır, ≤0 = çalıştırma).
        Yalnızca env.enable_deferrable=True olduğunda kullanılır.
    """
    if getattr(env, "enable_deferrable", False):
        return np.array([battery, deferrable], dtype=np.float32)
    return np.array([battery], dtype=np.float32)


class HoldPolicy:
    """Her zaman bekle — 'batarya yok' senaryosunun davranışsal eşdeğeri.

    Batarya kapasitesi sıfır olarak ayarlanmış bir ortamla aynı sonucu
    üretir; ancak tek bir kod yolunda çalışır (ayrı ortam gerektirmez).

    Aşama 3: Cihazı hiçbir zaman çalıştırmaz (en kötü kural tabanlı baseline).
    """

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:  # noqa: ARG002
        return -1.0  # hiç çalıştırma

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        return _make_action(0.0, env, self._deferrable_signal(obs, env))

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

    Aşama 3: Fiyat düşükken cihazı çalıştır (ucuz elektrikle çalıştır).

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

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:
        """Fiyat alt persantildeyse cihazı çalıştır — ucuz elektrik fırsatı."""
        prices = obs[8:32]
        low = np.percentile(prices, self.low_pct)
        current_price = float(env._current_day_prices[env.t])
        return 1.0 if current_price <= low else -1.0

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        prices = obs[8:32]
        low = np.percentile(prices, self.low_pct)
        high = np.percentile(prices, self.high_pct)
        current_price = float(env._current_day_prices[env.t])

        if current_price <= low:
            battery = 1.0    # şarj
        elif current_price >= high:
            battery = -1.0   # deşarj
        else:
            battery = 0.0    # bekle

        return _make_action(battery, env, self._deferrable_signal(obs, env))

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

    Aşama 3: Güneş fazlası varken cihazı çalıştır — ücretsiz güneş enerjisi kullan.

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

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:
        """Güneş fazlası varken cihazı çalıştır — kendi ürettiğin enerjiyi kullan."""
        t = env.t
        solar_kw = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0
        solar_surplus = solar_kw - demand_kw
        return 1.0 if solar_surplus > self.solar_surplus_threshold else -1.0

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        prices = obs[8:32]
        low = np.percentile(prices, self.low_pct)
        high = np.percentile(prices, self.high_pct)
        current_price = float(env._current_day_prices[env.t])

        t = env.t
        solar_kw = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0
        solar_surplus = solar_kw - demand_kw
        soc = float(obs[0])

        if solar_surplus > self.solar_surplus_threshold:
            battery = 1.0    # güneş fazlası → şarj
        elif current_price >= high and soc > 0.15:
            battery = -1.0   # fiyat yüksek + batarya dolu → deşarj
        elif current_price <= low and soc < 0.90:
            battery = 1.0    # gece ucuz → şarj
        else:
            battery = 0.0    # bekle

        return _make_action(battery, env, self._deferrable_signal(obs, env))

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

    Aşama 3: Gündüz saatlerinde (pik dışı) cihazı çalıştır.

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
        self.peak_hours = peak_hours or [(17, 22)]
        self.off_peak_hours = off_peak_hours or [(23, 24), (0, 7)]

    def _current_hour(self, env) -> int:
        return int(env.t)

    def _in_blocks(self, hour: int, blocks: list[tuple[int, int]]) -> bool:
        return any(start <= hour < end for start, end in blocks)

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:  # noqa: ARG002
        """Pik saatler dışında cihazı çalıştır — tepe yükü artırma."""
        hour = self._current_hour(env)
        # Pik saatlerde çalıştırma; gündüz orta dilimde çalıştır
        if self._in_blocks(hour, self.peak_hours):
            return -1.0   # pik saatte cihazı çalıştırma
        if self._in_blocks(hour, self.off_peak_hours):
            return -1.0   # gece şarj var, cihazı karıştırma
        return 1.0        # gündüz orta dilim → çalıştır

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        hour = self._current_hour(env)

        if self._in_blocks(hour, self.peak_hours):
            battery = -1.0   # deşarj — pik tarife
        elif self._in_blocks(hour, self.off_peak_hours):
            battery = 1.0    # şarj — gece tarifesi
        else:
            battery = 0.0    # bekle — gündüz

        return _make_action(battery, env, self._deferrable_signal(obs, env))

    def __repr__(self) -> str:
        return f"ToUPolicy(pik={self.peak_hours}, gece={self.off_peak_hours})"


class ForecastAwarePolicy:
    """Yarınki fiyat tahminini kullanan ileri görüşlü politika.

    Mevcut threshold politikaları sadece bugünün 24 saatine bakar.
    Bu politika gözlemdeki yarınki tahmin verisini (obs[32:56]) de
    değerlendirerek daha iyi kararlar alır.

    Mantık:
      - Yarın bugünden belirgin ölçüde pahalıysa → Bugün agresif şarj et.
      - Yarın bugünden belirgin ölçüde ucuzsa → Bugün şarj etme.
      - Aksi hâlde standart threshold kuralını uygula.

    Aşama 3: Günün en ucuz çeyreğinde cihazı çalıştır.

    Parameters
    ----------
    low_pct / high_pct:
        Şarj / deşarj eşiği persantilleri.
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

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:
        """Günün en ucuz %25'lik dilimine denk geliyorsa cihazı çalıştır."""
        prices = obs[8:32]
        current_price = float(env._current_day_prices[env.t])
        cheapest_quartile = np.percentile(prices, 25)
        return 1.0 if current_price <= cheapest_quartile else -1.0

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        today_prices    = obs[8:32]
        tomorrow_prices = obs[32:56]

        today_mean    = float(np.mean(today_prices))
        tomorrow_mean = float(np.mean(tomorrow_prices))

        current_price = float(env._current_day_prices[env.t])
        low  = np.percentile(today_prices, self.low_pct)
        high = np.percentile(today_prices, self.high_pct)
        soc  = float(obs[0])

        if tomorrow_mean > today_mean * (1 + self.tomorrow_premium):
            if current_price <= np.percentile(today_prices, 50) and soc < 0.95:
                battery = 1.0
            else:
                battery = 0.0
        elif tomorrow_mean < today_mean * (1 - self.tomorrow_discount):
            if current_price >= high:
                battery = -1.0
            else:
                battery = 0.0
        elif current_price <= low:
            battery = 1.0
        elif current_price >= high:
            battery = -1.0
        else:
            battery = 0.0

        return _make_action(battery, env, self._deferrable_signal(obs, env))

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
    bataryadan karşılar, tepeyi kesar.

    Aşama 3: Tepe riski düşükken (net çekiş eşiğin yarısının altında) cihazı çalıştır.

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

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:
        """Net çekiş tepe eşiğinin yarısının altındaysa cihazı çalıştır — güvenli pencere."""
        t = env.t
        solar_kw  = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0
        net_grid_kw = max(0.0, demand_kw - solar_kw)
        # Net çekiş tepe eşiğinin yarısından düşükse cihazı çalıştır
        safe = net_grid_kw < self.peak_threshold_kw * 0.5
        return 1.0 if safe else -1.0

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        t = env.t
        soc = float(obs[0])

        solar_kw  = float(obs[56 + t]) if len(obs) > 80 else 0.0
        demand_kw = float(obs[80 + t]) if len(obs) > 80 else 0.0
        net_grid_kw = max(0.0, demand_kw - solar_kw)

        if net_grid_kw > self.peak_threshold_kw and soc > self.reserve_soc:
            battery = -1.0   # tepe aşımı → bataryadan karşıla
        else:
            prices = obs[8:32]
            current_price = float(env._current_day_prices[t])
            low = np.percentile(prices, self.low_pct)
            battery = 1.0 if current_price <= low and soc < 0.90 else 0.0

        return _make_action(battery, env, self._deferrable_signal(obs, env))

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

    Aşama 3: Kesinti veya DR aktifken cihazı çalıştırma; normal + ucuzsa çalıştır.

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

    def _deferrable_signal(self, obs: np.ndarray, env) -> float:
        """Kesinti/DR aktifken cihazı çalıştırma; normal + ucuz fiyatta çalıştır."""
        grid_available = int(obs[6])
        dr_signal      = int(obs[7])

        # Kesinti veya DR eventinde ek yük oluşturma
        if grid_available == 0 or dr_signal == 1:
            return -1.0

        # Normal modda ucuz fiyatta çalıştır
        prices = obs[8:32]
        current_price = float(env._current_day_prices[env.t])
        low = np.percentile(prices, self.low_pct)
        return 1.0 if current_price <= low else -1.0

    def __call__(self, obs: np.ndarray, env) -> np.ndarray:
        grid_available = int(obs[6])
        dr_signal      = int(obs[7])
        soc            = float(obs[0])

        if grid_available == 0:
            battery = -0.3 if soc > self.emergency_reserve else 0.0
        elif dr_signal == 1:
            battery = -1.0 if soc > 0.20 else 0.0
        else:
            prices = obs[8:32]
            current_price = float(env._current_day_prices[env.t])
            low  = np.percentile(prices, self.low_pct)
            high = np.percentile(prices, self.high_pct)
            if current_price <= low:
                battery = 1.0
            elif current_price >= high:
                battery = -1.0
            else:
                battery = 0.0

        return _make_action(battery, env, self._deferrable_signal(obs, env))

    def __repr__(self) -> str:
        return (
            f"GridAwarePolicy("
            f"acil_rezerv={self.emergency_reserve:.0%}, "
            f"kesinti+DR bilinçli)"
        )
