import math

def calculate_mws_cost(price_in_1k: float, price_out_1k: float, tokens_in: int, tokens_out: int, unit_size: int) -> float:
    """
    Вычисляет итоговую стоимость использования модели на основе тарифов MWS.
    price_in_1k: цена за 1000 входящих токенов.
    price_out_1k: цена за 1000 исходящих токенов.
    tokens_in: планируемое количество входящих токенов.
    tokens_out: планируемое количество исходящих токенов.
    unit_size: планируемая отпускная единица в токенах.
    """
    units_in = math.ceil(tokens_in / unit_size)
    units_out = math.ceil(tokens_out / unit_size)
    
    unit_price_in = (price_in_1k / 1000) * unit_size
    unit_price_out = (price_out_1k / 1000) * unit_size
    
    total_cost = (units_in * unit_price_in) + (units_out * unit_price_out)
    
    return round(total_cost, 4)