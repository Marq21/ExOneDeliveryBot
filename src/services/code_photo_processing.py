import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.bot_instance import bot
from src.utils.image_utils import extract_code_from_image
from src.utils.code_validator import is_code_valid_for_store, get_example_image_path
import aiofiles
import aiofiles.os as aios

from src.utils.store_utils import get_readable_store_name


logger = logging.getLogger(__name__)

async def _extract_code_from_message_photo(message: types.Message) -> str | None:
    """Извлекает код из фотографии в сообщении."""
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    return extract_code_from_image(file_bytes.read())

async def _handle_no_code_detected(message: types.Message, processing_msg: types.Message):
    """Обрабатывает случай, когда код не распознан."""
    await bot.delete_message(message.chat.id, processing_msg.message_id)
    await message.answer(
        "❌ <b>Не удалось распознать код</b>\n"
        "Возможные причины:\n"
        "• Слишком темное/светлое фото\n"
        "• Код не в фокусе\n"
        "• Часть кода обрезана\n\n"
        "Попробуйте сделать более четкий скриншот.",
        parse_mode="HTML"
    )


async def _validate_extracted_code(code: str, state: FSMContext) -> tuple[bool, str, bytes | None]:
    """Валидирует код и возвращает результат, сообщение об ошибке и пример изображения."""
    data = await state.get_data()
    current_store = data.get('store')

    # ✅ ШАГ 1: Проверяем, подходит ли код под ВЫБРАННЫЙ магазин
    if is_code_valid_for_store(code, current_store):
        return True, "", None  # Успех!

    # ❌ ШАГ 2: Код не подходит под выбранный магазин → определяем, откуда он на самом деле
    if is_code_valid_for_store(code, "store_ozon"):
        actual_store_key = "store_ozon"
    elif is_code_valid_for_store(code, "store_wildberries"):
        actual_store_key = "store_wildberries"
    else:
        return False, "❌ Не удалось определить тип кода. Пожалуйста, отправьте чёткий скриншот.", None

    # Формируем сообщение
    selected_store_name = get_readable_store_name(current_store)
    actual_store_name = get_readable_store_name(actual_store_key)

    error_message = (
        f"❌ <b>Ошибка!</b>\n"
        f"Вы выбрали <b>{selected_store_name}</b>, но отправили код от <b>{actual_store_name}</b>.\n"
        f"Пожалуйста, отправьте правильный код, как на фото выше."
    )

    # ✅ Пример должен быть для ТОГО МАГАЗИНА, который пользователь ВЫБРАЛ (current_store),
    # чтобы напомнить, как должен выглядеть правильный код.
    example_image_path = get_example_image_path(current_store)
    example_image = None
    if example_image_path and await aios.path.exists(example_image_path):
        async with aiofiles.open(example_image_path, "rb") as f:
            example_image = await f.read()

    return False, error_message, example_image


async def _handle_invalid_code(
    message: types.Message,
    processing_msg: types.Message,
    error_message: str,
    example_image: bytes | None
):
    """Отправляет пользователю сообщение об ошибке валидации."""
    await bot.delete_message(message.chat.id, processing_msg.message_id)
    if example_image:
        await message.answer_photo(photo=example_image, caption=error_message, parse_mode="HTML")
    else:
        await message.answer(error_message, parse_mode="HTML")

async def _handle_valid_code(message: types.Message, processing_msg: types.Message, state: FSMContext, code: str):
    """Обрабатывает успешно распознанный и валидный код."""
    from src.utils.keyboard_utils import get_office_keyboard# Импортируем здесь, чтобы избежать циклического импорта
    from src.states.code_states import CodeStates

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

async def process_final_code_photo(message: types.Message, state: FSMContext):
    """
    Основная функция обработки фото с кодом.
    Вызывается из хендлера process_code_photo в send_code.py.
    """
    processing_msg = await message.answer("🔍 Обрабатываю изображение...")

    try:
        # --- ШАГ 1: Извлечение кода ---
        code = await _extract_code_from_message_photo(message)
        if not code:
            await _handle_no_code_detected(message, processing_msg)
            return

        # --- ШАГ 2: Валидация кода ---
        is_valid, error_message, example_image = await _validate_extracted_code(code, state)
        if not is_valid:
            await _handle_invalid_code(message, processing_msg, error_message, example_image)
            return

        # --- ШАГ 3: Успешная обработка ---
        await _handle_valid_code(message, processing_msg, state, code)

    except Exception as e:
        logger.error(f"Error in process_final_code_photo: {e}")
        await bot.delete_message(message.chat.id, processing_msg.message_id)
        await message.answer("❌ Произошла ошибка при обработке фото. Попробуйте еще раз.")