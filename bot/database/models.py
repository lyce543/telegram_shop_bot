from datetime import datetime
from sqlalchemy import BigInteger, String, Text, Float, DateTime, Enum, ForeignKey, func, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
import enum


class Base(DeclarativeBase):
    pass


class ModerationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WithdrawalStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="user")
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase", 
        foreign_keys="[Purchase.user_id]",
        back_populates="user"
    )
    withdrawals: Mapped[list["Withdrawal"]] = relationship("Withdrawal", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Card(Base):
    __tablename__ = "cards"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    photo_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus), 
        default=ModerationStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="cards")
    purchases: Mapped[list["Purchase"]] = relationship("Purchase", back_populates="card")
    
    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, status={self.status.value})>"


class Purchase(Base):
    __tablename__ = "purchases"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cards.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[user_id],
        back_populates="purchases"
    )
    card: Mapped["Card"] = relationship("Card", back_populates="purchases")
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, user_id={self.user_id}, card_id={self.card_id})>"


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    requisites: Mapped[str] = mapped_column(Text)
    status: Mapped[WithdrawalStatus] = mapped_column(
        Enum(WithdrawalStatus),
        default=WithdrawalStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="withdrawals")
    
    def __repr__(self):
        return f"<Withdrawal(id={self.id}, user_id={self.user_id}, amount={self.amount})>"
