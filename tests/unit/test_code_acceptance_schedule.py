from unittest.mock import patch
from datetime import datetime
from src.utils.code_acceptance_schedule import is_code_acceptance_time

def test_code_acceptance_allowed():
    # Мокаем текущее время на понедельник 10:00
    with patch('src.utils.code_acceptance_schedule.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 10, 0)  # Понедельник
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        assert is_code_acceptance_time() == True

def test_code_acceptance_blocked():
    # Мокаем текущее время на среду 11:00 (приём до 10:00)
    with patch('src.utils.code_acceptance_schedule.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 3, 11, 0)  # Среда
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        assert is_code_acceptance_time() == False