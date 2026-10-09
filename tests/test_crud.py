"""Contrato CRUD (rápido, sin esperas). Requiere Mongo levantado. Usa docs temporales."""

import unittest

from app import app


class TestCrud(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = app.test_client()
        r = cls.c.get("/health")
        if r.status_code != 200 or r.get_json().get("mongo") != "up":
            raise unittest.SkipTest("Mongo no disponible")
        r = cls.c.get("/vehiculos")
        cls.n0 = len(r.get_json())

    def test_01_health(self):
        r = self.c.get("/health")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["mongo"], "up")
        self.assertEqual(body["redis"], "up")

    def test_02_ciclo_crud(self):
        doc = {"nombre": "UTTemp", "categoria": "Aéreo",
               "peso_toneladas": 1, "descripcion": "Prueba unitaria."}
        self.assertEqual(self.c.post("/vehiculos", json=doc).status_code, 201)
        self.assertEqual(self.c.post("/vehiculos", json=doc).status_code, 409)
        r = self.c.get("/vehiculos")
        self.assertEqual(len(r.get_json()), self.n0 + 1)
        r = self.c.put("/vehiculos/UTTemp", json={"peso_toneladas": 9})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["peso_toneladas"], 9)
        self.assertEqual(self.c.delete("/vehiculos/UTTemp").status_code, 200)
        self.assertEqual(self.c.delete("/vehiculos/UTTemp").status_code, 404)
        r = self.c.get("/vehiculos")
        self.assertEqual(len(r.get_json()), self.n0)

    def test_03_validacion(self):
        self.assertEqual(self.c.post("/vehiculos", json={"nombre": "X"}).status_code, 400)
        self.assertEqual(
            self.c.post("/vehiculos", data="x", content_type="text/plain").status_code, 400)
        self.assertEqual(
            self.c.put("/vehiculos/Avión", json={"peso_toneladas": -1}).status_code, 400)
        self.assertEqual(
            self.c.put("/vehiculos/NoExiste", json={"peso": 1}).status_code, 400)
        self.assertEqual(self.c.put("/vehiculos/NoExiste", json={"peso_toneladas": 1}).status_code, 404)

    def test_04_errores_json(self):
        r = self.c.get("/ruta_que_no_existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())


if __name__ == "__main__":
    unittest.main()
