from __future__ import annotations

from typing import Any

import aiohttp

from lab4.constants import LLM_API_KEY, LLM_API_URL, LLM_MODEL


def llm_ready() -> bool:
    """
    Проверяет, подключена ли LLM.

    :return: True, если ключи есть
    """
    return bool(LLM_API_URL and LLM_API_KEY)


async def ask_llm(
    session: aiohttp.ClientSession,
    prompt: str,
) -> str | None:
    """
    Отправляет запрос в LLM API.

    :param session: aiohttp-сессия
    :param prompt: текст запроса
    :return: ответ модели или None
    """
    if not llm_ready():
        return None

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты полезный AI-ассистент для анализа технических данных.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    try:
        response = await session.post(
            LLM_API_URL,
            json=payload,
            headers=headers,
        )

        data = await response.json()

        if response.status != 200:
            return f"Ошибка LLM API: {data}"

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        if "answer" in data:
            return data["answer"]

        return str(data)

    except Exception as error:
        return f"Ошибка при запросе к LLM: {error}"
    