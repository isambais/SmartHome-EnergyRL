"""EPİAŞ bağlantı tanı aracı.

Çalıştır (proje kökünden):
    python -m backend.epias_test

Adım adım nerede takıldığını gösterir: .env okundu mu, TGT alındı mı,
fiyat servisi ne döndü.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]

# .env oku
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    print("[1] python-dotenv: kurulu ✓  (.env okundu)")
except Exception as e:
    print(f"[1] python-dotenv YOK ✗ → .env okunamadı ({e})")
    print("    Çözüm:  pip install python-dotenv")

user = os.environ.get("EPIAS_USER", "")
pw = os.environ.get("EPIAS_PASS", "")
print(f"[2] EPIAS_USER: {'DOLU ✓ (' + user + ')' if user else 'BOŞ ✗'}")
print(f"    EPIAS_PASS: {'DOLU ✓ (' + str(len(pw)) + ' karakter)' if pw else 'BOŞ ✗'}")
if not user or not pw:
    print("    → .env dosyası okunmuyor ya da alanlar boş. Uygulama arşiv/sentetik veriye düşer.")
    raise SystemExit

# TGT al
CAS = "https://giris.epias.com.tr/cas/v1/tickets"
try:
    r = requests.post(CAS, data={"username": user, "password": pw},
                      headers={"Content-Type": "application/x-www-form-urlencoded",
                               "Accept": "text/plain"}, timeout=15)
    print(f"[3] TGT isteği: HTTP {r.status_code}")
    if r.status_code not in (200, 201):
        print(f"    Yanıt: {r.text[:300]}")
        print("    → Kullanıcı adı/şifre hatalı olabilir ya da hesap doğrulanmamış.")
        raise SystemExit
    tgt = r.text.strip()
    print(f"    TGT alındı ✓ ({tgt[:25]}...)")
except SystemExit:
    raise
except Exception as e:
    print(f"[3] TGT isteği hata: {e}")
    raise SystemExit

# Fiyat çek
MCP = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"
gun = dt.date.today().strftime("%Y-%m-%dT00:00:00+03:00")
try:
    r2 = requests.post(MCP, json={"startDate": gun, "endDate": gun},
                       headers={"TGT": tgt, "Content-Type": "application/json"}, timeout=20)
    print(f"[4] Fiyat servisi: HTTP {r2.status_code}")
    if r2.status_code == 200:
        items = r2.json().get("items", [])
        print(f"    ✓ {len(items)} saatlik fiyat geldi. İlk kayıt: {items[0] if items else '—'}")
        print("\nSONUÇ: Canlı EPİAŞ ÇALIŞIYOR. Uygulama artık 'EPİAŞ API (canlı)' gösterecek.")
    else:
        print(f"    Yanıt: {r2.text[:400]}")
        print("\nSONUÇ: TGT alındı ama fiyat servisi reddetti.")
        print("    En olası neden: bilgisayarının IP'si EPİAŞ portalına kayıtlı değil")
        print("    (Şeffaflık Platformu → Web Servis IP Kayıt). Kayıtsız IP'ler veri alamaz.")
except Exception as e:
    print(f"[4] Fiyat servisi hata: {e}")
