import pytest
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from src.handlers.start import cmd_start

@pytest.mark.asyncio
async def test_start_command_resets_state():
    """Тест: /start сбрасывает любое активное состояние."""
    class MockMessage:
        from_user = type('obj', (object,), {'id': 123456789})
        chat = type('obj', (object,), {'id': 123456789})
        async def answer(self, *args, **kwargs):
            pass
    
    message = MockMessage()
    storage = MemoryStorage()
    state = FSMContext(storage, chat=123456789, user=123456789)
    
    # Устанавливаем тестовое состояние
    await state.set_state("TEST_STATE")
    assert await state.get_state() == "TEST_STATE"
    
    # Вызываем /start
    await cmd_start(message, state)
    
    # Проверяем, что состояние сброшено
    assert await state.get_state() is None