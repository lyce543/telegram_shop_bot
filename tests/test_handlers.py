import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext

from bot.filters.custom_filters import IsAdminFilter, PriceValidationFilter
from bot.config import config


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.chat = MagicMock(spec=Chat)
    message.chat.type = "private"
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.get_state = AsyncMock(return_value=None)
    return state


@pytest.mark.asyncio
async def test_is_private_filter():
    from bot.filters.custom_filters import IsPrivateFilter
    
    message = MagicMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.type = "private"
    
    filter_instance = IsPrivateFilter()
    result = await filter_instance(message)
    
    assert result is True


@pytest.mark.asyncio
async def test_is_private_filter_group():
    from bot.filters.custom_filters import IsPrivateFilter
    
    message = MagicMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.type = "group"
    
    filter_instance = IsPrivateFilter()
    result = await filter_instance(message)
    
    assert result is False