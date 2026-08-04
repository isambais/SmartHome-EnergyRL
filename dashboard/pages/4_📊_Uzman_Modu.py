import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import data as veri
from core.theme import apply_theme, plotly_layout
from core.ui import init_state

st.set_page_config(page_title="Uzman Modu", page_icon="📊", layout="wide")
apply_theme()
init_state()

ROOT = Path(__file__).resolve().parents[2]

st.title("📊 Uzman Modu")

with st.sidebar:
    st.session_state.uzman_modu = st.toggle("📊 Uzman modunu aç", st.session_state.uzman_modu)

if not st.session_state.uzman_modu:
    st.info("Bu sayfa teknik detaylar içerir. Görmek için soldaki **Uzman modunu aç** anahtarını etkinleştirin.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🤖 Algoritma Karşılaştırması", "🔮 Oracle / Forecast / Naive", "🌗 Mevsimsel Analiz"])

# ── Tab 1: Algoritmalar ──────────────────────────────────────────
with tab1:
    fk = ROOT / "logs" / "forecast_comparison.csv"
    if fk.exists():
        cmp_df = pd.read_csv(fk)
        rl = cmp_df[cmp_df["Politika"].isin(["SAC", "TD3", "PPO", "A2C"])]
        oracle = rl[rl["Mod"] == "Oracle"] if "Oracle" in rl["Mod"].values else rl

        fig = go.Figure()
        renk = {"SAC": "#3fb950", "TD3": "#58a6ff", "PPO": "#e3b341", "A2C": "#f0883e"}
        for _, r in oracle.iterrows():
            fig.add_trace(go.Bar(x=[r["Politika"]], y=[r["mean"]],
                                 error_y=dict(type="data", array=[r["std"]]),
                                 marker_color=renk.get(r["Politika"], "#8b949e"),
                                 name=r["Politika"]))
        fig.update_yaxes(title_text="Ortalama günlük ödül (TL)")
        fig.update_layout(title="RL algoritmaları — Oracle fiyat bilgisiyle günlük performans", showlegend=False)
        st.plotly_chart(plotly_layout(fig, 380), use_container_width=True)

        st.dataframe(rl.round(2), use_container_width=True, hide_index=True)
    else:
        st.warning("`logs/forecast_comparison.csv` bulunamadı.")

    fr = ROOT / "logs" / "forecast_results.csv"
    if fr.exists():
        st.subheader("Fiyat tahmin modelleri")
        st.dataframe(pd.read_csv(fr).round(2), use_container_width=True, hide_index=True)

# ── Tab 2: Pivot ─────────────────────────────────────────────────
with tab2:
    if fk.exists():
        pivot = cmp_df.pivot_table(index="Politika", columns="Mod", values="mean", aggfunc="mean")
        sirali_mod = [m for m in ["Oracle", "Forecast", "Naive"] if m in pivot.columns]
        if sirali_mod:
            pivot = pivot[sirali_mod]
        st.markdown("**Ortalama günlük ödül (TL)** — fiyat bilgisi kalitesine göre:")
        st.dataframe(pivot.round(2), use_container_width=True)

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale="RdYlGn", text=pivot.round(1).values,
            texttemplate="%{text}", colorbar=dict(title="TL")))
        fig.update_layout(title="Politika × Fiyat-bilgisi modu ısı haritası")
        st.plotly_chart(plotly_layout(fig, 420), use_container_width=True)

        st.caption(
            "**Oracle**: yarının gerçek fiyatını bilir · **Forecast**: LightGBM tahmini kullanır · "
            "**Naive**: bugünün fiyatını yarın için tahmin sayar.")
    else:
        st.warning("Karşılaştırma verisi yok.")

# ── Tab 3: Mevsimsel ─────────────────────────────────────────────
with tab3:
    df = veri.load_combined()
    df["ay"] = df["timestamp"].dt.month
    df["saat"] = df["timestamp"].dt.hour
    df["yil"] = df["timestamp"].dt.year

    aylik = df.groupby("ay")["price_tl_mwh"].mean()
    fig = go.Figure(go.Bar(x=list(range(1, 13)), y=[aylik.get(m, 0) for m in range(1, 13)],
                           marker_color=["#58a6ff" if m in (12, 1, 2) else
                                         "#3fb950" if m in (3, 4, 5) else
                                         "#e3b341" if m in (6, 7, 8) else "#f0883e"
                                         for m in range(1, 13)]))
    fig.update_xaxes(title_text="Ay", dtick=1)
    fig.update_yaxes(title_text="Ortalama PTF (TL/MWh)")
    fig.update_layout(title=f"Aylık ortalama fiyat ({df['yil'].min()}–{df['yil'].max()})")
    st.plotly_chart(plotly_layout(fig, 360), use_container_width=True)

    c1, c2 = st.columns(2)
    yaz = df[df["ay"].isin([6, 7, 8])].groupby("saat")["price_tl_mwh"].mean()
    kis = df[df["ay"].isin([12, 1, 2])].groupby("saat")["price_tl_mwh"].mean()
    with c1:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=yaz.index, y=yaz.values, name="Yaz", line=dict(color="#e3b341", width=3)))
        fig2.add_trace(go.Scatter(x=kis.index, y=kis.values, name="Kış", line=dict(color="#58a6ff", width=3)))
        fig2.update_xaxes(title_text="Saat", dtick=2)
        fig2.update_yaxes(title_text="TL/MWh")
        fig2.update_layout(title="Yaz vs Kış — günlük fiyat profili")
        st.plotly_chart(plotly_layout(fig2, 360), use_container_width=True)
    with c2:
        al = veri.load_aligned()
        al["ay"] = al["timestamp"].dt.month
        al["saat"] = al["timestamp"].dt.hour
        gy = al[al["ay"].isin([6, 7, 8])].groupby("saat")["solar_kw"].mean()
        gk = al[al["ay"].isin([12, 1, 2])].groupby("saat")["solar_kw"].mean()
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=gy.index, y=gy.values, name="Yaz", fill="tozeroy", line=dict(color="#f0883e")))
        fig3.add_trace(go.Scatter(x=gk.index, y=gk.values, name="Kış", fill="tozeroy", line=dict(color="#58a6ff")))
        fig3.update_xaxes(title_text="Saat", dtick=2)
        fig3.update_yaxes(title_text="kW (4 kW referans sistem)")
        fig3.update_layout(title="Yaz vs Kış — güneş üretim profili")
        st.plotly_chart(plotly_layout(fig3, 360), use_container_width=True)

    st.markdown(
        f'<div class="oneri-kutu">💡 Yazın fiyat tepesi öğleden sonraya (klima yükü), kışın akşama kayar. '
        f'Yaz güneş üretimi kışın yaklaşık <b>{(gy.sum() / max(gk.sum(), 0.1)):.1f} katı</b> — '
        f'ajan yazın öz-tüketim, kışın fiyat arbitrajı ağırlıklı çalışır.</div>',
        unsafe_allow_html=True)
