import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger("mws-assistant")
mws_request_count = 0

def clean_price(price_str):
    """Вспомогательная функция для очистки строки цены."""
    if not price_str or '–' in price_str:
        return 0.0
    cleaned = re.sub(r'[^0-9,.]', '', price_str)
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def get_mws_full_data():
    """
    Получает актуальный список доступных моделей GPT из документации MWS.
    Возвращает список словарей с ценами за 1000 токенов и техническими характеристиками 
    (контекст, размер модели, форматы ввода).
    """
    global mws_request_count
    urls = {
        "specs": "https://mws.ru/docs/cloud-platform/gpt/general/gpt-models.html",
        "prices": "https://mws.ru/docs/cloud-platform/gpt/general/pricing.html"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    specs_data = {}
    try:
        mws_request_count += 1
        logger.info(f"MWS запрос #{mws_request_count}: характеристики моделей")

        resp = requests.get(urls["specs"], headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 6:
                name = cols[0].get_text(strip=True).lower()
                specs_data[name] = {
                    "developer": cols[1].get_text(strip=True),
                    "input_format": cols[2].get_text(strip=True),
                    "output_format": cols[3].get_text(strip=True),
                    "context_limit_k": cols[4].get_text(strip=True),
                    "size_b": cols[5].get_text(strip=True)
                }

        logger.info(f"MWS запрос #{mws_request_count}: получено {len(specs_data)} моделей")

    except Exception as e:
        logger.error(f"Ошибка парсинга характеристик: {e}")

    final_catalog = []
    try:
        mws_request_count += 1
        logger.info(f"MWS запрос #{mws_request_count}: цены")

        resp = requests.get(urls["prices"], headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 6:
                name = cols[0].get_text(strip=True).lower()
                
                price_in = clean_price(cols[3].get_text(strip=True)) # цены без акций
                price_out = clean_price(cols[4].get_text(strip=True))
                unit_size = cols[5].get_text(strip=True)

                model_info = {
                    "model": name,
                    "price_in_1k": price_in,
                    "price_out_1k": price_out,
                    "unit_size": unit_size,
                    "currency": "RUB",
                    **specs_data.get(name, {})
                }
                final_catalog.append(model_info)

        logger.info(f"MWS запрос #{mws_request_count}: получено {len(final_catalog)} моделей с ценами")
        logger.info(f"Всего запросов к MWS за сессию: {mws_request_count}")

    except Exception as e:
        logger.error(f"Ошибка парсинга цен: {e}")

    return final_catalog
