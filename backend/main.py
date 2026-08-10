"""FastAPI backend — React frontend için API katmanı.

Çalıştırma (proje kökünden):
    uvicorn backend.main:app --reload --port 8000

dashboard/core'daki simülasyon/ajan/3D kodunu yeniden kullanır.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))

from dashboard.core.agent import get_agent, load_algo  # noqa: E402
from dashboard.core.config import (  # noqa: E402
    BINA_TIPLERI, BinaConfig, saatlik_gunes_kw, saatlik_talep_kw,
)
from dashboard.core.simulate import SICAKLIK_VERIM, VERIM, oneriler_kodlu, simulate_day  # noqa: E402
from dashboard.core.threejs import building_html  # noqa: E402

from fastapi import Depends  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend import data as veri  # noqa: E402
from backend.auth import (  # noqa: E402
    current_user, dogrula_sifre, hash_sifre, token_olustur,
)
from backend.db import get_db, init_db  # noqa: E402
from backend.models import SimKaydi, User  # noqa: E402

# EPİAŞ hesap bilgileri — sunucu tarafında ortam değişkeninden okunur.
# .env dosyası varsa yüklemeye çalış (python-dotenv kuruluysa).
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(ROOT / ".env")
except Exception:
    pass

EPIAS_USER = os.environ.get("EPIAS_USER", "")
EPIAS_PASS = os.environ.get("EPIAS_PASS", "")

from fastapi.openapi.models import HTTPBase as HTTPBaseModel  # noqa: E402
from fastapi.security import HTTPBearer  # noqa: E402

security = HTTPBearer()

app = FastAPI(
    title="SmartHome Energy RL API",
    swagger_ui_parameters={"persistAuthorization": True},
)
_FRONTEND_URL = os.environ.get("FRONTEND_URL", "")
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    *([_FRONTEND_URL] if _FRONTEND_URL else []),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Basit sonuç önbelleği (sunucu çalışırken geçerli) ────────────
import json as _json  # noqa: E402

_CACHE: dict = {}


def _cache_key(*parts) -> str:
    return _json.dumps(parts, default=str, sort_keys=True)


@app.on_event("startup")
def _startup():
    init_db()
    # Ağır bağımlılıkları önceden yükle: ilk sayfa açılışı hızlı olsun
    try:
        cached_agent()                 # RL modeli / torch importu
        veri.load_combined()           # EPİAŞ arşiv CSV
        veri.load_aligned()            # PVWatts / talep CSV
    except Exception:
        pass


# ── Modeller ─────────────────────────────────────────────────────
class BinaIn(BaseModel):
    bina_tipi: str = "Apartman"
    kat: int = 5
    daire_per_kat: int = 3
    aktif_daire: int = 12
    oda: int = 3
    cati_alani: float = 140.0
    asansor: bool = True
    hvac: bool = False
    su_pompasi: bool = True
    ev_sarj: bool = True
    kamera: bool = True
    gunes_isitici: bool = False
    jenerator: bool = True

    def to_cfg(self) -> BinaConfig:
        return BinaConfig(**self.model_dump())


class SimIn(BaseModel):
    config: BinaIn = Field(default_factory=BinaIn)
    tarih: str | None = None            # "YYYY-MM-DD"
    kesinti_saatleri: list[int] = []
    algo: str | None = None             # sac | td3 | ppo | a2c | None → varsayılan


class YatirimIn(BaseModel):
    config: BinaIn = Field(default_factory=BinaIn)
    batarya_tl: float | None = None
    panel_tl: float | None = None


class BuildingIn(BaseModel):
    config: BinaIn = Field(default_factory=BinaIn)
    saat: int = 12
    soc: float = 0.5
    gunes_kw: float = 0.0
    kesinti: bool = False
    height: int = 500
    dil: str = "tr"


# 3D HUD'daki "daire" etiketi — dile göre
_UNIT_LABEL = {"tr": "daire", "en": "flats", "ar": "وحدة"}


# ── Auth / profil istek modelleri ────────────────────────────────
class KayitIn(BaseModel):
    ad: str = Field(default="", max_length=120)
    email: str = Field(max_length=255)
    sifre: str = Field(min_length=4, max_length=128)


class GirisIn(BaseModel):
    email: str
    sifre: str


class SifreIn(BaseModel):
    eski: str
    yeni: str


class SimKaydiIn(BaseModel):
    bina_tipi: str = ""
    tasarruf_tl: float = 0.0
    gunes_kwh: float = 0.0
    not_: str = ""


def _user_json(u: User) -> dict:
    return {"id": u.id, "ad": u.ad, "email": u.email,
            "bina": u.bina, "created_at": u.created_at.isoformat()}


# ── Ajan önbelleği ───────────────────────────────────────────────
@lru_cache(maxsize=4)
def cached_agent(algo: str | None = None):
    if algo:
        try:
            ag = load_algo(algo)
            return ag, f"{algo.upper()} ajanı yüklendi"
        except Exception as e:
            return get_agent()[0], f"{algo.upper()} yüklenemedi ({type(e).__name__}), varsayılan ajan"
    return get_agent()


def _derived(cfg: BinaConfig) -> dict:
    return dict(
        toplam_daire=cfg.toplam_daire,
        gunluk_tuketim_kwh=round(cfg.gunluk_tuketim_kwh, 1),
        panel_sayisi=cfg.panel_sayisi,
        panel_kw=cfg.panel_kw,
        batarya_kwh=cfg.batarya_kwh,
        batarya_guc_kw=cfg.batarya_guc_kw,
    )


def _simulate(inp: SimIn):
    tarih = dt.date.fromisoformat(inp.tarih) if inp.tarih else dt.date.today()
    agent, ajan_msg = cached_agent(inp.algo.lower() if inp.algo else None)
    cfg = inp.config.to_cfg()

    fiyat, kaynak = veri.gun_fiyati(tarih, EPIAS_USER, EPIAS_PASS)
    shape = veri.gunes_sekli(tarih.month)
    gunes = saatlik_gunes_kw(cfg, tarih.month, shape if shape.max() > 0 else None)
    talep = saatlik_talep_kw(cfg)

    df = simulate_day(fiyat, gunes, talep, cfg.batarya_kwh, cfg.batarya_guc_kw,
                      agent, dow=tarih.weekday(),
                      outage_hours=set(inp.kesinti_saatleri) or None,
                      jenerator=cfg.jenerator, ay=tarih.month)
    return df, kaynak, agent, ajan_msg, cfg, tarih


# ── Endpoint'ler ─────────────────────────────────────────────────
@app.get("/api/bina-tipleri")
def bina_tipleri():
    return {tip: dict(bina_tipi=tip, **vals) for tip, vals in BINA_TIPLERI.items()}


@app.post("/api/simulate")
def simulate(inp: SimIn):
    key = _cache_key("sim", inp.model_dump())
    if key in _CACHE:
        return _CACHE[key]
    df, kaynak, agent, _msg, cfg, tarih = _simulate(inp)
    sonuc = {
        "kaynak": kaynak,
        "ajan": agent.name,
        "tarih": tarih.isoformat(),
        "batarya_verim_pct": round(VERIM * SICAKLIK_VERIM[tarih.month - 1] * 100, 1),
        "derived": _derived(cfg),
        "rows": df.round(4).to_dict(orient="records"),
        "oneriler": [oneriler_kodlu(df, h) for h in range(24)],
        "ozet": {
            "tasarruf_tl": round(float(df["tasarruf_tl"].sum()), 1),
            "taban_maliyet_tl": round(float(df["taban_maliyet_tl"].sum()), 1),
            "net_maliyet_tl": round(float(df["net_maliyet_tl"].sum()), 1),
            "gunes_kwh": round(float(df["gunes_kw"].sum()), 1),
            "talep_kwh": round(float(df["talep_kw"].sum()), 1),
        },
    }
    _CACHE[key] = sonuc
    return sonuc


@app.post("/api/building-html", response_class=HTMLResponse)
def building(inp: BuildingIn):
    return building_html(inp.config.to_cfg(), inp.saat, inp.soc, inp.gunes_kw,
                         outage=inp.kesinti, height=inp.height,
                         unit_label=_UNIT_LABEL.get(inp.dil, _UNIT_LABEL["tr"]))


@app.post("/api/yatirim")
def yatirim(inp: YatirimIn):
    key = _cache_key("yatirim", inp.model_dump())
    if key in _CACHE:
        return _CACHE[key]
    cfg = inp.config.to_cfg()
    batarya_tl = inp.batarya_tl if inp.batarya_tl else cfg.batarya_kwh * 12_000
    panel_tl = inp.panel_tl if inp.panel_tl else cfg.panel_sayisi * 6_500
    toplam = batarya_tl + panel_tl

    # 12 ayın her biri için temsilci gün simüle et — paralel
    from concurrent.futures import ThreadPoolExecutor  # noqa: E402
    AY_GUN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    yil = dt.date.today().year

    def _ay_simule(ay_no):
        try:
            sim = SimIn(config=inp.config, tarih=dt.date(yil, ay_no, 15).isoformat())
            df, _, _, _, _, _ = _simulate(sim)
            return {
                "ay": ay_no,
                "tasarruf": round(float(df["tasarruf_tl"].sum()) * AY_GUN[ay_no - 1], 0),
                "uretim_kwh": round(float(df["gunes_kw"].sum()) * AY_GUN[ay_no - 1], 0),
                "batarya_verim": round(VERIM * SICAKLIK_VERIM[ay_no - 1] * 100, 1),
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=6) as ex:
        aylik = [r for r in ex.map(_ay_simule, range(1, 13)) if r]

    yillik_tasarruf = float(sum(a["tasarruf"] for a in aylik)) if aylik else 1.0
    yillik_uretim = float(sum(a["uretim_kwh"] for a in aylik)) if aylik else 0.0
    amorti = toplam / max(yillik_tasarruf, 1.0)

    co2_ton = yillik_uretim * 450.0 / 1e6
    artislar = list(range(0, 55, 5))
    sonuc = {
        "varsayilan_batarya_tl": round(cfg.batarya_kwh * 12_000),
        "varsayilan_panel_tl": round(cfg.panel_sayisi * 6_500),
        "toplam_yatirim": round(toplam),
        "yillik_tasarruf": round(yillik_tasarruf),
        "yillik_uretim_kwh": round(yillik_uretim),
        "amorti_yil": round(amorti, 1),
        "co2_ton": round(co2_ton, 1),
        "agac": round(co2_ton * 1000 / 25.0),
        "araba": round(co2_ton / 2.0, 1),
        "aylik": aylik,
        "duyarlilik": [
            {"artis": a, "amorti": round(toplam / (yillik_tasarruf * (1 + a / 100)), 1)}
            for a in artislar
        ],
    }
    _CACHE[key] = sonuc
    return sonuc


@app.get("/api/uzman/karsilastirma")
def karsilastirma():
    if "karsilastirma" in _CACHE:
        return _CACHE["karsilastirma"]
    out = {"algoritmalar": [], "forecast": [], "pivot": []}
    fk = ROOT / "logs" / "forecast_comparison.csv"
    if fk.exists():
        cmp_df = pd.read_csv(fk)
        rl = cmp_df[cmp_df["Politika"].isin(["SAC", "TD3", "PPO", "A2C"])]
        out["algoritmalar"] = rl.round(2).to_dict(orient="records")
        pivot = cmp_df.pivot_table(index="Politika", columns="Mod", values="mean", aggfunc="mean")
        out["pivot"] = pivot.round(2).reset_index().to_dict(orient="records")
    fr = ROOT / "logs" / "forecast_results.csv"
    if fr.exists():
        out["forecast"] = pd.read_csv(fr).round(2).to_dict(orient="records")
    _CACHE["karsilastirma"] = out
    return out


@app.get("/api/uzman/mevsimsel")
def mevsimsel():
    if "mevsimsel" in _CACHE:
        return _CACHE["mevsimsel"]
    df = veri.load_combined().copy()
    df["ay"] = df["timestamp"].dt.month
    df["saat"] = df["timestamp"].dt.hour

    aylik = df.groupby("ay")["price_tl_mwh"].mean()
    yaz = df[df["ay"].isin([6, 7, 8])].groupby("saat")["price_tl_mwh"].mean()
    kis = df[df["ay"].isin([12, 1, 2])].groupby("saat")["price_tl_mwh"].mean()

    al = veri.load_aligned().copy()
    al["ay"] = al["timestamp"].dt.month
    al["saat"] = al["timestamp"].dt.hour
    gy = al[al["ay"].isin([6, 7, 8])].groupby("saat")["solar_kw"].mean()
    gk = al[al["ay"].isin([12, 1, 2])].groupby("saat")["solar_kw"].mean()

    return {
        "yil_araligi": [int(df["timestamp"].dt.year.min()), int(df["timestamp"].dt.year.max())],
        "aylik_fiyat": [round(float(aylik.get(m, 0)), 1) for m in range(1, 13)],
        "saatlik": [
            {
                "saat": h,
                "yaz_fiyat": round(float(yaz.get(h, 0)), 1),
                "kis_fiyat": round(float(kis.get(h, 0)), 1),
                "yaz_gunes": round(float(gy.get(h, 0)), 3),
                "kis_gunes": round(float(gk.get(h, 0)), 3),
            }
            for h in range(24)
        ],
        "gunes_orani": round(float(gy.sum() / max(gk.sum(), 0.1)), 1),
    }


# ── Kimlik doğrulama ─────────────────────────────────────────────
@app.post("/api/register")
def register(inp: KayitIn, db: Session = Depends(get_db)):
    email = inp.email.strip().lower()
    if not email or not inp.sifre:
        raise HTTPException(status_code=400, detail="E-posta ve şifre gerekli")
    if len(inp.sifre) < 4:
        raise HTTPException(status_code=400, detail="Şifre en az 4 karakter olmalı")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı — giriş yapın")
    user = User(ad=inp.ad.strip() or "Kullanıcı", email=email, sifre_hash=hash_sifre(inp.sifre))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": token_olustur(user.id), "user": _user_json(user)}


@app.post("/api/login")
def login(inp: GirisIn, db: Session = Depends(get_db)):
    email = inp.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not dogrula_sifre(inp.sifre, user.sifre_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    return {"token": token_olustur(user.id), "user": _user_json(user)}


# ── Profil ───────────────────────────────────────────────────────
@app.get("/api/profile")
def profile(user: User = Depends(current_user)):
    return {
        "user": _user_json(user),
        "gecmis": [
            {"id": g.id, "tarih": g.tarih.isoformat(), "bina_tipi": g.bina_tipi,
             "tasarruf_tl": g.tasarruf_tl, "gunes_kwh": g.gunes_kwh, "not_": g.not_}
            for g in user.gecmis
        ],
    }


@app.put("/api/profile/bina")
def profil_bina_kaydet(bina: BinaIn, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    user.bina = bina.model_dump()
    db.commit()
    return {"ok": True, "bina": user.bina}


@app.post("/api/profile/gecmis")
def profil_gecmis_ekle(inp: SimKaydiIn, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    kayit = SimKaydi(user_id=user.id, bina_tipi=inp.bina_tipi,
                     tasarruf_tl=inp.tasarruf_tl, gunes_kwh=inp.gunes_kwh, not_=inp.not_)
    db.add(kayit)
    db.commit()
    db.refresh(kayit)
    return {"ok": True, "id": kayit.id}


@app.put("/api/profile/sifre")
def profil_sifre_degistir(inp: SifreIn, user: User = Depends(current_user),
                          db: Session = Depends(get_db)):
    if not dogrula_sifre(inp.eski, user.sifre_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı")
    if len(inp.yeni) < 4:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 4 karakter olmalı")
    user.sifre_hash = hash_sifre(inp.yeni)
    db.commit()
    return {"ok": True}
