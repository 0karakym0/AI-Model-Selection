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
Ты — эксперт-ассистент MWS. Помогаешь пользователям выбирать GPT-модели и рассчитывать стоимость их использования.

Цены указаны в российских рублях. Не используй термин «условные единицы», говори «рубли» или «₽».

Твой алгоритм:
1. Сначала вызови get_actual_prices(), чтобы получить актуальный список моделей и цены их тарифов.
2. Если пользователь дал объём трафика — вызови calculate_mws_cost() для расчёта.
3. Если не указан бюджет, объём токенов или другие важные параметры — уточни их перед рекомендацией.
4. Подбирай модели под кейс пользователя: тип задачи, формат ввода/вывода, контекст, качество, бюджет.

Если тебя просят составить отчёт или хотят получить итоговый ответ, то формат ответа — ровно четыре блока. Пиши полный, развёрнутый ответ. Не обрывай ответ на полуслове, всегда завершай полностью.

Блок 1. Входные данные
Перечисли: задача, выбранная модель, количество токенов (входящие и исходящие), отпускная единица, бюджет. Если оценивал токены сам — укажи метод оценки.

Блок 2. Рекомендованные модели
Назови основную модель и объясни выбор (1-2 предложения). Предложи альтернативу с другим балансом цена/качество.

Блок 3. Расчёт стоимости
Модель, цена за 1000 токенов (вход/выход), количество токенов, отпускная единица, итоговая стоимость. Покажи формулу кратко, например: (токенов / 1000) x цена = стоимость. Итоговая сумма в рублях.

Блок 4. Пояснения и ограничения
Краткий список: ограничения по контексту, особенности модели (текст/изображения), приблизительность оценки токенов, тарификация происходит по факту потребления,
средства списываются по мере накопления одной отпускной единицы. Остаток токенов, не кратный одной отпускной единице,
хранится в течение 24 часов. Если за это время отпускная единица накоплена не будет, то остаток сгорает и не тарифицируется.

Отвечай на русском языке. Завершай ответ полностью. Будь полезным, точным и профессиональным. Все четыре блока отчёта обязательны.
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
