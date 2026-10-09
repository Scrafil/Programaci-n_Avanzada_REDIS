"""GET /vehiculos/<nombre> con caché Redis — dueño: W2-CACHE.

W2-API NO debe implementar este GET (ver PLAN_WAVES.md Wave 2);
W2-API sí implementa POST/lista/PUT/DELETE en routes/vehiculos.py.
"""

from flask import Blueprint, jsonify
from pymongo import MongoClient

import cache
import config

bp = Blueprint("vehiculos_cache", __name__)


def _collection():
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=2000)
    return client[config.MONGO_DB][config.MONGO_COLLECTION]


def _mongo_getter(nombre):
    return _collection().find_one({"nombre": nombre}, {"_id": 0})


@bp.get("/vehiculos/<nombre>")
def obtener_vehiculo(nombre):
    doc, fuente, ttl = cache.get_vehiculo(nombre, _mongo_getter)
    if doc is None:
        return jsonify({"error": "no encontrado"}), 404
    return jsonify({**doc, "fuente": fuente, "ttl_segundos": ttl}), 200
