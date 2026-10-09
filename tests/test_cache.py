"""Contrato caché: matriz TTL (unit, sin infra) + MISS/HIT/invalidación (vive).

La prueba de expiración real es lenta: solo corre con E2E_SLOW=1.
"""

import os
import time
import unittest

from cache import ttl_para
from app import app


class TestMatrizTtl(unittest.TestCase):
    def test_band_as(self):
        self.assertEqual(ttl_para("Aéreo"), 15)
        self.assertEqual(ttl_para("abcde"), 15)

    def test_banda_20(self):
        self.assertEqual(ttl_para("Acuático"), 20)
        self.assertEqual(ttl_para("Espacial"), 20)

    def test_banda_40(self):
        self.assertEqual(ttl_para("Acuático ligero"), 40)

    def test_no_cache_prioritaria(self):
        self.assertEqual(ttl_para("Terrestre (motorizado)"), 0)
        self.assertEqual(ttl_para("Terrestre (no motorizado)"), 0)

    def test_bordes(self):
        self.assertEqual(ttl_para("12345"), 15)
        self.assertEqual(ttl_para("123456"), 20)
        self.assertEqual(ttl_para("12345678901"), 40)
        self.assertEqual(ttl_para("x" * 21), 0)


class TestCacheVive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = app.test_client()
        h = cls.c.get("/health").get_json()
        if h.get("mongo") != "up" or h.get("redis") != "up":
            raise unittest.SkipTest("Mongo o Redis no disponibles")

    def test_miss_hit_avion(self):
        from cache import get_client, clave
        get_client().delete(clave("Avión"))
        g = self.c.get("/vehiculos/Avión").get_json()
        self.assertEqual((g["fuente"], g["ttl_segundos"]), ("mongodb", 15))
        g = self.c.get("/vehiculos/Avión").get_json()
        self.assertEqual(g["fuente"], "redis")
        self.assertTrue(0 < g["ttl_segundos"] <= 15)

    def test_no_cache_camion(self):
        from cache import get_client, clave
        for _ in range(2):
            g = self.c.get("/vehiculos/Camión").get_json()
            self.assertEqual((g["fuente"], g["ttl_segundos"]), ("mongodb", 0))
        self.assertIsNone(get_client().get(clave("Camión")))

    def test_invalidacion_put(self):
        from cache import get_client, clave
        self.c.get("/vehiculos/Barco")
        self.assertIsNotNone(get_client().get(clave("Barco")))
        self.c.put("/vehiculos/Barco", json={"peso_toneladas": 2.5})
        self.assertIsNone(get_client().get(clave("Barco")))
        self.c.put("/vehiculos/Barco", json={"peso_toneladas": 2})  # restaura seed

    @unittest.skipUnless(os.getenv("E2E_SLOW") == "1", "expiración real (16s)")
    def test_expiracion_real_c1(self):
        from cache import get_client, clave
        get_client().delete(clave("Avión"))
        self.c.get("/vehiculos/Avión")
        time.sleep(16)
        g = self.c.get("/vehiculos/Avión").get_json()
        self.assertEqual(g["fuente"], "mongodb")


if __name__ == "__main__":
    unittest.main()
