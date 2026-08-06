"""Veritabanı katmanı — SQLAlchemy engine + oturum.

Bağlantı DATABASE_URL ortam değişkeninden okunur. Örnekler:
  PostgreSQL : postgresql+psycopg://postgres:postgres@localhost:5432/smarthome
  SQLite     : sqlite:///./smarthome.db   (yerel test için)

.env dosyasına DATABASE_URL yazabilirsiniz. Verilmezse yerel SQLite dosyası
kullanılır (uygulama Postgres olmadan da çalışır).
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[1]

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{ROOT / 'smarthome.db'}",
)

# SQLite için özel bağlantı argümanı gerekir
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI bağımlılığı — istek başına oturum açar/kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Tabloları oluştur (yoksa)."""
    import backend.models  # noqa: F401  (modelleri kaydet)
    Base.metadata.create_all(bind=engine)
