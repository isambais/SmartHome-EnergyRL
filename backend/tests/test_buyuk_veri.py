"""Büyük veri ve stres testi — backend'in sınırlarını test eder."""
import statistics
import time

import requests

BASE = "http://localhost:8000"


def get_token():
    r = requests.post(f"{BASE}/api/login", json={"email": "test@test.com", "sifre": "test1234"})
    if r.status_code == 200:
        return r.json().get("token", "")
    r = requests.post(f"{BASE}/api/register", json={"ad": "Büyük Veri", "email": "buyukveri@test.com", "sifre": "test1234"})
    return r.json().get("token", "")


TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_simulate_normal():
    """Normal simulate isteği."""
    t0 = time.time()
    r = requests.post(f"{BASE}/api/simulate", json={
        "bina_tipi": "apartman", "kat": 10, "daire_basi_kwh": 8.0,
        "panel_kw": 50.0, "batarya_kwh": 100.0,
    }, headers=HEADERS)
    sure = time.time() - t0
    assert r.status_code == 200, f"Status: {r.status_code}"
    # İlk çağrıda SAC modeli yüklenir (~20s), lru_cache ile sonraki çağrılar hızlıdır
    assert sure < 30, f"Çok yavaş: {sure:.2f}s"
    print(f"  simulate normal: {sure:.3f}s ✓")


def test_yatirim_normal():
    """Normal yatırım hesabı (12 ay paralel)."""
    t0 = time.time()
    r = requests.post(f"{BASE}/api/yatirim", json={
        "bina_tipi": "apartman", "kat": 10, "daire_basi_kwh": 8.0,
        "panel_kw": 50.0, "batarya_kwh": 100.0,
        "panel_tl": 500000, "batarya_tl": 300000,
    }, headers=HEADERS)
    sure = time.time() - t0
    assert r.status_code == 200, f"Status: {r.status_code}"
    d = r.json()
    assert len(d.get("aylik", [])) == 12
    assert sure < 60, f"Çok yavaş: {sure:.2f}s"
    print(f"  yatirim 12 ay: {sure:.3f}s | ROI: {d.get('amorti_yil', '?')} yıl ✓")


def test_yatirim_ekstrem():
    """Aşırı büyük değerlerle yatırım — çökmemeli."""
    t0 = time.time()
    r = requests.post(f"{BASE}/api/yatirim", json={
        "bina_tipi": "ofis", "kat": 50, "daire_basi_kwh": 999.0,
        "panel_kw": 9999.0, "batarya_kwh": 99999.0,
        "panel_tl": 99_000_000, "batarya_tl": 99_000_000,
    }, headers=HEADERS)
    sure = time.time() - t0
    assert r.status_code == 200, f"Status: {r.status_code} — {r.text[:200]}"
    assert sure < 60, f"Çok yavaş: {sure:.2f}s"
    print(f"  yatirim ekstrem: {sure:.3f}s ✓")


def test_20_ardisik_simulate():
    """20 ardışık simulate isteği — cache + kararlılık."""
    times = []
    for _ in range(20):
        t0 = time.time()
        r = requests.post(f"{BASE}/api/simulate", json={
            "bina_tipi": "mustakil", "kat": 2, "daire_basi_kwh": 5.0,
            "panel_kw": 10.0, "batarya_kwh": 20.0,
        }, headers=HEADERS)
        times.append(time.time() - t0)
        assert r.status_code == 200

    ort = statistics.mean(times)
    maks = max(times)
    print(f"  20x simulate: ort={ort:.3f}s maks={maks:.3f}s toplam={sum(times):.2f}s ✓")
    # Simulation kendisi ~2s (model cached, lru_cache çalışıyor)
    assert ort < 4, f"Ortalama çok yavaş: {ort:.3f}s"
    assert maks < 8, f"En yavaş istek çok uzun: {maks:.3f}s"


def test_sifir_panel():
    """Panel olmadan simulate — sıfır değerler düzgün çalışmalı."""
    r = requests.post(f"{BASE}/api/simulate", json={
        "bina_tipi": "villa", "kat": 1, "daire_basi_kwh": 3.0,
        "panel_kw": 0.0, "batarya_kwh": 0.0,
    }, headers=HEADERS)
    assert r.status_code == 200
    d = r.json()
    assert d.get("tasarruf_tl", 0) == 0 or d.get("tasarruf_tl", 1) >= 0
    print("  sıfır panel/batarya: 200 ✓")


def test_sifir_yatirim():
    """panel_tl/batarya_tl=0 gönderilince backend varsayılan fiyatları kullanır."""
    r = requests.post(f"{BASE}/api/yatirim", json={
        "bina_tipi": "mustakil", "kat": 1, "daire_basi_kwh": 4.0,
        "panel_kw": 5.0, "batarya_kwh": 10.0,
        "panel_tl": 0, "batarya_tl": 0,
    }, headers=HEADERS)
    assert r.status_code == 200
    d = r.json()
    # 0 gönderilince backend varsayılan fiyatları kullanır (0 değil, pozitif değer döner)
    assert d.get("toplam_yatirim", 0) > 0
    assert d.get("varsayilan_panel_tl", 0) > 0
    assert d.get("varsayilan_batarya_tl", 0) > 0
    print(f"  sıfır TL → varsayılan kullanıldı: toplam={d['toplam_yatirim']:,} TL ✓")
