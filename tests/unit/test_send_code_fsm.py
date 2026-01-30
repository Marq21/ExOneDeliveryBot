import pytest
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from src.states.code_states import CodeStates
from src.handlers.send_code import start_send_code

@pytest.mark.asyncio
async def test_start_send_code_sets_correct_state():
    """Тест, что start_send_code устанавливает правильное состояние FSM."""
    class MockMessage:
        from_user = type('obj', (object,), {'id': 123456789})
        chat = type('obj', (object,), {'id': 123456789})
        
        async def answer(self, *args, **kwargs):
            pass
    
    message = MockMessage()
    storage = MemoryStorage()
    state = FSMContext(storage, chat=123456789, user=123456789)
    
    await start_send_code(message, state)
    
    current_state = await state.get_state()
    assert current_state == CodeStates.CHOOSING_STORE.state