import logging
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import qrcode

logger = logging.getLogger(__name__)

def generate_barcode_image_bytesio(barcode_string: str) -> BytesIO | None: # <-- НОВОЕ ИМЯ и возвращаем BytesIO
    """
    Генерирует изображение штрих-кода (CODE128) из строки и возвращает его как BytesIO.

    Args:
        barcode_string (str): Строка, представляющая штрих-код (например, "123456789").

    Returns:
        BytesIO | None: Байтовый поток с изображением PNG или None в случае ошибки.
    """
    if not barcode_string:
        logger.error("Barcode string is empty or None.")
        return None

    try:
        # Следуем проверенному способу из старого проекта
        barcode_obj = barcode.Code128(barcode_string, writer=ImageWriter()) # Указываем barcode.Code128 напрямую
        barcode_image = barcode_obj.render() # Получаем PIL Image

        barcode_bytes = BytesIO()
        barcode_image.save(barcode_bytes, format='PNG') # Сохраняем в BytesIO
        barcode_bytes.seek(0) # Перемещаем указатель в начало

        logger.debug(f"Generated barcode image in memory for code: {barcode_string}")
        return barcode_bytes # Возвращаем BytesIO
    except Exception as e:
        logger.error(f"Error generating barcode image for string '{barcode_string}': {e}")
        return None

def generate_qr_code_image_bytesio(qr_data: str) -> BytesIO | None: # <-- НОВОЕ ИМЯ и возвращаем BytesIO
    """
    Генерирует изображение QR-кода из строки и возвращает его как BytesIO.

    Args:
        qr_data (str): Данные для QR-кода (например, "https://example.com").

    Returns:
        BytesIO | None: Байтовый поток с изображением PNG или None в случае ошибки.
    """
    if not qr_data:
        logger.error("QR data string is empty or None.")
        return None

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        logger.debug(f"Generated QR code image in memory for data: {qr_data}")
        return buffer
    except Exception as e:
        logger.error(f"Error generating QR code image for data '{qr_data}': {e}")
        return None