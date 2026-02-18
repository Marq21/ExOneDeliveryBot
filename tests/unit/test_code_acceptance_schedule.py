from datetime import datetime
import pytz
from freezegun import freeze_time
from src.utils.code_acceptance_schedule import is_session_allowed_to_proceed

def _mock_config(monkeypatch, working_hours):
    # ОЧИЩАЕМ КЭШ ConfigLoader
    from src.utils.config_loader import ConfigLoader
    ConfigLoader._cache = {}
    ConfigLoader._last_load = datetime.min

    monkeypatch.setattr("src.utils.config_loader.ConfigLoader.get_config", lambda: {
        "working_hours": working_hours,
        "offices": [],
        "ozon_pvzs": [],
        "chats_config": {},
        "office_schedules": {},
        "code_validation_rules": {},
        "admin_error_chat_id": "123"
    })


def test_grace_period_logic_with_mock_config(monkeypatch):
    _mock_config(monkeypatch, {"monday": 16})
    MOSCOW_TZ = pytz.timezone('Europe/Moscow')

    late_start = int(MOSCOW_TZ.localize(datetime(2024, 1, 1, 16, 5)).timestamp())
    with freeze_time("2024-01-01 16:10:00", tz_offset=3):
        assert is_session_allowed_to_proceed(late_start) is False