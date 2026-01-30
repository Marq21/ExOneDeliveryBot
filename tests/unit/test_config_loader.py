import os
import pytest
from src.utils.config_loader import ConfigLoader

def test_config_loader_loads_correctly():
    """Тест на корректную загрузку конфигурации."""
    # Убедимся, что используется dev-конфиг для тестов
    os.environ["DEV"] = "true"
    
    config = ConfigLoader.get_config()
    
    # Проверяем наличие основных разделов
    assert "working_hours" in config
    assert "offices" in config
    assert "chats_config" in config
    assert "office_schedules" in config
    
    # Проверяем типы данных
    assert isinstance(config["offices"], list)
    assert isinstance(config["working_hours"], dict)
    assert len(config["offices"]) > 0
    
    # Проверяем структуру одного офиса
    office = config["offices"][0]
    assert "id" in office
    assert "name" in office
    assert "address" in office