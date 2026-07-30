"""Phase 3 TensorBoard callback — ertelenebilir yük metriklerini loglar.

SB3'ün varsayılan loglama mekanizması episode info'daki özel alanları otomatik
olarak TensorBoard'a yazmaz. Bu callback her episode sonunda:
  - device_activation_count  : gün içi toplam aktivasyon sayısı
  - device_activation_rate   : aktivasyon / saat (0-1)
  - deferrable_penalty_tl    : uygulanan ceza (0 veya 2.0)
  - device_used              : cihaz kullanıldı mı? (0/1)

değerlerini okuyup TensorBoard'a yazar.

Kullanım:
    from scripts.train.phase3_callback import Phase3MetricsCallback
    cb = Phase3MetricsCallback(verbose=0)
    model.learn(..., callback=[eval_callback, cb])
"""

from __future__ import annotations

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class Phase3MetricsCallback(BaseCallback):
    """Episode bitişinde Phase 3 ertelenebilir yük metriklerini loglar."""

    def __init__(self, verbose: int = 0) -> None:
        super().__init__(verbose)
        self._ep_activation_counts: list[float] = []
        self._ep_activation_rates: list[float] = []
        self._ep_penalties: list[float] = []
        self._ep_device_used: list[float] = []

    def _on_step(self) -> bool:
        # VecEnv: her ortam için info listesi gelir
        infos = self.locals.get("infos", [])
        for info in infos:
            ep = info.get("episode")          # EvalCallback / VecEnv episode bilgisi
            if ep is None:
                # SB3 VecEnv bazı durumlarda episode'u doğrudan info'ya koyar
                ep = info

            act_count = info.get("device_activation_count")
            act_rate  = info.get("device_activation_rate")
            penalty   = info.get("deferrable_penalty_tl", 0.0)

            # episode bitişinde VecEnv dicts'i flatten ettiğinden
            # bazıları sadece "episode" alt dict'te olabilir
            if act_count is None and isinstance(ep, dict):
                act_count = ep.get("device_activation_count")
                act_rate  = ep.get("device_activation_rate")

            if act_count is not None:
                self._ep_activation_counts.append(float(act_count))
                self._ep_activation_rates.append(float(act_rate or 0.0))
                self._ep_penalties.append(float(penalty))
                self._ep_device_used.append(1.0 if float(act_count) > 0 else 0.0)

        # Her 100 adımda bir toplu ortalamaları yaz
        if self.n_calls % 100 == 0 and self._ep_activation_counts:
            self.logger.record(
                "phase3/device_activation_count",
                float(np.mean(self._ep_activation_counts)),
            )
            self.logger.record(
                "phase3/device_activation_rate",
                float(np.mean(self._ep_activation_rates)),
            )
            self.logger.record(
                "phase3/deferrable_penalty_tl",
                float(np.mean(self._ep_penalties)),
            )
            self.logger.record(
                "phase3/device_used_ratio",
                float(np.mean(self._ep_device_used)),
            )
            self._ep_activation_counts.clear()
            self._ep_activation_rates.clear()
            self._ep_penalties.clear()
            self._ep_device_used.clear()

        return True
