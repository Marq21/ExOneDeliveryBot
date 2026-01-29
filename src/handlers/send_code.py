import logging
from pathlib import Path
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.states.code_states import CodeStates
from src.utils.config_loader import ConfigLoader
from src.bot_instance import bot
from src.handlers.start import get_main_menu
from src.services.code_processing import process_final_order_data
import aiofiles
import aiofiles.os as aios


logger = logging.getLogger(__name__)


def get_office_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора офиса с кнопками 'Назад' и 'В меню'. 'Назад' возвращает к выбору магазина."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    config = ConfigLoader.get_config()
    for office in config.get("offices", []):
        keyboard.add(
            InlineKeyboardButton(
                text=f"📍 {office['name']}",
                callback_data=f"office_{office['id']}"
            )
        )
    # Кнопка "Назад" возвращает к предыдущему шагу (выбор магазина)
    # Она будет обработана как специфичный callback в нужном состоянии или как глобальная (но лучше специфично)
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_store_choice"), # Явный вызов функции вручную
        InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")      # Обрабатывается глобально
    )
    return keyboard


async def start_send_code(message: types.Message, state: FSMContext):
    """Запуск сценария отправки кода — выбор маркетплейса."""
    logger.debug(f"🔄 Starting send_code flow for user {message.from_user.id}")
    await state.finish() # Всегда сбрасываем состояние перед началом

    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton("📦 OZON", callback_data="store_ozon"),
        InlineKeyboardButton("📦 Wildberries", callback_data="store_wildberries")
    )
    # Кнопка "В меню" - глобальная, обрабатывается в global_handlers
    # markup.row(InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")) # Убираем отсюда

    await message.answer("🛍 <b>Выберите маркетплейс:</b>", reply_markup=markup, parse_mode="HTML")
    await CodeStates.CHOOSING_STORE.set()


async def process_store_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора магазина."""
    await query.answer() # Всегда отвечаем на callback
    user_id = query.from_user.id
    callback_data = query.data
    logger.debug(f"Callback 'process_store_choice' received: {callback_data} from user {user_id}")

    # Проверяем состояние FSM
    current_state = await state.get_state()
    if current_state != CodeStates.CHOOSING_STORE.state:
        logger.warning(f"State mismatch for user {user_id}. Expected {CodeStates.CHOOSING_STORE.state}, got {current_state}")
        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        # Возвращаем главное меню
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return

    # Обработка выбора магазина
    if callback_data in ["store_ozon", "store_wildberries"]:
        store = callback_data
        await state.update_data(store=store)

        example_photo = "ozon-ok.jpg" if store == "store_ozon" else "wb.jpg"
        photo_path = Path("static") / "images" / example_photo

        caption = (
            "📸 <b>Отправьте скриншот с кодом выдачи</b>\n"
            "Для OZON: штрих-код (баркод)\n"
            "Для Wildberries: QR-код\n"
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

        await CodeStates.RECEIVING_CODE.set()
        logger.debug(f"Set state to RECEIVING_CODE for user {user_id}")
    else:
        # Неожиданный callback_data в этом состоянии
        logger.warning(f"Unexpected callback_data '{callback_data}' in CHOOSING_STORE for user {user_id}")
        await query.message.edit_text("❌ Неожиданная команда. Попробуйте заново.")
        await state.finish()
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())


async def back_to_store_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Возврат к выбору магазина.
    Эта функция вызывается явно из других хендлеров (например, process_office_choice).
    """
    await query.answer()
    logger.debug(f"Handling 'back_to_store_choice' for user {query.from_user.id}")
    # Удаляем старое сообщение с выбором офиса (если применимо)
    try:
        await query.message.delete()
    except Exception:
        pass # Игнорируем ошибки при удалении, если сообщение уже удалено

    # Вызываем основную функцию старта, она сама установит состояние
    await start_send_code(query.message, state)


async def process_code_photo(message: types.Message, state: FSMContext):
    """Обработка фото с кодом."""
    if not message.photo:
        await message.answer("📸 Пожалуйста, отправьте фото с кодом.")
        return

    processing_msg = await message.answer("🔍 Обрабатываю изображение...")

    try:
        photo = message.photo[-1] # Берем самое качественное фото
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        from src.utils.image_utils import extract_code_from_image
        code = extract_code_from_image(file_bytes.read())

        if not code:
            await message.answer(
                "❌ <b>Не удалось распознать код</b>\n"
                "Возможные причины:\n"
                "• Слишком темное/светлое фото\n"
                "• Код не в фокусе\n"
                "• Часть кода обрезана\n"
                "Попробуйте сделать более четкий скриншот.",
                parse_mode="HTML"
            )
            return

        await state.update_data(code=code)
        await bot.delete_message(message.chat.id, processing_msg.message_id)

        await message.answer(
            "✅ <b>Код распознан!</b>\n"
            f"<code>{code}</code>\n\n"
            "Теперь выберите офис, где планируете забрать заказ:",
            parse_mode="HTML",
            reply_markup=get_office_keyboard()
        )
        await CodeStates.CHOOSING_OFFICE.set()
        logger.debug(f"Set state to CHOOSING_OFFICE for user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await message.answer("❌ Произошла ошибка при обработке фото. Попробуйте еще раз.")


async def process_office_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора офиса."""
    await query.answer()
    user_id = query.from_user.id
    callback_data = query.data
    logger.debug(f"Callback 'process_office_choice' received: {callback_data} from user {user_id}")

    # Проверяем состояние FSM
    current_state = await state.get_state()
    if current_state != CodeStates.CHOOSING_OFFICE.state:
        logger.warning(f"State mismatch for user {user_id}. Expected {CodeStates.CHOOSING_OFFICE.state}, got {current_state}")
        await query.message.edit_text("❌ Ошибка состояния. Попробуйте заново.")
        await state.finish()
        # Возвращаем главное меню
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return

    # Обработка кнопки "Назад" - вызываем функцию возврата
    if callback_data == "back_to_store_choice":
        logger.debug(f"User {user_id} chose to go back to store selection.")
        await back_to_store_choice(query, state)
        return # Важно: выходим, чтобы не выполнять остальную логику

    # Обработка выбора офиса
    if callback_data.startswith("office_"):
        office_id = callback_data.replace("office_", "")
        await state.update_data(office_id=office_id)

        # Удаляем сообщение с выбором офиса
        try:
            await query.message.delete()
        except Exception:
            pass # Игнорируем ошибки при удалении

        # Получаем данные из FSM
        data = await state.get_data()
        store = data.get('store')

        if store == "store_ozon":
            await query.message.answer(
                "👤 <b>Введите ваше ФИО:</b>\n<i>Фамилия Имя Отчество (как в заказе)</i>",
                parse_mode="HTML"
            )
            await CodeStates.WAITING_FOR_NAME.set()
            logger.debug(f"Set state to WAITING_FOR_NAME for user {user_id}")
        elif store == "store_wildberries":
            await query.message.answer(
                "📱 <b>Введите ваш номер телефона:</b>\n<i>Формат: +7 XXX XXX-XX-XX</i>",
                parse_mode="HTML"
            )
            await CodeStates.WAITING_FOR_PHONE.set()
            logger.debug(f"Set state to WAITING_FOR_PHONE for user {user_id}")
        else:
            # На всякий случай, если store не определён
            logger.error(f"Store not set in FSM for user {user_id}")
            await query.message.answer("❌ Ошибка данных. Попробуйте снова.")
            await state.finish()
    else:
        # Неожиданный callback_data в этом состоянии (кроме back_to_store_choice)
        logger.warning(f"Unexpected callback_data '{callback_data}' in CHOOSING_OFFICE for user {user_id}")


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
    await CodeStates.WAITING_FOR_PHONE.set()
    logger.debug(f"Set state to WAITING_FOR_PHONE after name input for user {message.from_user.id}")

async def process_phone_input(message: types.Message, state: FSMContext):
    """Хендлер для ввода телефона. Вызывает бизнес-логику."""
    # Проверка, что FSM действительно в нужном состоянии, может быть опциональной,
    # так как она уже проверяется при регистрации хендлера.
    await process_final_order_data(message, state)


def register_send_code_handlers(dp):
    """Регистрация всех хендлеров, связанных с отправкой кода."""
    logger.debug("Registering send_code handlers...")

    # 1. Обработчик запуска сценария
    dp.register_message_handler(
        start_send_code,
        lambda msg: msg.text == "📤 Отправить код",
        state="*"  # Может быть вызван из любого состояния
    )

    # 2. Обработчик выбора магазина (только в состоянии CHOOSING_STORE)
    dp.register_callback_query_handler(
        process_store_choice,
        lambda q: q.data in ["store_ozon", "store_wildberries"],
        state=CodeStates.CHOOSING_STORE
    )

    # 3. Обработчик фото (только в состоянии RECEIVING_CODE)
    dp.register_message_handler(
        process_code_photo,
        content_types=types.ContentType.PHOTO,
        state=CodeStates.RECEIVING_CODE
    )

    # 4. Обработчик выбора офиса (только в состоянии CHOOSING_OFFICE)
    # Обрабатывает выбор офиса И кнопку "Назад"
    dp.register_callback_query_handler(
        process_office_choice,
        lambda q: q.data.startswith("office_") or q.data == "back_to_store_choice", # Оба случая
        state=CodeStates.CHOOSING_OFFICE
    )

    # 5. Обработчик ввода ФИО (только в состоянии WAITING_FOR_NAME)
    dp.register_message_handler(
        process_name_input,
        state=CodeStates.WAITING_FOR_NAME
    )

    # 6. Обработчик ввода телефона (только в состоянии WAITING_FOR_PHONE)
    dp.register_message_handler(
        process_phone_input,
        state=CodeStates.WAITING_FOR_PHONE
    )

    logger.debug("Send_code handlers registered.")