import os
import logging

os.environ["GRPC_VERBOSITY"] = "NONE"

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    raise RuntimeError("❌ Не задан GOOGLE_CLOUD_PROJECT. Создайте .env файл.")
if not os.environ.get("GOOGLE_CLOUD_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

os.environ["GOOGLE_ADK_SUPPRESS_EXPERIMENTAL_WARNINGS"] = "1"

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part
from parser import get_mws_full_data
from calculator import calculate_mws_cost

logging.getLogger("google_genai").setLevel(logging.ERROR)

PROJECT_ID = "556285447043"
LOCATION = "us-central1"

INSTRUCTION = """
Ты — официальный эксперт-ассистент MWS. Твоя задача — помогать пользователям выбирать подходящие GPT-модели и рассчитывать стоимость их использования.

Все цены указаны в российских рублях (₽). Никогда не используй термин «условные единицы», всегда говори «рубли» или «₽».

Твой алгоритм работы:
1. Всегда начинай с вызова get_actual_prices(), чтобы получить актуальный список моделей и их цены.
2. Если пользователь дал объём трафика — вызывай calculate_mws_cost() для расчёта стоимости.
3. Если пользователь не указал бюджет, объём токенов или другие важные параметры — уточни их, прежде чем давать рекомендацию.
4. Подбирай модели, исходя из кейса пользователя (тип задачи, формат ввода/вывода, контекст, качество, бюджет).

Формат ответа (структурированный отчёт):
Твой ответ должен содержать четыре блока:
1.Входные данные
Перечисли все параметры, которые ты использовал для расчёта, включая те, которые оценил самостоятельно:
Задача пользователя
Задача пользователя
Выбранная модель и причина выбора
Количество токенов (входящие / исходящие)
Отпускная единица
Бюджет (если указан)
2.Рекомендованные модели
Назови модель (или модели), объясни почему выбор пал именно на неё. Если критерий противоречит качеству — отметь это отдельно, дай альтернативу.
3.Расчёт стоимости
Приведи детальный расчёт: модель, цена за 1000 токенов (вход/выход), количество токенов, отпускная единица, итоговая стоимость в рублях.
4.Пояснения и ограничения
Укажи важные нюансы: есть ли акционные цены, ограничения по контексту, особенности модели (например, только текст или поддержка изображений), 24-часовое хранение остатка.
Если тебя просят вывести отчёт, ВСЕГДА выводи полные 4 блока отчёта.
Отвечай на русском языке. Будь полезным, точным и профессиональным.
"""

agent = LlmAgent(
    name="mws_assistant",
    model="gemini-2.5-flash",
    instruction=INSTRUCTION,
    description="Ассистент MWS для подбора GPT-моделей и расчёта стоимости",
    tools=[
        FunctionTool(get_mws_full_data),
        FunctionTool(calculate_mws_cost)
    ],
    generate_content_config={
        "temperature": 0.1,
        "max_output_tokens": 2048,
        "top_p": 0.95
    }
)

session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="mws_assistant_app",
    session_service=session_service
)


async def ask_agent(user_id: str, session_id: str, messages: list) -> str:
    """
    Вызов агента через ADK Runner с поддержкой сессий.
    messages: список словарей [{"role": "user", "content": "..."}, ...]
    """
    try:
        await session_service.create_session(
            app_name="mws_assistant_app",
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        pass

    user_message = messages[-1]["content"]
    new_message = Content(parts=[Part(text=user_message)], role="user")

    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response.strip()