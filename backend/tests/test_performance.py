import time
import threading
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

BINA = {
    "bina_tipi": "Apartman", "kat": 4, "daire_per_kat": 2,
    "aktif_daire": 6, "oda": 3, "cati_alani": 200,
    "asansor": True, "hvac": True, "su_pompasi": False,
    "ev_sarj": False, "kamera": False, "gunes_isitici": True, "jenerator": False
}

def test_api_response_time():
    # İlk çağrı — model yüklensin
    client.post("/api/simulate", json=BINA)
    
    # 5 ardışık çağrı — ortalama süre
    sureler = []
    for _ in range(5):
        t = time.time()
        client.post("/api/simulate", json=BINA)
        sureler.append(time.time() - t)
    
    ortalama = sum(sureler) / len(sureler)
    print(f"\nOrtalama response: {ortalama:.3f}s | Min: {min(sureler):.3f}s | Max: {max(sureler):.3f}s")
    assert ortalama < 1.0  # Cache'den 1 saniyeden az gelmeli
    
def test_coklu_kullanici():
    # İlk çağrı — model yüklensin
    client.post("/api/simulate", json=BINA)
    
    sonuclar = []
    
    def istek_at():
        t = time.time()
        r = client.post("/api/simulate", json=BINA)
        sonuclar.append({
            "status": r.status_code,
            "sure": round(time.time() - t, 3)
        })
    
    # 10 kullanıcı aynı anda istek atıyor
    threads = [threading.Thread(target=istek_at) for _ in range(10)]
    t_baslangic = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    toplam = time.time() - t_baslangic
    
    basarisiz = [s for s in sonuclar if s["status"] != 200]
    print(f"\n10 eşzamanlı istek — toplam: {toplam:.2f}s")
    print(f"Başarılı: {len(sonuclar) - len(basarisiz)}/10")
    print(f"Başarısız: {len(basarisiz)}")
    
    assert len(basarisiz) == 0  # Hepsi 200 dönmeli