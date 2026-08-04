import datetime as dt
import sys
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.theme import apply_theme, plotly_layout
from core.threejs import building_html
from core.ui import init_state, gunu_simule_et, gunun_verisi

st.set_page_config(page_title="Canlı EPİAŞ", page_icon="⚡", layout="wide")
apply_theme()
init_state()
cfg = st.session_state.cfg

st.title("⚡ Canlı EPİAŞ — Gün Öncesi Piyasası")

with st.sidebar:
    st.header("🔌 EPİAŞ Bağlantısı")
    st.session_state.epias_user = st.text_input("Kullanıcı (e-posta)", st.session_state.epias_user)
    st.session_state.epias_pass = st.text_input("Şifre", st.session_state.epias_pass, type="password")
    st.caption("Boş bırakılırsa arşiv/sentetik veri kullanılır.")
    st.divider()
    otomatik = st.toggle("🔄 Saat başı otomatik yenile", False)

    st.divider()
    st.header("🚨 Kesinti Simülasyonu")
    kesinti = st.toggle("Elektrik kesintisi var", False)
    if kesinti:
        aralik = st.slider("Kesinti saatleri", 0, 23, (18, 21))
        kesinti_saatleri = set(range(aralik[0], aralik[1] + 1))
    else:
        kesinti_saatleri = set()

simdi = dt.datetime.now()
saat = simdi.hour

df, kaynak, ajan = gunu_simule_et(cfg, outage_hours=kesinti_saatleri)
r = df.iloc[saat]

st.markdown(f"**{simdi:%d.%m.%Y %H:%M}** · Veri kaynağı: `{kaynak}` · Ajan: `{ajan}`")

if kesinti:
    st.markdown(
        f'<div class="kesinti-uyari">🚨 KESİNTİ SİMÜLASYONU AKTİF ({min(kesinti_saatleri):02d}:00–'
        f'{max(kesinti_saatleri):02d}:00) — '
        + ("jeneratör devrede, batarya öncelikli kullanılıyor" if cfg.jenerator
           else "jeneratör YOK — yalnızca batarya + güneş!") + "</div>",
        unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Şu anki fiyat", f"{r['fiyat_tl_mwh']:.0f} TL/MWh",
          f"{r['fiyat_tl_mwh'] - df['fiyat_tl_mwh'].mean():+.0f} / ortalama")
m2.metric("Günün en ucuz saati", f"{int(df.loc[df['fiyat_tl_mwh'].idxmin(), 'saat']):02d}:00",
          f"{df['fiyat_tl_mwh'].min():.0f} TL/MWh")
m3.metric("Günün en pahalı saati", f"{int(df.loc[df['fiyat_tl_mwh'].idxmax(), 'saat']):02d}:00",
          f"{df['fiyat_tl_mwh'].max():.0f} TL/MWh")
m4.metric("Ajanın bugünkü tasarrufu", f"{df['tasarruf_tl'].sum():.0f} TL")

c1, c2 = st.columns([1.3, 1])

with c1:
    renkler = ["#f85149" if s in kesinti_saatleri else ("#e3b341" if s == saat else "#30363d")
               for s in df["saat"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["saat"], y=df["fiyat_tl_mwh"], marker_color=renkler,
                         name="PTF (TL/MWh)"))
    ikon = {"şarj": "🔼", "deşarj": "🔽", "bekle": ""}
    fig.add_trace(go.Scatter(
        x=df["saat"], y=df["fiyat_tl_mwh"] + df["fiyat_tl_mwh"].max() * 0.05,
        mode="text", text=[ikon[k] for k in df["karar"]], showlegend=False))
    fig.update_xaxes(title_text="Saat", dtick=1)
    fig.update_yaxes(title_text="TL/MWh")
    fig.update_layout(title="Bugünün gün öncesi fiyatları ve ajan kararları (🔼 şarj · 🔽 deşarj)")
    st.plotly_chart(plotly_layout(fig, 420), use_container_width=True)

    if kesinti:
        k = df[df["kesinti"]]
        st.markdown(
            f'<div class="oneri-kutu">🔋 Kesinti boyunca batarya + güneş <b>{(k["talep_kw"].sum() - k["karsilanmayan_kwh"].sum() - k["jenerator_kwh"].sum()):.1f} kWh</b> karşıladı'
            + (f' · ⛽ jeneratör <b>{k["jenerator_kwh"].sum():.1f} kWh</b> üretti (maliyet {k["maliyet_tl"].sum():.0f} TL)' if cfg.jenerator else
               (f' · ⚠️ <b>{k["karsilanmayan_kwh"].sum():.1f} kWh karşılanamadı</b>' if k["karsilanmayan_kwh"].sum() > 0.05 else " · tüm talep karşılandı ✓"))
            + "</div>", unsafe_allow_html=True)

with c2:
    components.html(
        building_html(cfg, saat, float(r["soc"]), float(r["gunes_kw"]),
                      outage=saat in kesinti_saatleri, height=420),
        height=430,
    )
    st.caption("Şu anki saat için bina durumu")

# Saatlik karar tablosu
with st.expander("📋 Saat saat karar tablosu"):
    goster = df[["saat", "fiyat_tl_mwh", "karar", "soc", "gunes_kw", "talep_kw", "net_maliyet_tl", "tasarruf_tl"]].copy()
    goster["soc"] = (goster["soc"] * 100).round(0).astype(int).astype(str) + "%"
    goster.columns = ["Saat", "Fiyat (TL/MWh)", "Karar", "Batarya", "Güneş (kW)", "Talep (kW)", "Maliyet (TL)", "Tasarruf (TL)"]
    st.dataframe(goster.round(1), use_container_width=True, hide_index=True)

if otomatik:
    time.sleep(3600 - simdi.minute * 60 - simdi.second + 5)
    st.rerun()
