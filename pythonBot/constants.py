import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

TOKEN_BOT = os.getenv("TOKEN")

if TOKEN_BOT is None:
    raise RuntimeError("bot token not in .env")

WEATHER_API = os.getenv("WEATHER_API")

if WEATHER_API is None:
    raise RuntimeError("weather token not in .env")

TOKEN: str = TOKEN_BOT
API_URL: str = 'https://api.telegram.org/bot'
QUOTES_WEBSITE: str = 'https://www.azquotes.com'
API_WEATHER: str = 'https://api.openweathermap.org/data/2.5/weather'
MK_NEWS: str = 'https://www.mk.ru/rss/news/index.xml'
LENTA_NEWS: str = 'https://lenta.ru/rss/top7'
WEATHER_API_KEY: str = WEATHER_API
