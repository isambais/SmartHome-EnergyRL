"""Sayfalar arası ortak durum ve sidebar bileşenleri."""

from __future__ import annotations

import datetime as dt

import numpy as np
import streamlit as st

from . import data as veri
from .agent import get_agent
from .config import BINA_TIPLERI, BinaConfig, saatlik_talep_kw, saatlik_gunes_kw
from .simulate import simulate_day


def init_state() -> None:
    if "cfg" not in st.session_state:
        st.session_state.cfg = BinaConfig.from_tip("Apartman")
    st.session_state.setdefault("saat", dt.datetime.now().hour)
    st.session_state.setdefault("uzman_modu", False)
    st.session_state.setdefault("epias_user", "")
    st.session_state.setdefault("epias_pass", "")


@st.cache_resource(show_spinner="RL ajanı yükleniyor…")
def cached_agent():
    return get_agent()


def sidebar_konfigurator() -> BinaConfig:
    """Sol sidebar — bina konfigüratörü. Yeni BinaConfig döndürür ve saklar."""
    cfg: BinaConfig = st.session_state.cfg
    with st.sidebar:
        st.header("🏗️ Bina Konfigüratörü")
        tip = st.selectbox("Bina tipi", list(BINA_TIPLERI), index=list(BINA_TIPLERI).index(cfg.bina_tipi))
        if tip != cfg.bina_tipi:
            cfg = BinaConfig.from_tip(tip)
            st.session_state.cfg = cfg

        kat = st.slider("Kat sayısı", 1, 10, cfg.kat)
        dpk = st.slider("Kat başına daire", 1, 4, cfg.daire_per_kat)
        toplam = kat * dpk
        aktif = st.slider("Aktif daire", 0, toplam, min(cfg.aktif_daire, toplam))
        oda = st.slider("Oda sayısı (daire başına)", 1, 6, cfg.oda)
        cati = st.number_input("Çatı alanı (m²)", 10.0, 1000.0, float(cfg.cati_alani), step=10.0)

        st.subheader("Sistemler")
        c1, c2 = st.columns(2)
        with c1:
            asansor = st.checkbox("🛗 Asansör", cfg.asansor)
            hvac = st.checkbox("❄️ HVAC", cfg.hvac)
            pompa = st.checkbox("💧 Su Pompası", cfg.su_pompasi)
            ev = st.checkbox("🚗 EV Şarj", cfg.ev_sarj)
        with c2:
            kamera = st.checkbox("📷 Kamera", cfg.kamera)
            isitici = st.checkbox("☀️ Güneş Isıtıcı", cfg.gunes_isitici)
            jen = st.checkbox("⛽ Jeneratör", cfg.jenerator)

        st.divider()
        st.session_state.saat = st.slider("🕐 Saat", 0, 23, st.session_state.saat)
        st.session_state.uzman_modu = st.toggle("📊 Uzman modu", st.session_state.uzman_modu)

    yeni = BinaConfig(bina_tipi=tip, kat=kat, daire_per_kat=dpk, aktif_daire=aktif,
                      oda=oda, cati_alani=cati, asansor=asansor, hvac=hvac,
                      su_pompasi=pompa, ev_sarj=ev, kamera=kamera,
                      gunes_isitici=isitici, jenerator=jen)
    st.session_state.cfg = yeni
    return yeni


def gunun_verisi(cfg: BinaConfig, tarih: dt.date | None = None):
    """(fiyat TL/MWh, güneş kW, talep kW, kaynak) — bina ölçeğinde 24'lük seriler."""
    tarih = tarih or dt.date.today()
    fiyat, kaynak = veri.gun_fiyati(tarih, st.session_state.epias_user, st.session_state.epias_pass)
    shape = veri.gunes_sekli(tarih.month)
    gunes = saatlik_gunes_kw(cfg, tarih.month, shape if shape.max() > 0 else None)
    talep = saatlik_talep_kw(cfg)
    return fiyat, gunes, talep, kaynak


def gunu_simule_et(cfg: BinaConfig, tarih: dt.date | None = None,
                   outage_hours: set[int] | None = None):
    """Tam gün simülasyonu; (df, kaynak, ajan_adı) döndürür."""
    tarih = tarih or dt.date.today()
    agent, _msg = cached_agent()
    fiyat, gunes, talep, kaynak = gunun_verisi(cfg, tarih)
    df = simulate_day(fiyat, gunes, talep, cfg.batarya_kwh, cfg.batarya_guc_kw,
                      agent, dow=tarih.weekday(), outage_hours=outage_hours,
                      jenerator=cfg.jenerator)
    return df, kaynak, agent.name
