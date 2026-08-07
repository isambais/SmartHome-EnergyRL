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

st.set_page_config(page_title="Bina Simülasyonu", page_icon="⚡", layout="wide")
apply_theme()
init_state()

cfg = sidebar_konfigurator()

# ── Sayfa başlığı ──
st.markdown("""
<style>
.page-title {
    font-size: 1.6rem; font-weight: 700; color: #0f172a;
    margin-bottom: 0.1rem; font-family: 'Inter', system-ui, sans-serif;
}
.page-sub {
    font-size: 0.9rem; color: #64748b; margin-bottom: 1.2rem;
    font-family: 'Inter', system-ui, sans-serif;
}
.step-bar {
    background: #f0fdf4; border-left: 3px solid #22c55e;
    border-radius: 6px; padding: 10px 16px;
    font-size: 0.85rem; color: #374151;
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1rem;
}
.decision-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px; border-radius: 10px;
    font-size: 1.05rem; font-weight: 700;
    font-family: 'Inter', system-ui, sans-serif;
    margin-bottom: 0.8rem;
}
.decision-sarj    { background: #dbeafe; color: #1d4ed8; border: 1.5px solid #93c5fd; }
.decision-desarj  { background: #fef2f2; color: #dc2626; border: 1.5px solid #fca5a5; }
.decision-bekle   { background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; }
.metric-label { font-size: 0.78rem; color: #64748b; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }
.metric-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; line-height: 1.1; }
.metric-delta { font-size: 0.8rem; margin-top: 4px; }
.metric-card  {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 18px 20px; height: 100%;
}
.saat-label {
    font-size: 0.82rem; font-weight: 600; color: #374151;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Bina Simülasyonu</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">SAC ajanı 24 saatlik EPİAŞ fiyatlarını değerlendirerek şarj/deşarj kararları üretir.</div>', unsafe_allow_html=True)

# ── Simülasyonu çalıştır ──
df, kaynak, ajan = gunu_simule_et(cfg)
saat = st.session_state.saat
r = df.iloc[saat]

# Adım rehberi
st.markdown(f"""
<div class="step-bar">
  <span>1. Soldan binanızı tanımlayın &nbsp;·&nbsp; 2. Saati kaydırarak günü gezin &nbsp;·&nbsp; 3. Bina ve sonuçlar anında güncellenir</span>
  <span style="color:#22c55e; font-weight:600">Otomatik hesaplanıyor — veri: {kaynak} · ajan: {ajan}</span>
</div>
""", unsafe_allow_html=True)

# ── Ana layout: 3D sol, metrikler + grafik sağ ──
col3d, colres = st.columns([1.1, 1])

with col3d:
    components.html(
        building_html(cfg, saat, float(r["soc"]), float(r["gunes_kw"])),
        height=500,
    )

    # Saat slider — binanın tam altında
    st.markdown('<div class="saat-label">Simülasyon saati</div>', unsafe_allow_html=True)
    yeni_saat = st.slider(
        label="saat_slider",
        min_value=0, max_value=23,
        value=saat,
        format="%d:00",
        label_visibility="collapsed",
    )
    if yeni_saat != saat:
        st.session_state.saat = yeni_saat
        st.rerun()

    st.caption(
        f"Panel: {cfg.panel_sayisi} adet ({cfg.panel_kw} kW)  ·  "
        f"Batarya: {cfg.batarya_kwh} kWh  ·  "
        f"Günlük tüketim: {cfg.gunluk_tuketim_kwh:.1f} kWh"
    )

with colres:
    # ── Ajan kararı — öne çıkarılmış ──
    karar = r["karar"]
    karar_map = {
        "şarj":   ("decision-sarj",   "Batarya şarj ediliyor",  "Ucuz saat — enerji depolanıyor"),
        "deşarj": ("decision-desarj", "Batarya deşarj ediliyor","Pahalı saat — depo kullanılıyor"),
        "bekle":  ("decision-bekle",  "Bekleniyor",             "Şarj/deşarj için uygun fiyat değil"),
    }
    cls, karar_baslik, karar_aciklama = karar_map.get(karar, ("decision-bekle", karar, ""))
    st.markdown(f"""
    <div class="decision-badge {cls}">
      <span style="font-size:1.2rem">{"▲" if karar=="şarj" else "▼" if karar=="deşarj" else "⏸"}</span>
      <div>
        <div>{karar_baslik}</div>
        <div style="font-size:0.78rem;font-weight:400;opacity:0.8">{karar_aciklama}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 metrik kart ──
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)

    taban = df["taban_maliyet_tl"].sum()
    tasarruf = df["tasarruf_tl"].sum()
    tasarruf_pct = int(100 * tasarruf / max(taban, 0.01))
    soc_pct = int(r["soc"] * 100)
    soc_renk = "#22c55e" if soc_pct > 50 else "#f59e0b" if soc_pct > 20 else "#ef4444"
    soc_durum = {"şarj": "şarj oluyor", "deşarj": "deşarj oluyor", "bekle": "hazırda bekliyor"}[karar]

    with m1:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Bugünkü tasarruf</div>
          <div class="metric-value" style="color:#15803d">{tasarruf:.0f} TL</div>
          <div class="metric-delta" style="color:#64748b">faturadan %{tasarruf_pct} azalma</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Batarya seviyesi</div>
          <div class="metric-value" style="color:{soc_renk}">%{soc_pct}</div>
          <div class="metric-delta" style="color:#64748b">{soc_durum}</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Güneş üretimi</div>
          <div class="metric-value">{r["gunes_kw"]:.1f} kW</div>
          <div class="metric-delta" style="color:#64748b">gün toplamı {df["gunes_kw"].sum():.0f} kWh</div>
        </div>""", unsafe_allow_html=True)

    with m4:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Anlık tüketim</div>
          <div class="metric-value">{r["talep_kw"]:.1f} kW</div>
          <div class="metric-delta" style="color:#64748b">gün toplamı {df["talep_kw"].sum():.0f} kWh</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 24 saatlik grafik ──
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df["saat"], y=df["gunes_kw"], name="Güneş (kW)",
        fill="tozeroy", line=dict(color="#f0883e", width=1.5),
        fillcolor="rgba(240,136,62,0.18)"), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=df["saat"], y=df["fiyat_tl_mwh"], name="Fiyat (TL/MWh)",
        line=dict(color="#e3b341", width=2.5)))
    fig.add_trace(go.Scatter(
        x=df["saat"], y=df["soc"] * 100, name="Batarya SOC (%)",
        line=dict(color="#22c55e", width=2.5)), secondary_y=True)

    sarj_df   = df[df["karar"] == "şarj"]
    desarj_df = df[df["karar"] == "deşarj"]
    fig.add_trace(go.Scatter(
        x=sarj_df["saat"], y=sarj_df["fiyat_tl_mwh"], mode="markers",
        name="Şarj kararı",
        marker=dict(symbol="triangle-up", size=12, color="#3b82f6")))
    fig.add_trace(go.Scatter(
        x=desarj_df["saat"], y=desarj_df["fiyat_tl_mwh"], mode="markers",
        name="Deşarj kararı",
        marker=dict(symbol="triangle-down", size=12, color="#ef4444")))

    # Şu anki saat çizgisi
    fig.add_vline(x=saat, line_dash="dash", line_color="#94a3b8",
                  annotation_text=f"{saat:02d}:00", annotation_position="top")

    fig.update_yaxes(title_text="TL/MWh", secondary_y=False)
    fig.update_yaxes(title_text="% / kW", secondary_y=True)
    fig.update_xaxes(title_text="Saat", dtick=2)
    st.plotly_chart(plotly_layout(fig, 320), use_container_width=True)

# ── Öneriler ──
st.divider()
st.markdown('<div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:0.6rem">Şu anki öneriler</div>', unsafe_allow_html=True)
cols_on = st.columns(2)
for i, o in enumerate(oneriler(df, saat)):
    with cols_on[i % 2]:
        st.markdown(f'<div class="oneri-kutu">{o}</div>', unsafe_allow_html=True)
