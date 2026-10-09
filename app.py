from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import redis as redis_lib

import config
from routes.vehiculos import vehiculos_bp
from routes.vehiculos_cache import bp as vehiculos_cache_bp


def _check_mongo():
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.close()
        return "up"
    except (PyMongoError, Exception):
        return "down"


def _check_redis():
    try:
        if config.REDIS_URL:
            client = redis_lib.Redis.from_url(config.REDIS_URL, socket_connect_timeout=2)
        else:
            client = redis_lib.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                socket_connect_timeout=2,
            )
        client.ping()
        client.close()
        return "up"
    except Exception:
        return "down"


def create_app():
    app = Flask(__name__)
    app.register_blueprint(vehiculos_bp)
    app.register_blueprint(vehiculos_cache_bp)

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "mongo": _check_mongo(),
                "redis": _check_redis(),
                "db": f"{config.MONGO_DB}.{config.MONGO_COLLECTION}",
            }
        )

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "no encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "metodo no permitido"}), 405

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"error": "error interno"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
