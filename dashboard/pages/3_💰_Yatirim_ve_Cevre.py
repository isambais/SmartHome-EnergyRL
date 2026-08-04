import datetime as dt
import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.theme import apply_theme, plotly_layout
from core.ui import init_state, gunu_simule_et

st.set_page_config(page_title="Yatırım & Çevre", page_icon="💰", layout="wide")
apply_theme()
init_state()
cfg = st.session_state.cfg

st.title("💰 Yatırım & Çevre Analizi")

with st.sidebar:
    st.header("💸 Yatırım Maliyetleri")
    batarya_tl = st.number_input("Batarya maliyeti (TL)", 0.0, 5_000_000.0,
                                 float(cfg.batarya_kwh * 12_000), step=10_000.0,
                                 help=f"Öneri: {cfg.batarya_kwh} kWh × ~12.000 TL/kWh")
    panel_tl = st.number_input("Panel maliyeti (TL)", 0.0, 5_000_000.0,
                               float(cfg.panel_sayisi * 6_500), step=10_000.0,
                               help=f"Öneri: {cfg.panel_sayisi} panel × ~6.500 TL")
toplam_yatirim = batarya_tl + panel_tl


@st.cache_data(show_spinner="Mevsimsel simülasyon çalışıyor…")
def yillik_tahmin(_cfg_key: str) -> tuple[float, float]:
    """4 mevsim temsilci günü simüle edip yıllık tasarruf ve güneş üretimi tahmini."""
    tasarruflar, uretimler = [], []
    yil = dt.date.today().year
    for ay in (1, 4, 7, 10):
        try:
            gun = dt.date(yil, ay, 15)
            df, _, _ = gunu_simule_et(st.session_state.cfg, tarih=gun)
            tasarruflar.append(df["tasarruf_tl"].sum())
            uretimler.append(df["gunes_kw"].sum())
        except Exception:
            pass
    return float(np.mean(tasarruflar) * 365), float(np.mean(uretimler) * 365)


cfg_key = str(cfg) + str(dt.date.today())
yillik_tasarruf, yillik_uretim_kwh = yillik_tahmin(cfg_key)
amorti = toplam_yatirim / max(yillik_tasarruf, 1.0)

# ── Çevre ──
CO2_G_PER_KWH = 450.0          # Türkiye şebeke emisyon faktörü
AGAC_KG_YIL = 25.0             # bir ağacın yıllık CO₂ tutumu
ARABA_TON_YIL = 2.0            # ortalama binek aracın yıllık emisyonu
co2_ton = yillik_uretim_kwh * CO2_G_PER_KWH / 1e6
agac = co2_ton * 1000 / AGAC_KG_YIL
araba = co2_ton / ARABA_TON_YIL

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam yatırım", f"{toplam_yatirim:,.0f} TL")
m2.metric("Yıllık tasarruf", f"{yillik_tasarruf:,.0f} TL")
m3.metric("Amorti süresi", f"{amorti:.1f} yıl")
m4.metric("Yıllık CO₂ tasarrufu", f"{co2_ton:.1f} ton")

st.markdown(
    f'<div class="oneri-kutu">🌍 Sisteminiz <b>{amorti:.1f} yılda</b> kendini amorti ediyor; '
    f'yılda <b>{agac:.0f} ağacın</b> tuttuğu kadar CO₂ tasarrufu sağlıyor — bu '
    f'<b>{araba:.1f} arabanın</b> yıllık emisyonuna eşit.</div>',
    unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    yillar = np.arange(0, max(int(np.ceil(amorti)) + 6, 10))
    kumulatif = yillar * yillik_tasarruf
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=yillar, y=kumulatif, name="Kümülatif tasarruf",
                             line=dict(color="#3fb950", width=3), fill="tozeroy",
                             fillcolor="rgba(63,185,80,0.15)"))
    fig.add_hline(y=toplam_yatirim, line_dash="dash", line_color="#e3b341",
                  annotation_text=f"Yatırım: {toplam_yatirim:,.0f} TL")
    fig.add_vline(x=amorti, line_dash="dot", line_color="#58a6ff",
                  annotation_text=f"Amorti: {amorti:.1f} yıl")
    fig.update_xaxes(title_text="Yıl")
    fig.update_yaxes(title_text="TL")
    fig.update_layout(title="Amorti süresi — kümülatif tasarruf vs yatırım")
    st.plotly_chart(plotly_layout(fig, 400), use_container_width=True)

with c2:
    artislar = np.arange(0, 55, 5)
    amortiler = toplam_yatirim / (yillik_tasarruf * (1 + artislar / 100))
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=artislar, y=amortiler, line=dict(color="#f0883e", width=3),
                              mode="lines+markers", name="Amorti süresi"))
    fig2.update_xaxes(title_text="Elektrik fiyat artışı (%)")
    fig2.update_yaxes(title_text="Amorti (yıl)")
    fig2.update_layout(title="Fiyat duyarlılık analizi")
    st.plotly_chart(plotly_layout(fig2, 400), use_container_width=True)
    kisalma = amorti - toplam_yatirim / (yillik_tasarruf * 1.3)
    st.markdown(
        f'<div class="oneri-kutu">📈 Elektrik fiyatları <b>%30 artarsa</b> amorti süresi '
        f'<b>{kisalma:.1f} yıl kısalarak {amorti - kisalma:.1f} yıla</b> iner.</div>',
        unsafe_allow_html=True)
