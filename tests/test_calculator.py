import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator import calculate_mws_cost


def test_basic_calculation():
    """Базовый расчёт: ровно 1000 токенов, цена 1.0 за 1000, unit_size=100."""
    result = calculate_mws_cost(
        price_in_1k=1.0,
        price_out_1k=1.0,
        tokens_in=1000,
        tokens_out=1000,
        unit_size=100
    )
    assert result == 2.0


def test_zero_tokens():
    """Ноль токенов — стоимость должна быть 0."""
    result = calculate_mws_cost(
        price_in_1k=1.098,
        price_out_1k=1.098,
        tokens_in=0,
        tokens_out=0,
        unit_size=100
    )
    assert result == 0.0


def test_non_multiple_tokens():
    """Некратное количество токенов — округление вверх."""
    # 150 токенов при unit_size=100 → ceil(150/100)=2 единицы входа
    # 250 токенов при unit_size=100 → ceil(250/100)=3 единицы выхода
    # unit_price = (1.0/1000)*100 = 0.1
    # total = 2*0.1 + 3*0.1 = 0.5
    result = calculate_mws_cost(
        price_in_1k=1.0,
        price_out_1k=1.0,
        tokens_in=150,
        tokens_out=250,
        unit_size=100
    )
    assert result == 0.5


def test_embedding_model_unit_size():
    """Embedding-модель: unit_size=1000, только входные токены."""
    # 100 токенов при unit_size=1000 → ceil(100/1000)=1 единица
    # unit_price = (0.0366/1000)*1000 = 0.0366
    result = calculate_mws_cost(
        price_in_1k=0.0366,
        price_out_1k=0.0,
        tokens_in=100,
        tokens_out=0,
        unit_size=1000
    )
    assert result == 0.0366


def test_different_prices_in_out():
    """Разные цены для входа и выхода."""
    # 1000 токенов входа по 2.0, 500 токенов выхода по 4.0, unit_size=100
    # unit_price_in = (2.0/1000)*100 = 0.2, ceil(1000/100)=10 → 10*0.2=2.0
    # unit_price_out = (4.0/1000)*100 = 0.4, ceil(500/100)=5 → 5*0.4=2.0
    # total = 4.0
    result = calculate_mws_cost(
        price_in_1k=2.0,
        price_out_1k=4.0,
        tokens_in=1000,
        tokens_out=500,
        unit_size=100
    )
    assert result == 4.0


def test_rounding_up_edges():
    """Пограничный случай: 101 токен при unit_size=100 → 2 единицы."""
    # ceil(101/100)=2, ceil(0/100)=0
    # unit_price = (1.0/1000)*100 = 0.1
    # total = 2*0.1 = 0.2
    result = calculate_mws_cost(
        price_in_1k=1.0,
        price_out_1k=1.0,
        tokens_in=101,
        tokens_out=0,
        unit_size=100
    )
    assert result == 0.2