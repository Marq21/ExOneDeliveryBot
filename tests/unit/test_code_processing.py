import pytest
from src.services.code_processing import validate_phone

def test_validate_phone_valid():
    """Тест на валидный номер телефона."""
    is_valid, formatted = validate_phone("+7 (999) 123-45-67")
    assert is_valid == True
    assert formatted == "+7 (999) 123-45-67"

def test_validate_phone_invalid():
    """Тест на невалидный номер телефона."""
    is_valid, formatted = validate_phone("12345")
    assert is_valid == False
    assert formatted is None