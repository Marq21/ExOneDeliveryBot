import pytest
from src.utils.code_validator import is_code_valid_for_store

def test_ozon_code_validation():
    assert is_code_valid_for_store("12345*6789", "store_ozon") == True
    assert is_code_valid_for_store("12345_6789", "store_ozon") == False

def test_wb_code_validation():
    assert is_code_valid_for_store("12345_6789", "store_wildberries") == True
    assert is_code_valid_for_store("12345*6789", "store_wildberries") == False