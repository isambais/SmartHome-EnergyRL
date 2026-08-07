import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.simulate import oneriler
from core.theme import apply_theme, plotly_layout
from core.threejs import building_html
from core.ui import init_state, sidebar_konfigurator, gunu_simule_et

st.set_page_config(page_title="Bina Simülasyonu", page_icon="🏠", layout="wide")
apply_theme()
init_state()

cfg = sidebar_konfigurator()
saat = st.session_state.saat

st.title("🏠 Bina Simülasyonu")

df, kaynak, ajan = gunu_simule_et(cfg)
r = df.iloc[saat]

col3d, colres = st.columns([1.05, 1])

with col3d:
    components.html(
        building_html(cfg, saat, float(r["soc"]), float(r["gunes_kw"])),
        height=530,
    )
    st.caption(
        f"🖱️ Sürükle: döndür · Tekerlek: yakınlaştır — Panel: **{cfg.panel_sayisi} adet "
        f"({cfg.panel_kw} kW)** · Batarya: **{cfg.batarya_kwh} kWh** · "
        f"Günlük tüketim: **{cfg.gunluk_tuketim_kwh:.1f} kWh** · Veri: {kaynak} · Ajan: {ajan}"
    )

with colres:
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)
    m1.metric("💰 Bugünkü tasarruf", f"{df['tasarruf_tl'].sum():.0f} TL",
              f"%{100*df['tasarruf_tl'].sum()/max(df['taban_maliyet_tl'].sum(),0.01):.0f} daha az fatura")
    m2.metric("🔋 Batarya seviyesi", f"%{r['soc']*100:.0f}",
              {"şarj": "şarj oluyor", "deşarj": "deşarj oluyor", "bekle": "beklemede"}[r["karar"]])
    m3.metric("☀️ Güneş üretimi", f"{r['gunes_kw']:.1f} kW",
              f"gün toplamı {df['gunes_kw'].sum():.0f} kWh")
    m4.metric("🏠 Toplam tüketim", f"{df['talep_kw'].sum():.0f} kWh",
              f"şu an {r['talep_kw']:.1f} kW")

    # ── 24 saatlik grafik ──
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df["saat"], y=df["gunes_kw"], name="Güneş (kW)",
                             fill="tozeroy", line=dict(color="#f0883e", width=1),
                             fillcolor="rgba(240,136,62,0.25)"), secondary_y=True)
    fig.add_trace(go.Scatter(x=df["saat"], y=df["fiyat_tl_mwh"], name="Fiyat (TL/MWh)",
                             line=dict(color="#e3b341", width=2.5)))
    fig.add_trace(go.Scatter(x=df["saat"], y=df["soc"] * 100, name="Batarya SOC (%)",
                             line=dict(color="#3fb950", width=2.5)), secondary_y=True)
    sarj = df[df["karar"] == "şarj"]
    desarj = df[df["karar"] == "deşarj"]
    fig.add_trace(go.Scatter(x=sarj["saat"], y=sarj["fiyat_tl_mwh"], mode="markers",
                             name="Şarj kararı", marker=dict(symbol="triangle-up", size=13, color="#58a6ff")))
    fig.add_trace(go.Scatter(x=desarj["saat"], y=desarj["fiyat_tl_mwh"], mode="markers",
                             name="Deşarj kararı", marker=dict(symbol="triangle-down", size=13, color="#f85149")))
    fig.add_vline(x=saat, line_dash="dash", line_color="#8b949e")
    fig.update_yaxes(title_text="TL/MWh", secondary_y=False)
    fig.update_yaxes(title_text="% / kW", secondary_y=True)
    fig.update_xaxes(title_text="Saat", dtick=2)
    st.plotly_chart(plotly_layout(fig, 360), use_container_width=True)

# ── Öneri kutusu ──
st.subheader("💡 Şu anki öneriler")
for o in oneriler(df, saat):
    st.markdown(f'<div class="oneri-kutu">{o}</div>', unsafe_allow_html=True)
