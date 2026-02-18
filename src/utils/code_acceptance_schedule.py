import logging
from datetime import datetime
import pytz
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

GRACE_PERIOD_MINUTES = 15


def is_session_allowed_to_proceed(session_start_timestamp: int | None = None) -> bool:
    """
    Проверяет, может ли пользователь начать или завершить отправку кода.

    Args:
        session_start_timestamp (int | None):
            - None → проверка для СТАРТА (обычное рабочее время).
            - int → проверка для ЗАВЕРШЕНИЯ (рабочее время + grace period).

    Returns:
        bool: True, если действие разрешено.
    """
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    current_weekday = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    now_minutes = current_hour * 60 + current_minute

    config = ConfigLoader.get_config()
    working_hours = config.get("working_hours", {})

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

    hour_limit = working_hours.get(day_key)
    if hour_limit is None:
        logger.warning(f"No working hours defined for {day_key}")
        return False

    limit_minutes = hour_limit * 60

    # === Случай 1: Проверка для СТАРТА сценария ===
    if session_start_timestamp is None:
        allowed = now_minutes < limit_minutes
        logger.debug(
            f"[START] Now: {now_minutes} min, limit: {limit_minutes} min → allowed: {allowed}")
        return allowed

    # === Случай 2: Проверка для ЗАВЕРШЕНИЯ сценария ===
    try:
        session_start_dt = datetime.fromtimestamp(
            session_start_timestamp, tz=moscow_tz)
        session_start_minutes = session_start_dt.hour * 60 + session_start_dt.minute
        started_in_time = session_start_minutes < limit_minutes
    except (OSError, ValueError, OverflowError):
        logger.warning(
            f"Invalid session_start_timestamp: {session_start_timestamp}")
        return False

    if not started_in_time:
        logger.info("Session started after working hours — denied.")
        return False

    # Grace period: +15 минут после окончания приёма
    grace_end_minutes = limit_minutes + GRACE_PERIOD_MINUTES
    allowed = now_minutes <= grace_end_minutes
    logger.debug(
        f"[FINISH] Started at {session_start_minutes} min (in time: {started_in_time}), "
        f"now: {now_minutes} min, grace end: {grace_end_minutes} min → allowed: {allowed}"
    )
    return allowed


def format_working_hours_message() -> str:
    """
    Форматирует сообщение с расписанием приёма кодов из конфигурации.
    """
    config = ConfigLoader.get_config()
    working_hours = config.get("working_hours", {})

    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }

    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz).strftime("%A").lower()

    lines = ["<b>🕗 Расписание приёма кодов:</b>"]
    for config_key, readable_name in day_names.items():
        hour_limit = working_hours.get(config_key, "—")
        if hour_limit != "—":
            status = " (сейчас)" if config_key == today else ""
            lines.append(
                f"• <b>{readable_name}</b>: до {hour_limit}:00{status}")
        else:
            lines.append(f"• <b>{readable_name}</b>: не работает")

    return "\n".join(lines)
