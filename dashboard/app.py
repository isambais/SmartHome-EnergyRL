import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.theme import apply_theme
from core.ui import cached_agent, init_state

st.set_page_config(page_title="SmartHome Energy RL", page_icon="⚡", layout="wide")
apply_theme()
init_state()

st.title("⚡ SmartHome Energy RL — Bina Yönetim Sistemi")
st.markdown(
    "Güneş paneli, batarya ve akıllı sistemleri olan binanız için **yapay zekâ destekli "
    "enerji yönetimi**. Arka planda gerçek EPİAŞ fiyat verisiyle eğitilmiş bir RL ajanı "
    "(SAC) saat saat şarj/deşarj kararları verir — siz sadece binanızı tarif edin."
)

_, msg = cached_agent()
st.info(f"🤖 {msg}")

c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/1_🏠_Bina_Simulasyonu.py", label="🏠 **Bina Simülasyonu** — 3D bina, saatlik kararlar, öneriler")
    st.page_link("pages/2_⚡_Canli_EPIAS.py", label="⚡ **Canlı EPİAŞ** — bugünün fiyatları, kesinti senaryosu")
with c2:
    st.page_link("pages/3_💰_Yatirim_ve_Cevre.py", label="💰 **Yatırım & Çevre** — amorti süresi, CO₂ tasarrufu")
    st.page_link("pages/4_📊_Uzman_Modu.py", label="📊 **Uzman Modu** — algoritma karşılaştırmaları")

st.caption("Başlamak için soldaki menüden **Bina Simülasyonu** sayfasını açın.")
