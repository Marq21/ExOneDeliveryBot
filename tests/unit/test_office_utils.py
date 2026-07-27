from datetime import datetime

from src.utils.config_loader import ConfigLoader
from src.utils import office_utils


def setup_function():
    """
    Сбрасываем кэш ConfigLoader перед каждым тестом.
    """
    ConfigLoader._cache = {}
    ConfigLoader._last_load = datetime.min


def _mock_offices(monkeypatch, offices):
    monkeypatch.setattr(
        "src.utils.office_utils.ConfigLoader.get_config",
        lambda: {"offices": offices}
    )


def test_is_office_available_true(monkeypatch):
    offices = [
        {
            "id": "Ex.One",
            "name": "Центр",
            "address": "ул. Университетская 39А"
        }
    ]

    _mock_offices(monkeypatch, offices)

    assert office_utils.is_office_available("Ex.One") is True


def test_is_office_available_false(monkeypatch):
    offices = [
        {
            "id": "Ex.One",
            "name": "Центр",
            "address": "ул. Университетская 39А"
        }
    ]

    _mock_offices(monkeypatch, offices)

    assert office_utils.is_office_available("Ex.One#8") is False


def test_get_office_by_id(monkeypatch):
    offices = [
        {
            "id": "Ex.One",
            "name": "Центр",
            "address": "ул. Университетская 39А"
        },
        {
            "id": "Ex.Two",
            "name": "Гора",
            "address": "проспект Восточный 100"
        }
    ]

    _mock_offices(monkeypatch, offices)

    office = office_utils.get_office_by_id("Ex.Two")

    assert office is not None
    assert office["name"] == "Гора"


def test_get_office_by_id_not_found(monkeypatch):
    offices = [
        {
            "id": "Ex.One",
            "name": "Центр",
            "address": "ул. Университетская 39А"
        }
    ]

    _mock_offices(monkeypatch, offices)

    assert office_utils.get_office_by_id("Ex.One#10") is None