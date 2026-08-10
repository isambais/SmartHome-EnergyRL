from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dogru_giris():
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "sifre": "TEST_PASS_REMOVED"
    })
    assert response.status_code == 200
    assert "token" in response.json()
    
def test_yanlis_sifre():
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "sifre": "yanlis123"
    })
    assert response.status_code == 401
    
def test_olmayan_kullanici():
    response = client.post("/api/login",json = {
        "email": "yok@yok.com",
        "sifre": "1234"
        })
    assert response.status_code == 401
    
def test_bos_alan():
    response = client.post("/api/login", json={
        "email": "",
        "sifre": ""
    })
    assert response.status_code == 401
    

def test_gecersiz_email():
    response = client.post("/api/login", json={
        "email": "buemail degil",
        "sifre": "1234"
    })
    assert response.status_code == 401
    
def test_uzun_email():
    response = client.post("/api/login", json={
        "email": "a" * 300 + "@test.com",
        "sifre": "1234"
    })
    assert response.status_code == 401
    
def test_logout():
    # Önce giriş yap, token al
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "sifre": "TEST_PASS_REMOVED"
    })
    token = response.json()["token"]
    response = client.get("/api/profile",headers = {
        "Authorization" : f"Bearer {token}"
    })
    assert response.status_code == 200
    
    response = client.get("/api/profile")
    assert response.status_code == 401