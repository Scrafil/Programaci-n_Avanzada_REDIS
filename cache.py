"""Capa de caché Redis — dueño: W2-CACHE.

Contrato inamovible (PLAN_WAVES.md §0.3/§0.4):
- CAMPO_IDENTIFICADOR = "categoria" (TTL según len(categoria)).
- Clave: `vehiculo:<nombre>` (búsqueda por nombre).
- Valor: JSON del documento (sin _id). SETEX con el TTL.
- TTL 15/20/40/0 por len(categoria); >20 prioritaria = NO guardar.
- `fuente="redis"` solo si hubo HIT; si no, Mongo + SETEX (si TTL > 0).

PUT/DELETE (W2-API) deben llamar a `invalidar(nombre)` en try/except.
"""

import json

import redis as redis_lib

import config

CAMPO_IDENTIFICADOR = "categoria"


def ttl_para(categoria: str) -> int:
    n = len(categoria or "")
    if n > 20:  # PRIORITARIA (equivale a "descripción superior a 20")
        return 0  # 0 = NO almacenar en caché
    if n <= 5:
        return 15
    if n <= 10:
        return 20
    return 40


_client = None


def get_client():
    """Singleton perezoso de Redis (WLS: localhost:6379 o REDIS_URL)."""
    global _client
    if _client is None:
        if config.REDIS_URL:
            _client = redis_lib.Redis.from_url(
                config.REDIS_URL, socket_connect_timeout=2, decode_responses=True
            )
        else:
            _client = redis_lib.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                socket_connect_timeout=2,
                decode_responses=True,
            )
    return _client


def clave(nombre: str) -> str:
    return f"{config.CACHE_KEY_PREFIX}{nombre}"


def get_vehiculo(nombre, mongo_getter):
    """Flujo GET con caché.

    Returns (doc | None, fuente | None, ttl:int).
    - HIT: (doc, "redis", ttl_restante)
    - MISS con doc: (doc, "mongodb", ttl) + SETEX si ttl > 0
    - MISS sin doc: (None, None, 0) -> la ruta responde 404
    - Redis caído: degradado a Mongo sin romper (fuente mongodb).
    """
    key = clave(nombre)
    try:
        raw = get_client().get(key)
    except Exception:
        raw = None  # Redis caído -> seguir a Mongo
    if raw:
        try:
            doc = json.loads(raw)
        except (TypeError, ValueError):
            doc = None
        if isinstance(doc, dict):
            try:
                ttl_rest = get_client().ttl(key)
            except Exception:
                ttl_rest = -1
            if ttl_rest == -2:  # expiró entre GET y TTL -> tratar como MISS
                pass
            else:
                if ttl_rest is None or ttl_rest < 0:
                    try:
                        ttl_rest = ttl_para(doc.get(CAMPO_IDENTIFICADOR, ""))
                    except Exception:
                        ttl_rest = 0
                return doc, "redis", int(ttl_rest)
        # payload corrupto -> caer a Mongo y re-cachear

    doc = mongo_getter(nombre)
    if doc is None:
        return None, None, 0
    try:
        ttl = ttl_para(doc.get(CAMPO_IDENTIFICADOR, ""))
    except Exception:
        ttl = 0
    if ttl > 0:
        try:
            get_client().setex(key, ttl, json.dumps(doc, ensure_ascii=False))
        except Exception:
            pass  # Mongo manda aunque Redis falle
        return doc, "mongodb", ttl
    return doc, "mongodb", 0  # C4: NO guardar


def invalidar(nombre) -> int:
    """DEL vehiculo:<nombre>. Llamado por PUT/DELETE. Nunca lanza."""
    try:
        return int(get_client().delete(clave(nombre)))
    except Exception:
        return 0
