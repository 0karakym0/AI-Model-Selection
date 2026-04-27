import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="authlib")
warnings.filterwarnings("ignore", message=".*PLUGGABLE_AUTH.*")
warnings.filterwarnings("ignore", message=".*end user credentials.*")
import uvicorn
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("mws-assistant")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from agent import ask_agent


os.environ["GRPC_VERBOSITY"] = "NONE"

app = FastAPI(title="MWS Assistant OpenAI-compatible API")

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ChatCompletionRequest(BaseModel):
    model: str = "mws-agent"
    messages: List[Message] = Field(..., min_length=1)
    
    @field_validator("messages")
    @classmethod
    def last_message_must_be_user(cls, v):
        if v[-1].role != "user":
            raise ValueError("Последнее сообщение должно быть от пользователя")
        return v


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    start_time = time.time()
    try:
        user_message = request.messages[-1].content[:100]
        logger.info(f"Запрос: {len(request.messages)} сообщений | Контент: «{user_message}...»")

        history_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        answer = await ask_agent(
            user_id="api_user",
            session_id="default_session",
            messages=history_dicts
        )

        elapsed = time.time() - start_time
        logger.info(f"Ответ: {len(answer)} символов | Время: {elapsed:.2f} сек")

        return {
            "id": "chatcmpl-unique-id",
            "object": "chat.completion",
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": answer
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Ошибка через {elapsed:.2f} сек: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info("Запуск сервера MWS Assistant на http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)