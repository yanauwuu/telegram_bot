from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from lab4.constants import API_URL, TOKEN, QUOTES_WEBSITE
from typing import Any


def get_me() -> dict[str, Any]:
    """
    Проверка токена

    :return: ответ Telegram API в формате json
    """
    response = requests.get(API_URL + TOKEN + '/getMe')
    if response.status_code != 200:
        raise RuntimeError('getMe failed, token is invalid')
    return response.json()


def send_message(chat_id: int, text: str) -> dict[str, Any]:
    """
    Отправка сообщения через sendMessage

    :param:
        chat_id - id чата-адресата
        text - текст сообщения

    :return:
        ответ Telegram API в формате json
    """
    info = {'chat_id': chat_id, 'text': text}
    response = requests.post(API_URL + TOKEN + '/sendMessage', json=info)
    if response.status_code != 200:
        raise RuntimeError('sendMessage failed')
    return response.json()


def get_updates(
        offset: int | None = None,
        timeout: float = 30,
) -> list[dict[str, Any]]:
    """
    Обновления от телеграма с помощью getUpdates

    :param:
        offset - с какого айди апдейта прочитать обновление
        timeout - время long polling

    :return:
        список обновлений (каждый в словаре)
    """
    response = requests.get(
        f'{API_URL}{TOKEN}/getUpdates?offset={offset}',
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError('getUpdates failed')
    return response.json()["result"]


def get_daily_quote() -> str:
    """
    Парсинг цитаты с сайта

    :return: строка с цитатой, либо строка/кортеж с ошибкой
    """
    try:
        content = requests.get(
            QUOTES_WEBSITE,
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
    except requests.RequestException:
        return 'quote not found'
    parsed = BeautifulSoup(content.text, 'html.parser')
    quote_tag = parsed.select_one("div.content-slide a")
    author_tag = parsed.select_one("div.q_user a")

    if quote_tag is None or author_tag is None:
        return "quote not found"

    quote = quote_tag.get_text(" ", strip=True)
    author = author_tag.get_text(" ", strip=True)

    if quote:
        return f"Цитата дня \n {quote} \n Автор {author}"
    return "quote not found"


def main() -> None:
    """
    Цикл polling
    получает обновления,
    на команде /quote отправляет цитату,
    иначе работает как эхо-бот
    """
    offset = None
    while True:
        upd = get_updates(offset=offset, timeout=30)
        for u in upd:
            upd_id = u.get("update_id")
            if not isinstance(upd_id, int):
                continue
            offset = upd_id + 1

            message = u.get("message")
            if not isinstance(message, dict):
                continue
            chat = message.get("chat")
            if not isinstance(chat, dict):
                continue
            chat_id = chat.get("id")
            if not isinstance(chat_id, int):
                continue
            text = message.get("text")
            if not isinstance(text, str):
                continue

            if text.strip() == "/quote":
                try:
                    send_message(chat_id, get_daily_quote())
                except requests.RequestException:
                    send_message(chat_id, "quote not found")
            else:
                send_message(chat_id, text)


if __name__ == "__main__":
    main()
