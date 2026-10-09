from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

import config
from routes.models import validate_vehiculo

vehiculos_bp = Blueprint("vehiculos", __name__)

_client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)


def _col():
    return _client[config.MONGO_DB][config.MONGO_COLLECTION]


def _invalidar(nombre):
    # cache.py lo provee W2-CACHE; si aún no existe, no se rompe nada.
    try:
        from cache import invalidar
    except Exception:
        return
    try:
        invalidar(nombre)
    except Exception:
        pass


@vehiculos_bp.post("/vehiculos")
def crear():
    clean, err = validate_vehiculo(request.get_json(silent=True))
    if err:
        return jsonify({"error": err}), 400
    try:
        _col().insert_one(dict(clean))
        _invalidar(clean["nombre"])
        return jsonify(clean), 201
    except DuplicateKeyError:
        return jsonify({"error": f"ya existe: {clean['nombre']}"}), 409
    except PyMongoError:
        return jsonify({"error": "error de base de datos"}), 500


@vehiculos_bp.get("/vehiculos")
def listar():
    try:
        docs = list(_col().find({}, {"_id": 0}).sort("nombre", 1))
        return jsonify(docs), 200
    except PyMongoError:
        return jsonify({"error": "error de base de datos"}), 500


@vehiculos_bp.put("/vehiculos/<nombre>")
def actualizar(nombre):
    data = request.get_json(silent=True)
    if isinstance(data, dict) and "nombre" in data and data["nombre"] != nombre:
        return jsonify({"error": "nombre no se puede modificar"}), 400
    clean, err = validate_vehiculo(data, partial=True)
    if err:
        return jsonify({"error": err}), 400
    try:
        res = _col().update_one({"nombre": nombre}, {"$set": clean})
        if res.matched_count == 0:
            return jsonify({"error": f"no existe: {nombre}"}), 404
        _invalidar(nombre)
        doc = _col().find_one({"nombre": nombre}, {"_id": 0})
        return jsonify(doc), 200
    except PyMongoError:
        return jsonify({"error": "error de base de datos"}), 500


@vehiculos_bp.delete("/vehiculos/<nombre>")
def eliminar(nombre):
    try:
        doc = _col().find_one({"nombre": nombre}, {"_id": 0})
        if doc is None:
            return jsonify({"error": f"no existe: {nombre}"}), 404
        _col().delete_one({"nombre": nombre})
        _invalidar(nombre)
        return jsonify(doc), 200
    except PyMongoError:
        return jsonify({"error": "error de base de datos"}), 500
