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
from src.handlers.start import get_main_menu
from src.services.code_processing import process_final_order_data
import aiofiles
import aiofiles.os as aios
from src.utils.store_utils import get_readable_store_name
from src.utils.keyboard_utils import (
    get_store_selection_keyboard,
    get_ozon_pvz_keyboard,
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

    # Проверяем состояние FSM
    current_state = await state.get_state()
    if current_state != CodeStates.CHOOSING_STORE.state:
        logger.warning(
            f"State mismatch for user {user_id}. Expected {CodeStates.CHOOSING_STORE.state}, got {current_state}")
        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        # Возвращаем главное меню
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return

    # Обработка выбора магазина
    if callback_data == "store_ozon":
        await state.update_data(store="store_ozon")
        await state.set_state(CodeStates.CHOOSING_OZON_PVZ)
        await query.message.answer(
            "📍 <b>Выберите пункт выдачи OZON:</b>",
            reply_markup=get_ozon_pvz_keyboard(),
            parse_mode="HTML"
        )
        logger.debug(f"Set state to CHOOSING_OZON_PVZ for user {user_id}")

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
            logger.error(f"Error sending example photo: {e}")
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


async def process_ozon_pvz_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора ПВЗ OZON."""
    await query.answer()
    user_id = query.from_user.id
    pvz_id = query.data.replace("ozon_pvz_", "")
    logger.debug(f"User {user_id} selected OZON PVZ: {pvz_id}")

    # Сохраняем выбранный ПВЗ
    await state.update_data(ozon_pvz_id=pvz_id)

    # Получаем описание и пример
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
        else:
            await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")
    except Exception as e:
        logger.error(
            f"Error sending OZON example photo after PVZ selection: {e}")
        await bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="HTML")

    await state.set_state(CodeStates.RECEIVING_CODE)
    logger.debug(
        f"Set state to RECEIVING_CODE after PVZ selection for user {user_id}")


async def back_to_store_from_pvz(query: types.CallbackQuery, state: FSMContext):
    """Возврат от выбора ПВЗ OZON к выбору магазина."""
    await query.answer()
    logger.debug(
        f"User {query.from_user.id} going back from PVZ to store selection.")
    # Сбрасываем всё и перезапускаем выбор магазина
    await start_send_code(query.message, state)


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


async def process_office_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора офиса."""
    await query.answer()
    user_id = query.from_user.id
    callback_data = query.data
    logger.debug(
        f"Callback 'process_office_choice' received: {callback_data} from user {user_id}")

    # Проверяем состояние FSM
    current_state = await state.get_state()
    if current_state != CodeStates.CHOOSING_OFFICE.state:
        logger.warning(
            f"State mismatch for user {user_id}. Expected {CodeStates.CHOOSING_OFFICE.state}, got {current_state}")
        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        # Возвращаем главное меню
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return

    # Обработка кнопки "Назад" - вызываем функцию возврата
    if callback_data == "back_to_store_choice":
        logger.debug(f"User {user_id} chose to go back to store selection.")
        await back_to_store_choice(query, state)
        return  # Важно: выходим, чтобы не выполнять остальную логику

    # Обработка выбора офиса
    if callback_data.startswith("office_"):
        office_id = callback_data.replace("office_", "")
        await state.update_data(office_id=office_id)

        # Удаляем сообщение с выбором офиса
        try:
            await query.message.delete()
        except Exception:
            pass  # Игнорируем ошибки при удалении

        # Получаем данные из FSM
        data = await state.get_data()
        store = data.get('store')

        if store == "store_ozon":
            await query.message.answer(
                "👤 <b>Введите ваше ФИО:</b>\n<i>Фамилия Имя Отчество</i>",
                parse_mode="HTML"
            )
            await state.set_state(CodeStates.WAITING_FOR_NAME)

            logger.debug(f"Set state to WAITING_FOR_NAME for user {user_id}")
        elif store == "store_wildberries":
            await query.message.answer(
                "📱 <b>Введите ваш номер телефона:</b>\n<i>Формат: +7 XXX XXX-XX-XX</i>",
                parse_mode="HTML"
            )
            await state.set_state(CodeStates.WAITING_FOR_PHONE)
            logger.debug(f"Set state to WAITING_FOR_PHONE for user {user_id}")
        else:
            # На всякий случай, если store не определён
            logger.error(f"Store not set in FSM for user {user_id}")
            await query.message.answer("❌ Ошибка данных. Попробуйте снова.")
            await state.finish()
    else:
        # Неожиданный callback_data в этом состоянии (кроме back_to_store_choice)
        logger.warning(
            f"Unexpected callback_data '{callback_data}' in CHOOSING_OFFICE for user {user_id}")


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

    # Обработчик запуска сценария
    dp.register_message_handler(
        start_send_code,
        lambda msg: msg.text == "📤 Отправить код",
        state="*"  # Может быть вызван из любого состояния
    )

    # Обработчик выбора магазина (только в состоянии CHOOSING_STORE)
    dp.register_callback_query_handler(
        process_store_choice,
        lambda q: q.data in ["store_ozon", "store_wildberries"],
        state=CodeStates.CHOOSING_STORE
    )

    # Обработчик выбора адреса для пвз озон
    dp.register_callback_query_handler(
        process_ozon_pvz_choice,
        lambda q: q.data.startswith("ozon_pvz_"),
        state=CodeStates.CHOOSING_OZON_PVZ
    )

    # Обработчик кнопки "назад" для клавиатуры выбора адреса пвз озон
    dp.register_callback_query_handler(
        back_to_store_from_pvz,
        lambda q: q.data == "back_to_store_choice",
        state=CodeStates.CHOOSING_OZON_PVZ
    )

    # Обработчик фото (только в состоянии RECEIVING_CODE)
    dp.register_message_handler(
        process_code_photo,
        content_types=types.ContentType.PHOTO,
        state=CodeStates.RECEIVING_CODE
    )

    # Обработчик выбора офиса (только в состоянии CHOOSING_OFFICE)
    # Обрабатывает выбор офиса И кнопку "Назад"
    dp.register_callback_query_handler(
        process_office_choice,
        lambda q: q.data.startswith(
            "office_") or q.data == "back_to_store_choice",  # Оба случая
        state=CodeStates.CHOOSING_OFFICE
    )

    # Обработчик ввода ФИО (только в состоянии WAITING_FOR_NAME)
    dp.register_message_handler(
        process_name_input,
        state=CodeStates.WAITING_FOR_NAME
    )

    # Обработчик ввода телефона (только в состоянии WAITING_FOR_PHONE)
    dp.register_message_handler(
        process_phone_input,
        state=CodeStates.WAITING_FOR_PHONE
    )

    logger.debug("Send_code handlers registered.")
