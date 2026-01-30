import logging
from datetime import datetime
import pytz
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

def is_code_acceptance_time() -> bool:
    """
    Проверяет, можно ли сейчас принимать коды от пользователей.
    Использует настройки из config['working_hours'].
    
    Returns:
        bool: True, если приём кодов разрешён.
    """
    try:
        # Получаем текущее время в часовом поясе Москвы
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        current_weekday = now.weekday()
        current_hour = now.hour
        
        # Загружаем конфигурацию
        config = ConfigLoader.get_config()
        working_hours = config.get("working_hours", {})
        
        # Сопоставляем день недели с ключом в конфиге
        weekday_map = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday"
        }
        
        day_key = weekday_map.get(current_weekday)
        if not day_key:
            logger.warning(f"Unknown weekday: {current_weekday}")
            return False
            
        # Получаем лимит времени для сегодняшнего дня
        hour_limit = working_hours.get(day_key)
        if hour_limit is None:
            logger.warning(f"No working hours defined for {day_key}")
            return False
            
        # Проверяем, не превышен ли лимит
        if current_hour < hour_limit:
            logger.debug(f"Code acceptance is allowed. Current hour: {current_hour}, limit: {hour_limit}")
            return True
        else:
            logger.info(f"Code acceptance is closed. Current hour: {current_hour}, limit: {hour_limit}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking code acceptance time: {e}")
        # В случае ошибки лучше разрешить, чтобы не блокировать пользователей
        return True
    
    
def format_working_hours_message() -> str:
    """
    Форматирует сообщение с расписанием приёма кодов из конфигурации.
    
    Returns:
        str: Готовое HTML-сообщение для отправки пользователю.
    """
    config = ConfigLoader.get_config()
    working_hours = config.get("working_hours", {})
    
    # Сопоставление ключей конфига с читаемыми названиями дней
    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    # Получаем текущий день недели
    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz).strftime("%A").lower() # 'monday', 'tuesday', etc.
    
    lines = ["<b>🕗 Расписание приёма кодов:</b>"]
    
    for config_key, readable_name in day_names.items():
        hour_limit = working_hours.get(config_key, "—")
        if hour_limit != "—":
            status = " (сейчас)" if config_key == today else ""
            lines.append(f"• <b>{readable_name}</b>: до {hour_limit}:00{status}")
        else:
            lines.append(f"• <b>{readable_name}</b>: не работает")
    
    return "\n".join(lines)