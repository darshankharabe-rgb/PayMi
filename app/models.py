# app/models.py

from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship("User")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Store amounts as cents to avoid floating-point rounding errors
    amount: Mapped[int] = mapped_column(Integer, nullable=False) 
  
    # Will be credit  or debit
    entry_type: Mapped[str] = mapped_column(String, nullable=False) 
    # A unique UUID to link the debit and credit rows of a single transfer together
   
    transaction_id: Mapped[str] = mapped_column(String, index=True, nullable=False) 
  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    account: Mapped["Account"] = relationship("Account")
