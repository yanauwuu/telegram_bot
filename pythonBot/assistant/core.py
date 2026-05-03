from __future__ import annotations

from pathlib import Path

import aiohttp

from lab4.assistant.chunker import make_chunks
from lab4.assistant.llm_client import ask_llm
from lab4.assistant.prompts import make_prompt
from lab4.assistant.retriever import find_chunks


user_histories: dict[int, list[dict[str, str]]] = {}
user_chunks: dict[int, list[str]] = {}


def read_text(path: Path) -> str:
    """
    Читает текстовый файл.

    :param path: путь к файлу
    :return: текст файла
    """
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_default_chunks(data_path: Path) -> list[str]:
    """
    Загружает стандартную базу знаний.

    :param data_path: путь к файлу
    :return: список кусков текста
    """
    text = read_text(data_path)

    return make_chunks(text)


def set_user_file(user_id: int, path: Path) -> None:
    """
    Подключает пользователю его файл.

    :param user_id: id пользователя
    :param path: путь к файлу
    """
    text = read_text(path)
    user_chunks[user_id] = make_chunks(text)


def get_history(user_id: int) -> list[dict[str, str]]:
    """
    Возвращает историю пользователя.

    :param user_id: id пользователя
    :return: история сообщений
    """
    return user_histories.get(user_id, [])


def add_history(user_id: int, role: str, text: str) -> None:
    """
    Добавляет сообщение в историю.

    :param user_id: id пользователя
    :param role: роль user/assistant
    :param text: текст сообщения
    """
    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": role,
        "text": text,
    })

    user_histories[user_id] = user_histories[user_id][-10:]


def clear_history(user_id: int) -> None:
    """
    Очищает историю пользователя.

    :param user_id: id пользователя
    """
    user_histories[user_id] = []


def get_chunks_for_user(
    user_id: int,
    default_chunks: list[str],
) -> list[str]:
    """
    Возвращает базу знаний пользователя или стандартную.

    :param user_id: id пользователя
    :param default_chunks: стандартная база знаний
    :return: список кусков
    """
    if user_id in user_chunks:
        return user_chunks[user_id]

    return default_chunks


def fallback_answer(context_chunks: list[str]) -> str:
    """
    Ответ без LLM.

    :param context_chunks: найденный контекст
    :return: текст ответа
    """
    context = "\n\n".join(context_chunks)

    return (
        "LLM API пока не подключён, поэтому показываю найденный контекст:\n\n"
        f"{context}\n\n"
        "Чтобы получить полноценный AI-ответ, добавь LLM_API_URL и LLM_API_KEY в .env."
    )


async def answer_question(
    session: aiohttp.ClientSession,
    user_id: int,
    question: str,
    default_chunks: list[str],
) -> str:
    """
    Главная функция AI-ассистента.

    :param session: aiohttp-сессия
    :param user_id: id пользователя
    :param question: вопрос пользователя
    :param default_chunks: стандартная база знаний
    :return: ответ ассистента
    """
    chunks = get_chunks_for_user(user_id, default_chunks)
    context_chunks = find_chunks(question, chunks)

    if not context_chunks:
        return (
            "Я не нашёл подходящей информации в базе знаний.\n"
            "Попробуй переформулировать вопрос или отправь мне .txt файл."
        )

    history = get_history(user_id)
    prompt = make_prompt(question, context_chunks, history)

    add_history(user_id, "user", question)

    llm_answer = await ask_llm(session, prompt)

    if llm_answer is None:
        answer = fallback_answer(context_chunks)
    else:
        answer = llm_answer

    add_history(user_id, "assistant", answer)

    return answer
