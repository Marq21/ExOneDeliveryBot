from io import BytesIO
import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.utils.generate_codes import generate_barcode_image_bytesio, generate_qr_code_image_bytesio # <-- ИМПОРТИРУЕМ НОВОЕ
from src.utils.config_loader import ConfigLoader
from src.bot_instance import bot
from src.handlers.start import get_main_menu

logger = logging.getLogger(__name__)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (бизнес-логика) ---

def validate_phone(phone_text: str) -> tuple[bool, str | None]:
    """Проверяет формат телефона. Возвращает (успешно?, отформатированный_телефон или None)."""
    cleaned_phone = ''.join(filter(str.isdigit, phone_text))
    if not cleaned_phone.startswith('7') or len(cleaned_phone) != 11:
        return False, None
    formatted_phone = f"+7 ({cleaned_phone[1:4]}) {cleaned_phone[4:7]}-{cleaned_phone[7:9]}-{cleaned_phone[9:11]}"
    return True, formatted_phone

async def get_order_data_and_config(state: FSMContext) -> dict | None:
    data = await state.get_data()
    store = data.get("store")
    code = data.get("code")
    name = data.get("name", "")
    office_id = data.get("office_id")
    ozon_pvz_id = data.get("ozon_pvz_id")

    if not all([store, code, office_id]):
        logger.error("Missing required order data in FSM.")
        return None

    if store == "store_ozon" and not name:
        logger.error("Name missing for OZON order.")
        return None

    config = ConfigLoader.get_config()
    office_name = next((o["name"] for o in config["offices"] if o["id"] == office_id), office_id)

    target_chat = None
    if store == "store_ozon":
        # Используем специфичные ключи для OZON по ПВЗ
        if ozon_pvz_id == "trolleibusnaya":
            chat_key = "ozon_trolleibusnaya"
        elif ozon_pvz_id == "rostselmash":
            chat_key = "ozon_rostselmash"
        else:
            logger.error(f"Unknown OZON PVZ ID: {ozon_pvz_id}")
            return None
        target_chat = config["chats_config"].get(office_id, {}).get(chat_key)
    else:  # store_wildberries
        target_chat = config["chats_config"].get(office_id, {}).get("wb")

    if not target_chat:
        logger.error(f"Target chat not found for office={office_id}, store={store}, pvz={ozon_pvz_id}")
        return None

    return {
        "store": store,
        "code": code,
        "name": name,
        "office_name": office_name,
        "target_chat": target_chat,
        "ozon_pvz_id": ozon_pvz_id  # для логов
    }


def prepare_image_and_caption_bytesio(order_data: dict) -> tuple[BytesIO | None, str | None]:
    """Генерирует изображение (как BytesIO) и текст. Возвращает (image_bytesio, caption_text) или (None, None)."""
    code = order_data["code"]
    store = order_data["store"]
    name = order_data["name"]
    phone = order_data["formatted_phone"]
    office_name = order_data["office_name"]

    image_buffer = None
    caption_text = ""

    if store == "store_ozon":
        logger.debug(f"Generating barcode image for OZON code: {code}")
        image_buffer = generate_barcode_image_bytesio(code)
        if image_buffer:
            caption_text = (
                f"Код для получения OZON: {code}\n"
                f"ФИО: {name}\n"
                f"Телефон: {phone}\n\n"
                f"Пункт: {office_name}"
            )
        else:
            logger.error(f"generate_barcode_image_bytesio returned None for OZON code: {code}") # <-- Лог как было
    else:
        logger.debug(f"Generating QR code image for WB  {code}")
        image_buffer = generate_qr_code_image_bytesio(code)
        if image_buffer:
            caption_text = (
                f"Код для получения Wildberries:\n"
                f"{code}\n"
                f"Телефон: {phone}\n\n"
                f"Пункт: {office_name}"
            )
        else:
            logger.error(f"generate_qr_code_image_bytesio returned None for WB  {code}")

    if not image_buffer:
        logger.error(f"Failed to generate image for {store} code: {code}")
        return None, None

    return image_buffer, caption_text

async def send_image_to_target_chat_bytesio(target_chat: str, image_bytesio: BytesIO, caption: str) -> bool:
    """Отправляет изображение (из BytesIO) в целевой чат. Возвращает True при успехе."""
    try:
        # Используем InputFile.from_io для отправки содержимого BytesIO
        input_file = types.InputFile(image_bytesio, filename='code_image.png')
        await bot.send_photo(chat_id=target_chat, photo=input_file, caption=caption)
        logger.info(f"Photo sent successfully to {target_chat}")
        return True
    except Exception as e:
        logger.error(f"Failed to send photo via bot.send_photo to {target_chat}: {e}")
        
        if "Image_process_failed" in str(e):
            logger.error("Telegram reported Image_process_failed. Generated image might be corrupt.")

        if "File must be non-empty" in str(e):
             logger.error("Telegram reported File must be non-empty. Generated BytesIO might be empty.")
        return False

async def send_confirmation_to_user(message: types.Message, office_name: str):
    """Отправляет подтверждение пользователю."""
    
    await message.answer(
        "✅ <b>Код успешно отправлен!</b>\n"
        f"🏢 <b>Офис:</b> {office_name}\n",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


async def process_final_order_data(message: types.Message, state: FSMContext):
    """
    Основная функция обработки финальных данных заказа (телефон, генерация, отправка).
    Вызывается из хендлера process_phone_input в send_code.py.
    """
    phone_text = message.text.strip()

    is_valid, formatted_phone = validate_phone(phone_text)
    if not is_valid:
        await message.answer(
            "❌ <b>Неверный формат номера</b>\n"
            "• Начинаться с 7\n"
            "• Содержать 11 цифр\n"
            "• Пример: +7 XXX XXX-XX-XX\n\n"
            "Пожалуйста, введите корректный номер:",
            parse_mode="HTML"
        )
        return

    # 2. Сохранение в FSM
    cleaned_phone = ''.join(filter(str.isdigit, phone_text))
    await state.update_data(phone=formatted_phone, cleaned_phone=cleaned_phone)

    # 3. Показать прогресс
    progress_msg = await message.answer("🔄 Отправляю данные...")

    # 4. Получить данные и конфиг
    order_data = await get_order_data_and_config(state)
    if not order_data:
        await bot.delete_message(message.chat.id, progress_msg.message_id)
        await message.answer("❌ Ошибка конфигурации или данных. Пожалуйста, сообщите администратору.")
        await state.finish()
        return

    # 5. Подставить отформатированный телефон в order_data
    order_data["formatted_phone"] = formatted_phone

    # 6. Подготовить изображение (BytesIO) и текст
    image_buffer, caption_text = prepare_image_and_caption_bytesio(order_data)
    if not image_buffer:
        await bot.delete_message(message.chat.id, progress_msg.message_id)
        await message.answer("❌ Ошибка: не удалось сгенерировать изображение кода.")
        await state.finish()
        return

    # 7. Отправить в рабочий чат (BytesIO)
    send_success = await send_image_to_target_chat_bytesio(
        target_chat=order_data["target_chat"],
        image_bytesio=image_buffer,
        caption=caption_text
    )

    # 8. Обработка результата отправки
    await bot.delete_message(message.chat.id, progress_msg.message_id)
    if send_success:
        # 8a. Успех
        await send_confirmation_to_user(message, order_data["office_name"])
        logger.info(f"Code sent successfully by user {message.from_user.id} to {order_data['target_chat']}")
    else:
        # 8b. Ошибка отправки
        await message.answer("❌ Произошла ошибка при отправке изображения кода. Попробуйте позже.")

    await state.finish()