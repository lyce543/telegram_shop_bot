from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, case
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from bot.database.models import Base, User, Card, ModerationStatus, Purchase, Withdrawal, WithdrawalStatus
from bot.config import config
from bot.utils.logger import logger


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        self.session_maker = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    
    async def add_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> User:
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(id=user_id, username=username, first_name=first_name, balance=Decimal('0.00'))
                session.add(user)
                logger.info(f"New user added: {user_id} (@{username})")
            else:
                user.username = username
                user.first_name = first_name
            
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    
    async def update_user_balance(self, user_id: int, amount: Decimal) -> Optional[User]:
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                user.balance += amount
                await session.commit()
                await session.refresh(user)
                logger.info(f"User {user_id} balance updated: {amount}")
            
            return user
    
    async def add_card(self, user_id: int, title: str, description: str, 
                       price: Decimal, photo_id: Optional[str] = None) -> Card:
        async with self.session_maker() as session:
            card = Card(
                user_id=user_id,
                title=title,
                description=description,
                price=price,
                photo_id=photo_id,
                status=ModerationStatus.PENDING
            )
            session.add(card)
            await session.commit()
            await session.refresh(card)
            logger.info(f"Card added: {card.id} by user {user_id}")
            return card
    
    async def get_approved_cards(self) -> List[Card]:
        async with self.session_maker() as session:
            result = await session.execute(
                select(Card)
                .where(Card.status == ModerationStatus.APPROVED)
                .order_by(Card.created_at.desc())
            )
            return list(result.scalars().all())
    
    async def get_pending_cards(self) -> List[Card]:
        async with self.session_maker() as session:
            result = await session.execute(
                select(Card)
                .where(Card.status == ModerationStatus.PENDING)
                .order_by(Card.created_at.asc())
            )
            return list(result.scalars().all())
    
    async def get_card(self, card_id: int) -> Optional[Card]:
        async with self.session_maker() as session:
            result = await session.execute(select(Card).where(Card.id == card_id))
            return result.scalar_one_or_none()
    
    async def update_card_status(self, card_id: int, status: ModerationStatus) -> Optional[Card]:
        async with self.session_maker() as session:
            result = await session.execute(select(Card).where(Card.id == card_id))
            card = result.scalar_one_or_none()
            
            if card:
                card.status = status
                card.moderated_at = datetime.now()
                await session.commit()
                await session.refresh(card)
                logger.info(f"Card {card_id} status updated to {status.value}")
            
            return card
    
    async def update_card_field(self, card_id: int, field: str, value: any) -> Optional[Card]:
        async with self.session_maker() as session:
            result = await session.execute(select(Card).where(Card.id == card_id))
            card = result.scalar_one_or_none()
            
            if card:
                setattr(card, field, value)
                await session.commit()
                await session.refresh(card)
                logger.info(f"Card {card_id} field '{field}' updated")
            
            return card
    
    async def delete_card(self, card_id: int) -> bool:
        async with self.session_maker() as session:
            result = await session.execute(select(Card).where(Card.id == card_id))
            card = result.scalar_one_or_none()
            
            if card:
                await session.delete(card)
                await session.commit()
                logger.info(f"Card {card_id} deleted")
                return True
            
            return False
    
    async def add_purchase(self, user_id: int, card_id: int, amount: Decimal, seller_id: int) -> Purchase:
        async with self.session_maker() as session:
            purchase = Purchase(
                user_id=user_id,
                card_id=card_id,
                amount=amount,
                seller_id=seller_id
            )
            session.add(purchase)
            
            result = await session.execute(select(User).where(User.id == seller_id))
            seller = result.scalar_one_or_none()
            if seller:
                seller.balance += amount
            
            await session.commit()
            await session.refresh(purchase)
            logger.info(f"Purchase created: user {user_id} bought card {card_id} for {amount}")
            return purchase
    
    async def create_withdrawal(self, user_id: int, amount: Decimal, requisites: str) -> Optional[Withdrawal]:
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or user.balance < amount:
                return None
            
            user.balance -= amount
            
            withdrawal = Withdrawal(
                user_id=user_id,
                amount=amount,
                requisites=requisites,
                status=WithdrawalStatus.PENDING
            )
            session.add(withdrawal)
            await session.commit()
            await session.refresh(withdrawal)
            logger.info(f"Withdrawal created: user {user_id}, amount {amount}")
            return withdrawal
    
    async def get_pending_withdrawals(self) -> List[Withdrawal]:
        async with self.session_maker() as session:
            result = await session.execute(
                select(Withdrawal)
                .where(Withdrawal.status == WithdrawalStatus.PENDING)
                .order_by(Withdrawal.created_at.asc())
            )
            return list(result.scalars().all())
    
    async def complete_withdrawal(self, withdrawal_id: int) -> Optional[Withdrawal]:
        async with self.session_maker() as session:
            result = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
            withdrawal = result.scalar_one_or_none()
            
            if withdrawal:
                withdrawal.status = WithdrawalStatus.COMPLETED
                withdrawal.completed_at = datetime.now()
                await session.commit()
                await session.refresh(withdrawal)
                logger.info(f"Withdrawal {withdrawal_id} completed")
            
            return withdrawal
    
    async def get_user_statistics(self) -> List[dict]:
        async with self.session_maker() as session:
            result = await session.execute(
                select(
                    User.id,
                    User.username,
                    User.first_name,
                    func.count(Card.id).label('total_cards'),
                    func.sum(case((Card.status == ModerationStatus.APPROVED, 1), else_=0)).label('approved'),
                    func.sum(case((Card.status == ModerationStatus.REJECTED, 1), else_=0)).label('rejected')
                )
                .outerjoin(Card, User.id == Card.user_id)
                .group_by(User.id)
            )
            
            statistics = []
            for row in result:
                statistics.append({
                    'user_id': row.id,
                    'username': row.username,
                    'first_name': row.first_name,
                    'total_cards': row.total_cards or 0,
                    'approved': row.approved or 0,
                    'rejected': row.rejected or 0
                })
            
            return statistics


db = Database(config.DATABASE_URL)