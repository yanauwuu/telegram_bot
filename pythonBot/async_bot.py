from __future__ import annotations

from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import ssl
import certifi

from lab4.constants import (
    API_URL,
    TOKEN,
    WEATHER_API_KEY,
    API_WEATHER,
    MK_NEWS,
    LENTA_NEWS,
)

from lab4.sync_bot import get_daily_quote

from typing import Any

user_states: dict[int, str] = {}

TIMEOUT = ClientTimeout(total=30)


async def send_message(
    session: aiohttp.ClientSession,
    chat_id: int,
    text: str,
) -> dict[str, Any]:
    """
        Отправка сообщения через sendMessage

    :param:
        session - aiohttp-сессия
        chat_id - айди чата
        text - текст сообщения

    :return:
        ответ Telegram API в формате json
    """
    info = {'chat_id': chat_id, 'text': text}
    response = await session.post(API_URL + TOKEN + '/sendMessage', json=info)
    if response.status != 200:
        raise RuntimeError('sendMessage failed')
    return await response.json()


async def get_updates(
    session: aiohttp.ClientSession,
    offset: int | None = None,
    timeout: ClientTimeout = TIMEOUT,
) -> list[dict[str, Any]]:
    """
    Обновления от телеграма с помощью getUpdates, long pollling

    :param:
        session - aiohttp-сессия
        offset - с какого айди апдейта читать
        timeout - время long polling
    :return:
        список апдейтов, каждый в словаре
    """
    response = await session.get(
        f'{API_URL}{TOKEN}/getUpdates?offset={offset}',
        timeout=timeout,
    )
    if response.status != 200:
        raise RuntimeError('getUpdates failed')
    info = await response.json()
    final = info.get("result")
    if not isinstance(final, list):
        return []
    return [i for i in final if isinstance(i, dict)]


async def lenta_news(session: aiohttp.ClientSession) -> list[str]:
    """
    Парсинг новостей с Lenta и возвращение первых трех строк

    :param:
        session - aiohttp-сессия
    :return:
        список заголовков
    """
    response = await session.get(LENTA_NEWS, timeout=TIMEOUT)
    if response.status != 200:
        raise RuntimeError('не удалось получить новости от Лента')
    text = await response.text()

    parsed = BeautifulSoup(text, 'html.parser')
    items = parsed.select('item')[:3]
    titles = []
    for item in items:
        title = item.select_one('title')
        if title:
            titles.append(title.get_text(" ", strip=True))
    return titles


async def mk_news(session: aiohttp.ClientSession) -> list[str]:
    """
    Парсинг новостей с MK и возвращение первых трех строк

    :param:
        session - aiohttp-сессия
    :return:
        список заголовков
    """
    response = await session.get(MK_NEWS, timeout=TIMEOUT)
    if response.status != 200:
        raise RuntimeError('не удалось получить новости от МК')
    text = await response.text()

    parsed = BeautifulSoup(text, 'html.parser')
    items = parsed.select('item')[:3]
    titles = []

    for item in items:
        title = item.select_one('title')
        if title:
            titles.append(title.get_text(" ", strip=True))
    return titles


async def get_weather(session: aiohttp.ClientSession, city: str) -> str:
    """
    Запрос погоды по городу

    :param:
        session - aiohttp-сессия
        city - город
    :return:
        строка с инфой о погоде или исключение
    """
    response = await session.get(
        API_WEATHER,
        params={'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'},
        timeout=TIMEOUT
    )
    if response.status != 200:
        raise RuntimeError('не удалось получить запрос с сайта')
    info = await response.json()

    try:
        temperature = info["main"]["temp"]
        wind = info["wind"]["speed"]
        name = info["name"]
        description = info["weather"][0]["description"]
    except (KeyError, IndexError, TypeError):
        return "Погода не найдена"

    return (
        f"Погода в городе {name}\n"
        f"{description}\n"
        f"Температура: {temperature} градусов\n"
        f"Ветер: {wind} м/c"
    )


async def main() -> None:
    """
    Цикл polling
    получает обновления,
    на команде /quote отправляет цитату,
    на /headlines отправляет новости с Ленты и МК
    на /weather запрашивает город и отправляет погоду
    иначе работает как эхо-бот
    """
    offset: int | None = None
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            upd = await get_updates(session, offset=offset, timeout=TIMEOUT)
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
                user = message.get("from")
                if not isinstance(user, dict):
                    continue
                user_id = user.get("id")
                if not isinstance(user_id, int):
                    continue
                text = message.get("text")
                if not isinstance(text, str):
                    continue

                if user_id in user_states:
                    if user_states.get(user_id) == "waiting_for_city":
                        try:
                            weather = await get_weather(session, text)
                        except (
                                aiohttp.ClientError,
                                asyncio.TimeoutError,
                                RuntimeError
                        ):
                            weather = "Погода не найдена"

                        await send_message(session, chat_id, weather)
                        user_states.pop(user_id, None)
                        continue

                if text.strip() == "/quote":
                    try:
                        quote = await asyncio.to_thread(get_daily_quote)
                    except Exception:
                        quote = 'quote not found'
                    await send_message(session, chat_id, quote)

                elif text.strip() == "/headlines":
                    lenta, mk = await asyncio.gather(
                        lenta_news(session),
                        mk_news(session))

                    final_msg = "Лента:\n"
                    for news in lenta:
                        final_msg += f"- {news}\n"

                    final_msg += "\nМК:\n"
                    for news in mk:
                        final_msg += f"- {news}\n"

                    await send_message(session, chat_id, final_msg)

                elif text.strip() == "/weather":
                    await send_message(session, chat_id, "Ваш город")
                    user_states[user_id] = 'waiting_for_city'

                else:
                    await send_message(session, chat_id, text)


if __name__ == "__main__":
    asyncio.run(main())
