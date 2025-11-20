import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from bot.database.models import Base, User, Card, ModerationStatus, Purchase, Withdrawal, WithdrawalStatus
from bot.database.database import Database


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    db = Database("sqlite+aiosqlite:///:memory:")
    db.engine = engine
    db.session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield db
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_add_user(test_db):
    user = await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    assert user.id == 12345
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.balance == Decimal('0.00')


@pytest.mark.asyncio
async def test_get_user(test_db):
    await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    user = await test_db.get_user(12345)
    
    assert user is not None
    assert user.id == 12345


@pytest.mark.asyncio
async def test_update_user_balance(test_db):
    await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    user = await test_db.update_user_balance(12345, Decimal('100.50'))
    
    assert user.balance == Decimal('100.50')


@pytest.mark.asyncio
async def test_add_card(test_db):
    await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    card = await test_db.add_card(
        user_id=12345,
        title="Test Product",
        description="This is a test product description",
        price=Decimal('99.99'),
        photo_id="test_photo_id"
    )
    
    assert card.title == "Test Product"
    assert card.price == Decimal('99.99')
    assert card.status == ModerationStatus.PENDING


@pytest.mark.asyncio
async def test_update_card_status(test_db):
    await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    card = await test_db.add_card(
        user_id=12345,
        title="Test Product",
        description="This is a test product description",
        price=Decimal('99.99')
    )
    
    updated_card = await test_db.update_card_status(card.id, ModerationStatus.APPROVED)
    
    assert updated_card.status == ModerationStatus.APPROVED
    assert updated_card.moderated_at is not None


@pytest.mark.asyncio
async def test_add_purchase(test_db):
    buyer = await test_db.add_user(
        user_id=12345,
        username="buyer",
        first_name="Buyer"
    )
    
    seller = await test_db.add_user(
        user_id=54321,
        username="seller",
        first_name="Seller"
    )
    
    card = await test_db.add_card(
        user_id=seller.id,
        title="Test Product",
        description="Description",
        price=Decimal('50.00')
    )
    
    purchase = await test_db.add_purchase(
        user_id=buyer.id,
        card_id=card.id,
        amount=Decimal('50.00'),
        seller_id=seller.id
    )
    
    assert purchase.user_id == buyer.id
    assert purchase.card_id == card.id
    assert purchase.amount == Decimal('50.00')
    
    updated_seller = await test_db.get_user(seller.id)
    assert updated_seller.balance == Decimal('50.00')


@pytest.mark.asyncio
async def test_create_withdrawal(test_db):
    user = await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    await test_db.update_user_balance(user.id, Decimal('100.00'))
    
    withdrawal = await test_db.create_withdrawal(
        user_id=user.id,
        amount=Decimal('50.00'),
        requisites="1234567890"
    )
    
    assert withdrawal is not None
    assert withdrawal.amount == Decimal('50.00')
    assert withdrawal.status == WithdrawalStatus.PENDING
    
    updated_user = await test_db.get_user(user.id)
    assert updated_user.balance == Decimal('50.00')


@pytest.mark.asyncio
async def test_create_withdrawal_insufficient_balance(test_db):
    user = await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    withdrawal = await test_db.create_withdrawal(
        user_id=user.id,
        amount=Decimal('50.00'),
        requisites="1234567890"
    )
    
    assert withdrawal is None


@pytest.mark.asyncio
async def test_complete_withdrawal(test_db):
    user = await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    await test_db.update_user_balance(user.id, Decimal('100.00'))
    
    withdrawal = await test_db.create_withdrawal(
        user_id=user.id,
        amount=Decimal('50.00'),
        requisites="1234567890"
    )
    
    completed = await test_db.complete_withdrawal(withdrawal.id)
    
    assert completed.status == WithdrawalStatus.COMPLETED
    assert completed.completed_at is not None


@pytest.mark.asyncio
async def test_get_pending_withdrawals(test_db):
    user = await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    await test_db.update_user_balance(user.id, Decimal('200.00'))
    
    await test_db.create_withdrawal(user.id, Decimal('50.00'), "req1")
    await test_db.create_withdrawal(user.id, Decimal('30.00'), "req2")
    
    pending = await test_db.get_pending_withdrawals()
    
    assert len(pending) == 2


@pytest.mark.asyncio
async def test_get_user_statistics(test_db):
    await test_db.add_user(
        user_id=12345,
        username="testuser",
        first_name="Test"
    )
    
    card1 = await test_db.add_card(
        user_id=12345,
        title="Product 1",
        description="Description 1",
        price=Decimal('10.00')
    )
    
    card2 = await test_db.add_card(
        user_id=12345,
        title="Product 2",
        description="Description 2",
        price=Decimal('20.00')
    )
    
    card3 = await test_db.add_card(
        user_id=12345,
        title="Product 3",
        description="Description 3",
        price=Decimal('30.00')
    )
    
    await test_db.update_card_status(card1.id, ModerationStatus.APPROVED)
    await test_db.update_card_status(card2.id, ModerationStatus.REJECTED)
    
    stats = await test_db.get_user_statistics()
    
    assert len(stats) == 1
    assert stats[0]['user_id'] == 12345
    assert stats[0]['total_cards'] == 3
    assert stats[0]['approved'] == 1
    assert stats[0]['rejected'] == 1