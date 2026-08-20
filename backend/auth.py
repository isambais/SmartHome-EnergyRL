"""Kimlik doğrulama: şifre hash'leme + basit JWT token."""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
from base64 import urlsafe_b64decode, urlsafe_b64encode

from fastapi import Depends, Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User

SECRET = os.environ.get("SECRET_KEY", "smarthome-dev-secret-degistir")
TOKEN_GUN = 30  # token geçerlilik süresi


# ── Şifre hash (PBKDF2-HMAC-SHA256, harici bağımlılık yok) ────────
def hash_sifre(sifre: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", sifre.encode(), salt, 200_000)
    return salt.hex() + "$" + dk.hex()


def dogrula_sifre(sifre: str, kayit: str) -> bool:
    try:
        salt_hex, dk_hex = kayit.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", sifre.encode(), salt, 200_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ── Basit imzalı token (JWT benzeri, HS256) ──────────────────────
def _b64(b: bytes) -> str:
    return urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return urlsafe_b64decode(s + "=" * (-len(s) % 4))


def token_olustur(user_id: int) -> str:
    exp = (dt.datetime.utcnow() + dt.timedelta(days=TOKEN_GUN)).timestamp()
    payload = _b64(json.dumps({"uid": user_id, "exp": exp}).encode())
    imza = _b64(hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{imza}"


def token_coz(token: str) -> int | None:
    try:
        payload, imza = token.split(".", 1)
        beklenen = _b64(hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(imza, beklenen):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < dt.datetime.utcnow().timestamp():
            return None
        return int(data["uid"])
    except Exception:
        return None


# ── FastAPI bağımlılığı: geçerli kullanıcı ───────────────────────
def current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    # Swagger Bearer veya düz Authorization header — ikisini de destekle
    token = ""
    if credentials:
        token = credentials.credentials
    elif authorization:
        token = authorization.replace("Bearer ", "").strip()
    uid = token_coz(token) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Oturum geçersiz veya süresi dolmuş")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return user
