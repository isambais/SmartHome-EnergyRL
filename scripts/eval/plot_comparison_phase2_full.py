"""
Curriculum Aşama 2 — Tam politika karşılaştırması (kural tabanlı + RL).
30 günlük eval sonuçlarını çubuk grafik olarak çizer.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ── Veriler ───────────────────────────────────────────────────────────────────
policies = [
    "Bekle\n(Hold)",
    "Rastgele",
    "Eşik\n(Threshold)",
    "Öz-tüketim",
    "ToU\n(saat blok)",
    "Tahmin\nkullanır",
    "Tepe\nkesme",
    "Şebeke\nbilinçli",
    "PPO",
    "A2C",
    "SAC",
    "TD3",
]

means = [-1.74, -23.68, -2.57, -7.47, -15.95, -4.91, -9.95, -2.97,
         +7.11, +1.71, +12.92, +12.46]
stds  = [11.42,  17.89, 16.13, 18.77,  10.01, 16.60, 11.50, 16.30,
         11.91,  13.72, 13.09, 13.35]

# Renk: kural tabanlı → turuncu tonu, RL → yeşil tonu, rastgele → kırmızı
colors = [
    "#555555",  # Bekle
    "#c0392b",  # Rastgele
    "#e67e22",  # Eşik
    "#d35400",  # Öz-tüketim
    "#e74c3c",  # ToU
    "#e67e22",  # Tahmin
    "#d35400",  # Tepe kesme
    "#e67e22",  # Şebeke bilinçli
    "#2980b9",  # PPO
    "#8e44ad",  # A2C
    "#27ae60",  # SAC
    "#1e8449",  # TD3
]

# ── Çizim ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7), facecolor="#0d1117")
ax.set_facecolor("#0d1117")

x = np.arange(len(policies))
bars = ax.bar(x, means, color=colors, width=0.6,
              error_kw=dict(ecolor="white", capsize=5, linewidth=1.5),
              yerr=stds, capsize=5)

# Değer etiketleri
for bar, mean in zip(bars, means):
    va = "bottom" if mean >= 0 else "top"
    offset = 0.5 if mean >= 0 else -0.5
    ax.text(bar.get_x() + bar.get_width() / 2,
            mean + offset,
            f"{mean:+.2f} TL",
            ha="center", va=va, fontsize=8.5, color="white", fontweight="bold")

# Sıfır çizgisi
ax.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)

# Ayırıcı çizgi (kural tabanlı | RL)
ax.axvline(7.5, color="#888888", linewidth=1.2, linestyle=":", alpha=0.7)
ax.text(3.5, ax.get_ylim()[0] * 0.85 if ax.get_ylim()[0] < 0 else -28,
        "Kural Tabanlı Baseline'lar", ha="center", color="#aaaaaa", fontsize=9)
ax.text(9.5, ax.get_ylim()[0] * 0.85 if ax.get_ylim()[0] < 0 else -28,
        "RL Algoritmaları", ha="center", color="#aaaaaa", fontsize=9)

# Eksenler
ax.set_xticks(x)
ax.set_xticklabels(policies, color="white", fontsize=9)
ax.set_ylabel("Ortalama Günlük Kazanç (TL)", color="white", fontsize=11)
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_edgecolor("#444444")

# Başlık
ax.set_title(
    "Curriculum Aşama 2 — Kural Tabanlı + RL Tam Karşılaştırması\n"
    "Ortalama Günlük Ödül (TL) · 30 Gün · SmartHomeEnergyEnv",
    color="white", fontsize=12, fontweight="bold", pad=15
)

# Legend
legend_handles = [
    mpatches.Patch(color="#555555", label="Pasif baseline"),
    mpatches.Patch(color="#e67e22", label="Kural tabanlı"),
    mpatches.Patch(color="#2980b9", label="RL (PPO/A2C)"),
    mpatches.Patch(color="#27ae60", label="RL (SAC/TD3)"),
]
ax.legend(handles=legend_handles, loc="lower right",
          facecolor="#1a1a2e", edgecolor="#444444",
          labelcolor="white", fontsize=9)

plt.tight_layout()
out = Path("docs/policy_comparison_phase2_full.png")
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0d1117")
print(f"Kaydedildi: {out}")
