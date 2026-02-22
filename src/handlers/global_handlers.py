import logging
from aiogram import types
from aiogram.dispatcher import FSMContext

from src.utils.keyboard_utils import get_main_menu


logger = logging.getLogger(__name__)

# --- ГЛОБАЛЬНЫЕ ХЕНДЛЕРЫ ---

async def global_back_to_menu_handler(query: types.CallbackQuery, state: FSMContext):
    """
    Глобальный обработчик 'Вернуться в меню'.
    Сбрасывает FSM и отправляет главное меню.
    """
    await query.answer() # Всегда отвечаем на callback
    user_id = query.from_user.id
    logger.debug(f"Global 'back_to_menu' triggered by user {user_id}")

    # Проверяем и сбрасываем состояние FSM
    current_state = await state.get_state()
    if current_state:
        logger.info(f"Finishing FSM state '{current_state}' for user {user_id} via 'back_to_menu'")
        await state.finish()
    else:
        logger.debug(f"No active FSM state for user {user_id} when 'back_to_menu' was pressed")

    # Отправляем главное меню
    # Удаляем или редактируем старое сообщение с кнопкой, если нужно
    # await query.message.delete() # Опционально, аккуратно
    await query.message.answer("Выберите действие:", reply_markup=get_main_menu())


def register_global_callbacks(dp):
    """
    Регистрация глобальных callback-хендлеров.
    """
    logger.debug("Registering global callback handlers...")

    # Регистрируем глобальный хендлер 'back_to_menu' с фильтром конкретного callback_data
    # Это безопаснее, чем state="*", если у вас есть другие хендлеры на callback_query
    dp.register_callback_query_handler(
        global_back_to_menu_handler,
        lambda q: q.data == "back_to_menu",
        state="*"
    )

    logger.debug("Global callback handlers registered.")