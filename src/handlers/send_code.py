import cv2
import numpy as np
from pyzbar import pyzbar
from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.states.code_states import CodeStates
from src.utils.config_loader import ConfigLoader
from src.bot_instance import bot
import aiofiles
import aiofiles.os as aios
from pathlib import Path
import logging
from src.handlers.start import get_main_menu


logger = logging.getLogger(__name__)

def extract_code_from_image(image_bytes: bytes) -> str | None:
    """Извлечение кода из изображения"""
    try:
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            logger.error("Failed to decode image")
            return None
            
        decoded_objects = pyzbar.decode(image)
        for obj in decoded_objects:
            if obj.type in ('CODE128', 'QRCODE'):
                return obj.data.decode('utf-8')
        return None
    except Exception as e:
        logger.error(f"Error extracting code from image: {e}")
        return None

def get_office_keyboard():
    """Создание клавиатуры для выбора офиса"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    config = ConfigLoader.get_config()
    
    for office in config.get("offices", []):
        keyboard.add(
            InlineKeyboardButton(
                text=f"📍 {office['name']}",
                callback_data=f"office_{office['id']}"
            )
        )
    
    # Добавляем кнопку возврата
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_store_choice"),
        InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")
    )
    
    return keyboard


async def start_send_code(message: types.Message, state: FSMContext):
    """Начало процесса отправки кода"""
    logger.debug(f"🔄 Starting send_code flow for user {message.from_user.id}")

    current_state = await state.get_state()
    if current_state:
        await state.reset_state() 

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📦 OZON", callback_data="store_ozon"),
        InlineKeyboardButton("📦 Wildberries", callback_data="store_wildberries"),
        InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")
    )
    
    await message.answer(
        "🛍 <b>Выберите маркетплейс:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await CodeStates.CHOOSING_STORE.set()

    current = await state.get_state()
    logger.debug(f"State after set: {current}")


async def process_store_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора магазина"""

    logger.debug(f"📥 Callback received: data={query.data}, user_id={query.from_user.id}")
    current_state = await state.get_state()
    logger.debug(f"🔍 Current FSM state: {current_state}")

    if query.data == "back_to_menu":
        logger.debug("↩️ Handling 'back_to_menu'")
        await query.answer()
        await state.finish()
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return
    
    logger.debug(f"✅ Processing store choice: {query.data}")

    store = query.data
    await state.update_data(store=store)
    
    example_photo = "ozon-ok.jpg" if store == "store_ozon" else "wb.jpg"
    photo_path = Path("static") / "images" / example_photo
    
    caption = (
        "📸 <b>Отправьте скриншот с кодом выдачи</b>\n\n"
        "Для OZON: штрих-код (баркод)\n"
        "Для Wildberries: QR-код\n\n"
        "<i>Убедитесь, что код хорошо виден на фото</i>"
    )
    
    try:
        # Асинхронная проверка существования файла
        if await aios.path.exists(photo_path):
            # Асинхронное чтение файла
            async with aiofiles.open(photo_path, "rb") as f:
                photo_bytes = await f.read()
            
            # Отправка фото
            await bot.send_photo(
                chat_id=query.from_user.id,
                photo=photo_bytes,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            await query.message.answer(caption, parse_mode="HTML")
            logger.warning(f"Example photo not found: {photo_path}")
    except Exception as e:
        logger.error(f"Error sending example photo: {e}")
        await query.message.answer(caption, parse_mode="HTML")
    
    await CodeStates.RECEIVING_CODE.set()
    await query.answer()


async def back_to_store_choice(query: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору магазина"""
    logger.debug("↩️ Callback: back_to_store_choice")
    await start_send_code(query.message, state)
    await query.answer()

async def process_code_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии с кодом"""
    if not message.photo:
        await message.answer("📸 Пожалуйста, отправьте фото с кодом.")
        return
    
    # Отправляем уведомление о начале обработки
    processing_msg = await message.answer("🔍 Обрабатываю изображение...")
    
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        
        code = extract_code_from_image(file_bytes.read())
        if not code:
            await message.answer(
                "❌ <b>Не удалось распознать код</b>\n\n"
                "Возможные причины:\n"
                "• Слишком темное/светлое фото\n"
                "• Код не в фокусе\n"
                "• Часть кода обрезана\n\n"
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
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке фото. Попробуйте еще раз."
        )

async def process_office_choice(query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора офиса"""
    if query.data == "back_to_store_choice":
        await back_to_store_choice(query, state)
        return
    elif query.data == "back_to_menu":
        await query.answer()
        await state.finish()
        await query.message.answer("Выберите действие:", reply_markup=get_main_menu())
        return
    
    office_id = query.data.replace("office_", "")
    await state.update_data(office_id=office_id)
    
    async with state.get_data() as data:
        store = data.get('store')
        
        if store == "store_ozon":
            await query.message.answer(
                "👤 <b>Введите ваше ФИО:</b>\n\n"
                "<i>Фамилия Имя Отчество (как в заказе)</i>",
                parse_mode="HTML"
            )
            await CodeStates.WAITING_FOR_NAME.set()
        elif store == "store_wildberries":
            await query.message.answer(
                "📱 <b>Введите ваш номер телефона:</b>\n\n"
                "<i>Формат: +7 XXX XXX-XX-XX или 7XXXXXXXXXX</i>",
                parse_mode="HTML"
            )
            await CodeStates.WAITING_FOR_PHONE.set()
    
    await query.answer()

async def process_name_input(message: types.Message, state: FSMContext):
    """Обработка ввода ФИО"""
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(
            "❌ ФИО должно содержать от 2 до 100 символов.\n"
            "Пожалуйста, введите корректное ФИО:"
        )
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        "📱 <b>Введите ваш номер телефона:</b>\n\n"
        "<i>Формат: +7 XXX XXX-XX-XX или 7XXXXXXXXXX</i>",
        parse_mode="HTML"
    )
    await CodeStates.WAITING_FOR_PHONE.set()

async def process_phone_input(message: types.Message, state: FSMContext):
    """Обработка ввода номера телефона"""
    phone = message.text.strip()
    
    # Очистка номера
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Проверка формата
    if not cleaned or not cleaned.startswith('7') or len(cleaned) != 11:
        await message.answer(
            "❌ <b>Неверный формат номера</b>\n\n"
            "Номер должен:\n"
            "• Начинаться с 7\n"
            "• Содержать 11 цифр\n"
            "• Быть в формате: +7 XXX XXX-XX-XX\n\n"
            "Пожалуйста, введите корректный номер:",
            parse_mode="HTML"
        )
        return
    
    # Форматирование для отображения
    formatted_phone = f"+7 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:9]}-{cleaned[9:11]}"
    
    await state.update_data(phone=formatted_phone, cleaned_phone=cleaned)
    
    # Получение всех данных
    async with state.get_data() as data:
        store = data.get('store')
        code = data.get('code')
        name = data.get('name', '')
        office_id = data.get('office_id')
        
        config = ConfigLoader.get_config()
        
        # Поиск офиса
        office_name = office_id
        for office in config.get("offices", []):
            if office["id"] == office_id:
                office_name = office["name"]
                break
        
        # Определение целевого чата
        target_chat = None
        marketplace_key = "ozon" if store == "store_ozon" else "wb"
        
        if "chats_config" in config and office_id in config["chats_config"]:
            target_chat = config["chats_config"][office_id].get(marketplace_key)
        
        if not target_chat:
            logger.error(f"Target chat not found for office {office_id}, marketplace {marketplace_key}")
            await message.answer(
                "❌ Ошибка конфигурации. Пожалуйста, сообщите администратору."
            )
            return
        
        # Формирование сообщения
        if store == "store_ozon":
            caption = (
                f"🛍 <b>OZON - НОВЫЙ КОД</b>\n\n"
                f"👤 <b>ФИО:</b> {name}\n"
                f"📱 <b>Телефон:</b> {formatted_phone}\n"
                f"🎫 <b>Код:</b> <code>{code}</code>\n"
                f"🏢 <b>Офис:</b> {office_name}\n\n"
                f"👤 <b>Отправитель:</b> @{message.from_user.username or message.from_user.id}"
            )
        else:
            caption = (
                f"🛍 <b>Wildberries - НОВЫЙ КОД</b>\n\n"
                f"📱 <b>Телефон:</b> {formatted_phone}\n"
                f"🎫 <b>Код:</b> <code>{code}</code>\n"
                f"🏢 <b>Офис:</b> {office_name}\n\n"
                f"👤 <b>Отправитель:</b> @{message.from_user.username or message.from_user.id}"
            )
        
        try:
            # Отправка в рабочий чат
            await bot.send_message(target_chat, caption, parse_mode="HTML")
            
            # Подтверждение пользователю
            await message.answer(
                "✅ <b>Код успешно отправлен!</b>\n\n"
                f"🏢 <b>Офис:</b> {office_name}\n"
                f"📅 <b>Статус:</b> Передано в отдел доставки\n\n"
                "<i>Ожидайте уведомления о готовности заказа</i>",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error sending code to chat: {e}")
            await message.answer(
                "❌ Произошла ошибка при отправке кода. Попробуйте позже."
            )
    
    await state.finish()


async def handle_unknown_callback(query: types.CallbackQuery):
    """Обработка неизвестных callback-запросов"""
    await query.answer("⚠️ Это действие сейчас недоступно. Начните заново.", show_alert=True)


def register_send_code_handlers(dp: Dispatcher):
    """Регистрация обработчиков"""
    dp.register_message_handler(
        start_send_code,
        lambda msg: msg.text == "📤 Отправить код",
        state="*"
    )
    
    dp.register_callback_query_handler(
        process_store_choice,
        lambda q: q.data in ["store_ozon", "store_wildberries", "back_to_menu"],
        # state=[CodeStates.CHOOSING_STORE, None] 
        state="*"
    )
    
    dp.register_callback_query_handler(
        back_to_store_choice,
        lambda q: q.data == "back_to_store_choice",
        state="*"
    )
    
    dp.register_message_handler(
        process_code_photo,
        content_types=types.ContentTypes.PHOTO,
        state=CodeStates.RECEIVING_CODE
    )
    
    dp.register_callback_query_handler(
        process_office_choice,
        lambda q: q.data.startswith("office_") or q.data in ["back_to_store_choice", "back_to_menu"],
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

    # Обработчик для всех остальных callback-запросов
    dp.register_callback_query_handler(
        handle_unknown_callback,
        state="*"
    )