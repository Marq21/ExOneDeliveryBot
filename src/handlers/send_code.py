import logging
import time
from pathlib import Path
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.services.code_photo_processing import process_final_code_photo
from src.states.code_states import CodeStates
from src.utils.code_acceptance_schedule import format_working_hours_message, is_session_allowed_to_proceed
from src.utils.code_validator import get_store_description
from src.bot_instance import bot
from src.services.code_processing import process_final_order_data
import aiofiles
import aiofiles.os as aios
from src.utils.store_utils import get_readable_store_name
from src.utils.config_loader import ConfigLoader
from src.utils.office_utils import is_office_available
from src.utils.keyboard_utils import (
    get_main_menu,
    get_store_selection_keyboard,
    get_office_keyboard,
    # get_ozon_pvz_keyboard,
)


logger = logging.getLogger(__name__)


async def start_send_code(message: types.Message, state: FSMContext):
    """Запуск сценария отправки кода — выбор маркетплейса."""
    logger.debug(f"🔄 Starting send_code flow for user {message.from_user.id}")
    await state.finish()  # Всегда сбрасываем состояние перед началом

    # --- Проверка расписания приёма кодов ---
    if not is_session_allowed_to_proceed():
        # Форматируем и отправляем подробное расписание
        schedule_message = format_working_hours_message()
        await message.answer(
            f"🕗 <b>К сожалению, приём кодов сейчас закрыт.</b>\n\n"
            f"{schedule_message}\n\n"
            f"Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )
        return

    await state.update_data(session_start_timestamp=int(time.time()))
    markup = get_store_selection_keyboard()

    await message.answer("🛍 <b>Выберите маркетплейс:</b>", reply_markup=markup, parse_mode="HTML")
    await state.set_state(CodeStates.CHOOSING_STORE)


async def process_store_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора магазина."""
    await query.answer()
    user_id = query.from_user.id
    callback_data = query.data
    logger.debug(
        f"Callback 'process_store_choice' received: {callback_data} from user {user_id}")

    current_state = await state.get_state()
    if current_state != CodeStates.CHOOSING_STORE.state:
        logger.warning(
            f"State mismatch for user {user_id}. Expected {CodeStates.CHOOSING_STORE.state}, got {current_state}")
        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return

    if callback_data == "store_ozon":
        await state.update_data(store="store_ozon")
        # ⚠️ ВРЕМЕННО: ПВЗ "50-летия Ростсельмаша" не работает, используем только "Троллейбусная"
        await state.update_data(ozon_pvz_id="trolleibusnaya")

        example_photo = "ozon-ok.jpg"
        photo_path = Path("static") / "images" / example_photo
        store_description = get_store_description("store_ozon")
        readable_store_name = get_readable_store_name("store_ozon")
        caption = (
            f"📸 <b>Отправьте скриншот с кодом выдачи</b>\n"
            f"Для {readable_store_name}: {store_description}\n"
            "<i>Убедитесь, что код хорошо виден на фото</i>"
        )
        try:
            if await aios.path.exists(photo_path):
                async with aiofiles.open(photo_path, "rb") as f:
                    photo_bytes = await f.read()
                await bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=photo_bytes,
                    caption=caption,
                    parse_mode="HTML"
                )
                logger.debug(f"Sent example photo: {photo_path}")
            else:
                await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")
                logger.warning(f"Example photo not found: {photo_path}")
        except Exception as e:
            logger.error(f"Error sending example photo: {e}")
            await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")

        await state.set_state(CodeStates.RECEIVING_CODE)
        logger.debug(
            f"Set state to RECEIVING_CODE for user {user_id} (OZON, PVZ=trolleibusnaya)")

    elif callback_data == "store_wildberries":
        await state.update_data(store="store_wildberries")
        example_photo = "wb.jpg"
        photo_path = Path("static") / "images" / example_photo
        store_description = get_store_description("store_wildberries")
        readable_store_name = get_readable_store_name("store_wildberries")
        caption = (
            f"📸 <b>Отправьте скриншот с кодом выдачи</b>\n"
            f"Для {readable_store_name}: {store_description}\n"
            "<i>Убедитесь, что код хорошо виден на фото</i>"
        )

        try:
            if await aios.path.exists(photo_path):
                async with aiofiles.open(photo_path, "rb") as f:
                    photo_bytes = await f.read()
                await bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=photo_bytes,
                    caption=caption,
                    parse_mode="HTML"
                )
                logger.debug(f"Sent example photo: {photo_path}")
            else:
                await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")
                logger.warning(f"Example photo not found: {photo_path}")
        except Exception as e:
            logger.exception(f"Error sending example photo: {e}")
            await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")
        await state.set_state(CodeStates.RECEIVING_CODE)

        logger.debug(f"Set state to RECEIVING_CODE for user {user_id}")
    else:
        # Неожиданный callback_data в этом состоянии
        logger.warning(
            f"Unexpected callback_data '{callback_data}' in CHOOSING_STORE for user {user_id}")
        await query.message.edit_text("❌ Неожиданная команда. Попробуйте заново.")
        await state.finish()
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())


async def back_to_store_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Возврат к выбору магазина.
    Эта функция вызывается явно из других хендлеров (например, process_office_choice).
    """
    await query.answer()
    logger.debug(
        f"Handling 'back_to_store_choice' for user {query.from_user.id}")
    # Удаляем старое сообщение с выбором офиса (если применимо)
    try:
        await query.message.delete()
    except Exception:
        pass  # Игнорируем ошибки при удалении, если сообщение уже удалено

    # Вызываем основную функцию старта, она сама установит состояние
    await start_send_code(query.message, state)


async def process_code_photo(message: types.Message, state: FSMContext):
    """Обработка фото с кодом."""
    if not message.photo:
        await message.answer("📸 Пожалуйста, отправьте фото с кодом.")
        return
    await process_final_code_photo(message, state)


async def _is_expected_state(
    query: types.CallbackQuery,
    state: FSMContext,
    expected_state: str
) -> bool:
    """
    Проверяет, что пользователь находится в ожидаемом FSM-состоянии.
    """
    current_state = await state.get_state()

    if current_state != expected_state:
        user_id = query.from_user.id

        logger.warning(
            f"State mismatch for user {user_id}. "
            f"Expected {expected_state}, got {current_state}"
        )

        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        await query.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu()
        )

        return False

    return True


async def _notify_office_unavailable(
    query: types.CallbackQuery,
    office_id: str
) -> None:
    """
    Сообщает пользователю, что выбранный офис недоступен.
    """
    user_id = query.from_user.id

    logger.warning(
        f"User {user_id} tried to select unavailable office: {office_id}"
    )

    error_text = (
        "❌ Этот пункт выдачи сейчас недоступен.\n"
        "Пожалуйста, выберите другой офис:"
    )

    try:
        await query.message.edit_text(
            error_text,
            reply_markup=get_office_keyboard()
        )
    except Exception:
        await query.message.answer(
            error_text,
            reply_markup=get_office_keyboard()
        )


async def _process_valid_office_choice(
    query: types.CallbackQuery,
    state: FSMContext,
    office_id: str
) -> None:
    """
    Обрабатывает корректный выбор офиса и переводит пользователя дальше.
    """
    user_id = query.from_user.id

    await state.update_data(office_id=office_id)

    # Удаляем сообщение с выбором офиса
    try:
        await query.message.delete()
    except Exception:
        pass

    data = await state.get_data()
    store = data.get("store")

    if store == "store_ozon":
        await query.message.answer(
            "👤 <b>Введите ваше ФИО:</b>\n"
            "<i>Фамилия Имя Отчество</i>",
            parse_mode="HTML"
        )
        await state.set_state(CodeStates.WAITING_FOR_NAME)

        logger.debug(
            f"Set state to WAITING_FOR_NAME for user {user_id}"
        )

    elif store == "store_wildberries":
        await query.message.answer(
            "📱 <b>Введите ваш номер телефона:</b>\n"
            "<i>Формат: +7 XXX XXX-XX-XX</i>",
            parse_mode="HTML"
        )
        await state.set_state(CodeStates.WAITING_FOR_PHONE)

        logger.debug(
            f"Set state to WAITING_FOR_PHONE for user {user_id}"
        )

    else:
        logger.error(
            f"Store not set in FSM for user {user_id}"
        )

        await query.message.answer("❌ Ошибка данных. Попробуйте снова.")
        await state.finish()


async def process_office_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора офиса."""
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    logger.debug(
        f"Callback 'process_office_choice' received: {callback_data} "
        f"from user {user_id}"
    )

    if not await _is_expected_state(
        query,
        state,
        CodeStates.CHOOSING_OFFICE.state
    ):
        return

    # Обработка кнопки "Назад"
    if callback_data == "back_to_store_choice":
        logger.debug(
            f"User {user_id} chose to go back to store selection."
        )

        await back_to_store_choice(query, state)
        return

    # Обработка выбора офиса
    if callback_data.startswith("office_"):
        office_id = callback_data.replace("office_", "")

        if not is_office_available(office_id):
            await _notify_office_unavailable(query, office_id)
            return

        await _process_valid_office_choice(query, state, office_id)
        return

    # Неожиданный callback_data
    logger.warning(
        f"Unexpected callback_data '{callback_data}' "
        f"in CHOOSING_OFFICE for user {user_id}"
    )

async def process_name_input(message: types.Message, state: FSMContext):
    """Обработка ввода ФИО (только для OZON)."""
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer("❌ ФИО должно содержать от 2 до 100 символов.\nПожалуйста, введите корректное ФИО:")
        return
    await state.update_data(name=name)
    await message.answer(
        "📱 <b>Введите ваш номер телефона:</b>\n<i>Формат: +7 XXX XXX-XX-XX</i>",
        parse_mode="HTML"
    )
    await state.set_state(CodeStates.WAITING_FOR_PHONE)

    logger.debug(
        f"Set state to WAITING_FOR_PHONE after name input for user {message.from_user.id}")


async def process_phone_input(message: types.Message, state: FSMContext):
    """Хендлер для ввода телефона. Вызывает бизнес-логику."""
    data = await state.get_data()
    session_start = data.get("session_start_timestamp")
    if not is_session_allowed_to_proceed(session_start):
        await message.answer("🕗 Время на завершение заказа истекло.")
        await state.finish()
        return
    await process_final_order_data(message, state)


def register_send_code_handlers(dp):
    """Регистрация всех хендлеров, связанных с отправкой кода."""
    logger.debug("Registering send_code handlers...")

    dp.register_message_handler(
        start_send_code,
        lambda msg: msg.text == "📤 Отправить код",
        state="*"
    )

    dp.register_callback_query_handler(
        process_store_choice,
        lambda q: q.data in ["store_ozon", "store_wildberries"],
        state=CodeStates.CHOOSING_STORE
    )

    dp.register_message_handler(
        process_code_photo,
        content_types=types.ContentType.PHOTO,
        state=CodeStates.RECEIVING_CODE
    )

    dp.register_callback_query_handler(
        process_office_choice,
        lambda q: q.data.startswith(
            "office_") or q.data == "back_to_store_choice",
        state=CodeStates.CHOOSING_OFFICE
    )

    dp.register_message_handler(
        process_name_input,
        state=CodeStates.WAITING_FOR_NAME
    )

    dp.register_message_handler(
        process_phone_input,
        state=CodeStates.WAITING_FOR_PHONE
    )

    logger.debug("Send_code handlers registered.")
