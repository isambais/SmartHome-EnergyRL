import pytest 
from playwright.sync_api import Page

def test_anasayfa_aciyor(page: Page):
    page.goto("http://localhost:5173")
    assert page.title() != ""

def test_giris_sayfasi_aciyor(page: Page):
    page.goto("http://localhost:5173/giris")
    assert page.url == "http://localhost:5173/giris"

def test_olmayan_sayfa(page: Page):
    page.goto("http://localhost:5173/olmayan-sayfa")
    assert page.url != ""  # uygulama çökmemeli
    
def test_token_olmadan_korumalı_sayfa(page: Page):
    page.goto("http://localhost:5173/simulasyon")
    page.wait_for_url("**/kayit**")
    assert "kayit" in page.url    

def test_sayfa_yenilenince(page: Page):
    # Giriş yap
    page.goto("http://localhost:5173/giris")
    page.fill("input[type='email']", "test@example.com")
    page.fill("input[type='password']", "TEST_PASS_REMOVED")
    page.click("button[type='submit']")
    page.wait_for_url("http://localhost:5173/")

    # Simulasyon sayfasına git
    page.goto("http://localhost:5173/simulasyon")
    page.wait_for_load_state("networkidle")

    # Sayfayı yenile
    page.reload()
    page.wait_for_load_state("networkidle")

    # Hala simulasyon'da olmalı, login'e atmamalı
    assert "simulasyon" in page.url
    
def test_direkt_url_erisim(page: Page):
    page.goto("http://localhost:5173/epias")
    page.wait_for_url("**/kayit**")
    assert "kayit" in page.url 
    
    page.goto("http://localhost:5173/giris")
    page.fill("input[type='email']", "test@example.com")
    page.fill("input[type='password']", "TEST_PASS_REMOVED")
    page.click("button[type='submit']")
    page.wait_for_url("http://localhost:5173/")
    
    page.goto("http://localhost:5173/epias")
    page.wait_for_load_state("networkidle")
    assert "epias" in page.url
    
    
