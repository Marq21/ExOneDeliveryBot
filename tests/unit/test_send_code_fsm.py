# tests/unit/test_send_code_fsm.py
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.dispatcher import FSMContext
from src.states.code_states import CodeStates
from src.handlers.send_code import start_send_code


@pytest.mark.asyncio
async def test_start_send_code_sets_correct_state():
    """Тест, что start_send_code вызывает set_state с правильным состоянием."""
    with patch("src.handlers.send_code.is_code_acceptance_time", return_value=True):
        message = AsyncMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789

        state = AsyncMock(spec=FSMContext)

        await start_send_code(message, state)

        state.set_state.assert_awaited_once_with(CodeStates.CHOOSING_STORE)