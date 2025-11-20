import pytest
from unittest.mock import MagicMock
from aiogram.types import Message, User, Chat

from bot.filters.custom_filters import IsAdminFilter, PriceValidationFilter, AmountValidationFilter
from bot.config import config


@pytest.mark.asyncio
async def test_is_admin_filter_admin():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 999999999
    
    filter_instance = IsAdminFilter()
    
    original_admin_ids = config.ADMIN_IDS.copy()
    config.ADMIN_IDS = [message.from_user.id]
    
    result = await filter_instance(message)
    
    config.ADMIN_IDS = original_admin_ids
    
    assert result is True


@pytest.mark.asyncio
async def test_is_admin_filter_not_admin():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 99999
    
    filter_instance = IsAdminFilter()
    result = await filter_instance(message)
    
    assert result is False


@pytest.mark.asyncio
async def test_price_validation_filter_valid():
    message = MagicMock(spec=Message)
    message.text = "99.99"
    
    filter_instance = PriceValidationFilter()
    result = await filter_instance(message)
    
    assert result is True


@pytest.mark.asyncio
async def test_price_validation_filter_valid_comma():
    message = MagicMock(spec=Message)
    message.text = "99,99"
    
    filter_instance = PriceValidationFilter()
    result = await filter_instance(message)
    
    assert result is True


@pytest.mark.asyncio
async def test_price_validation_filter_invalid():
    message = MagicMock(spec=Message)
    message.text = "not a price"
    
    filter_instance = PriceValidationFilter()
    result = await filter_instance(message)
    
    assert result is False


@pytest.mark.asyncio
async def test_price_validation_filter_negative():
    message = MagicMock(spec=Message)
    message.text = "-10.00"
    
    filter_instance = PriceValidationFilter()
    result = await filter_instance(message)
    
    assert result is False


@pytest.mark.asyncio
async def test_amount_validation_filter_valid():
    message = MagicMock(spec=Message)
    message.text = "100.50"
    
    filter_instance = AmountValidationFilter()
    result = await filter_instance(message)
    
    assert result is True


@pytest.mark.asyncio
async def test_amount_validation_filter_invalid():
    message = MagicMock(spec=Message)
    message.text = "invalid"
    
    filter_instance = AmountValidationFilter()
    result = await filter_instance(message)
    
    assert result is False