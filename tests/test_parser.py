import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import get_mws_full_data


def test_get_mws_full_data_returns_list():
    """Проверяем, что функция возвращает список."""
    catalog = get_mws_full_data()
    assert isinstance(catalog, list)


def test_catalog_has_expected_fields():
    """Проверяем, что у каждой модели есть обязательные поля."""
    catalog = get_mws_full_data()
    if len(catalog) == 0:
        return  # сайт недоступен — тест не фейлим

    required_fields = ["model", "price_in_1k", "price_out_1k", "unit_size"]
    for model in catalog:
        for field in required_fields:
            assert field in model, f"Модель {model.get('model', '?')} не содержит поле {field}"


def test_prices_are_numeric():
    """Проверяем, что цены — это числа (float или int)."""
    catalog = get_mws_full_data()
    if len(catalog) == 0:
        return

    for model in catalog:
        assert isinstance(model["price_in_1k"], (int, float)), \
            f"price_in_1k у {model['model']} не число: {type(model['price_in_1k'])}"
        assert isinstance(model["price_out_1k"], (int, float)), \
            f"price_out_1k у {model['model']} не число: {type(model['price_out_1k'])}"


def test_unit_size_is_string():
    """Проверяем, что unit_size есть и это непустая строка."""
    catalog = get_mws_full_data()
    if len(catalog) == 0:
        return

    for model in catalog:
        assert "unit_size" in model
        assert isinstance(model["unit_size"], str)
        assert len(model["unit_size"]) > 0