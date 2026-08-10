from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def get_token(email, sifre):
    r = client.post("/api/login", json={"email": email, "sifre": sifre})
    return r.json()["token"]

def test_baska_kullanici_verisi():
    token1 = get_token("test@example.com", "TEST_PASS_REMOVED")
    r = client.get("/api/profile", headers={"Authorization": f"Bearer {token1}"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "test@example.com"
    

def test_token_olmadan_api():
    r = client.get("/api/profile")
    assert r.status_code == 401
    

def test_sql_injection():
    r = client.post("/api/login",json = {
        "email": "' OR '1'='1",
        "sifre": "' OR '1'='1"
    })
    assert r.status_code == 401
    
def test_gecersiz_token():
    r = client.get("/api/profile" , headers = {
        "Authorization": "Bearer sahtetoken123"
    })
    assert r.status_code == 401
    
def test_cors():
    r = client.options("/api/profile", headers={
        "Origin": "http://evil-site.com",
        "Access-Control-Request-Method": "GET"
    })
    assert r.headers.get("access-control-allow-origin") != "http://evil-site.com"
    
def test_sifre_hash():
    r = client.post("/api/register",json = {
        "ad": "Hash Test",
        "email": "hashtest@test.com",
        "sifre": "testpass123"
    })
    assert r.status_code in [200,409]
    
    data = r.json()
    
    assert 'sifre_hash' not in str(data)
    assert 'testpass123' not in str(data)
