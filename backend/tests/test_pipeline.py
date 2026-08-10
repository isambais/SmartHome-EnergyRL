from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

BINA = {
    "bina_tipi": "Apartman", "kat": 4, "daire_per_kat": 2,
    "aktif_daire": 6, "oda": 3, "cati_alani": 200,
    "asansor": True, "hvac": True, "su_pompasi": False,
    "ev_sarj": False, "kamera": False, "gunes_isitici": True, "jenerator": False
}

def test_model_dogru_input():
    r = client.post("/api/simulate", json=BINA)
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data
    assert len(data["rows"]) == 24
    assert "karar" in data["rows"][0]
    assert data["rows"][0]["karar"] in ["şarj", "deşarj", "bekle"]


def test_sacma_input():
    r = client.post("/api/simulate", json={
        "bina_tipi": "Apartman", "kat": -5, "daire_per_kat": 0,
        "aktif_daire": 999, "oda": -1, "cati_alani": -100,
        "asansor": True, "hvac": True, "su_pompasi": False,
        "ev_sarj": False, "kamera": False, "gunes_isitici": True, "jenerator": False
    })
    # Ya hata dönmeli ya da sınır içinde tutulmalı
    assert r.status_code in [200, 400, 422]
    if r.status_code == 200:
        data = r.json()
        assert len(data["rows"]) == 24  # En azından çökmemeli

def test_sacma_input_degerleri():
    r = client.post("/api/simulate", json={
        "bina_tipi": "Apartman", "kat": -5, "daire_per_kat": 0,
        "aktif_daire": 999, "oda": -1, "cati_alani": -100,
        "asansor": True, "hvac": True, "su_pompasi": False,
        "ev_sarj": False, "kamera": False, "gunes_isitici": True, "jenerator": False
    })
    if r.status_code == 200:
        ozet = r.json()["ozet"]
        print(f"\nSaçma input sonucu: {ozet}")
        # Tasarruf mantıklı aralıkta mı?
        assert ozet["tasarruf_tl"] > -100000
        assert ozet["tasarruf_tl"] < 10000000   

import time

def test_response_suresi():
    baslangic = time.time()
    r = client.post("/api/simulate", json=BINA)
    sure = time.time() - baslangic
    assert r.status_code == 200
    print(f"\nSimülasyon süresi: {sure:.2f}s")
    assert sure < 30  # 30 saniyeden uzun sürerse sorun var


def test_response_suresi_ikinci_cagri():
    # İlk çağrı — model yükleniyor
    client.post("/api/simulate", json=BINA)
    
    # İkinci çağrı — cache'den gelmeli
    baslangic = time.time()
    r = client.post("/api/simulate", json=BINA)
    sure = time.time() - baslangic
    print(f"\nİkinci çağrı süresi: {sure:.2f}s")
    assert r.status_code == 200
    assert sure < 5  # Cache'den gelince 5 saniyeden az olmalı
    
    
def test_tutarlilik():
    r1 = client.post("/api/simulate", json=BINA)
    r2 = client.post("/api/simulate", json=BINA)
    
    ozet1 = r1.json()["ozet"]
    ozet2 = r2.json()["ozet"]
    
    assert ozet1["tasarruf_tl"] == ozet2["tasarruf_tl"]
    assert ozet1["gunes_kwh"] == ozet2["gunes_kwh"]
    print(f"\nTasarruf 1: {ozet1['tasarruf_tl']} | Tasarruf 2: {ozet2['tasarruf_tl']}")
    
    
def test_model_hata_durumu():
    # Tüm alanlar default'a sahip — eksik alan kabul edilmeli
    r = client.post("/api/simulate", json={"bina_tipi": "Apartman"})
    assert r.status_code == 200  # Default değerlerle çalışmalı
    assert len(r.json()["rows"]) == 24
    
def test_gecersiz_bina_tipi():
    bina = BINA.copy()
    bina["bina_tipi"] = "UcakGemisi"
    r = client.post("/api/simulate", json=bina)
    # Ya 400 hatası ya da varsayılan bina tipiyle devam etmeli
    assert r.status_code in [200, 400, 422]
    print(f"\nGeçersiz bina tipi sonucu: {r.status_code}")