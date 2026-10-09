import os

from dotenv import load_dotenv

load_dotenv()


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/automoviles")
MONGO_DB = os.getenv("MONGO_DB", "automoviles")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "vehiculos")

REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = _int("REDIS_PORT", 6379)
REDIS_DB = _int("REDIS_DB", 0)

FLASK_PORT = _int("FLASK_PORT", 5000)
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

CAMPO_IDENTIFICADOR = os.getenv("CAMPO_IDENTIFICADOR", "categoria")
CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "vehiculo:")
