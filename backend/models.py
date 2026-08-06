"""Veritabanı modelleri: kullanıcı, kayıtlı bina, simülasyon geçmişi."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sifre_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    # Kullanıcının kayıtlı bina yapılandırması (tek satır, JSON)
    bina: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    gecmis: Mapped[list["SimKaydi"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="SimKaydi.id.desc()"
    )


class SimKaydi(Base):
    """Kullanıcının çalıştırdığı bir simülasyonun özeti."""

    __tablename__ = "sim_gecmisi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tarih: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    bina_tipi: Mapped[str] = mapped_column(String(60), default="")
    tasarruf_tl: Mapped[float] = mapped_column(Float, default=0.0)
    gunes_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    not_: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="gecmis")
