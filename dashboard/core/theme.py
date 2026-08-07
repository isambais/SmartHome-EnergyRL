"""Ortak tema: CSS, Plotly şablonu, metrik kartlar."""

from __future__ import annotations

import streamlit as st

BG = "#0d1117"
CARD = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"

CSS = f"""
<style>
.stApp {{ background-color: {BG}; }}
section[data-testid="stSidebar"] {{ background-color: {CARD}; border-right: 1px solid {BORDER}; }}
div[data-testid="stMetric"] {{
  background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
  padding: 14px 16px;
}}
div[data-testid="stMetric"] label {{ color: {MUTED}; }}
.oneri-kutu {{
  background: {CARD}; border: 1px solid {BORDER}; border-left: 4px solid #58a6ff;
  border-radius: 8px; padding: 12px 16px; margin: 6px 0; color: {TEXT};
  font-size: 1.02rem;
}}
.kesinti-uyari {{
  background: #3d1418; border: 1px solid #f85149; border-radius: 8px;
  padding: 12px 16px; color: #ff7b72; font-weight: 700;
  animation: yanip 1s infinite alternate;
}}
@keyframes yanip {{ from {{ opacity: 1; }} to {{ opacity: 0.55; }} }}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def plotly_layout(fig, height: int = 420):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG, plot_bgcolor=CARD,
        height=height, margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", y=1.12, x=0),
        font=dict(color=TEXT),
    )
    return fig
