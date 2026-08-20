from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_bos_form():
    response = client.post("/api/register", json={
        "ad": "",
        "email": "",
        "sifre": ""
    })
    assert response.status_code in [400, 422]
    
def test_cok_uzun_veri():
    response = client.post("/api/register", json={
        "ad": "a" * 500,
        "email": "a" * 300 + "@test.com",
        "sifre": "b" * 500
    })
    assert response.status_code in [400,422]
    
def test_ozel_karakterler():
    response = client.post("/api/register", json={
        "ad": "Test !@#$%^&*()",
        "email": "test.ozel+123@test.com",
        "sifre": "!@#$%^&*()"
    })
    assert response.status_code in [200,409]
    
def test_turkce_karakterleri():
    response = client.post("/api/register", json={
        "ad": "Şükrü Çelik",
        "email": "turkce.test99@test.com",
        "sifre": "şifrğüş123"
    })
    assert response.status_code in [200,409]
    
def test_emoji():
    response = client.post("/api/register", json={
        "ad": "Test 😀🔥",
        "email": "emoji.test@test.com",
        "sifre": "sifre123😀"
    })
    assert response.status_code in [200, 409]
    
def test_yanlis_format():
    response = client.post("/api/register", json={
        "ad": 12345,
        "email": None,
        "sifre": True
    })
    assert response.status_code == 422
    
def test_ayni_veri_iki_kere():
    import time
    email = f"tekrar{int(time.time())}@test.com"
    veri = {
        "ad": "Tekrar Kullanici",
        "email": email,
        "sifre": "1234"
    }
    ilk = client.post("/api/register", json=veri)
    ikinci = client.post("/api/register", json=veri)

    assert ilk.status_code == 200
    assert ikinci.status_code == 409