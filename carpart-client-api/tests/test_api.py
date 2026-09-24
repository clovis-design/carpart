"""Tests HTTP d'intégration contre l'API démarrée avec MySQL."""

import json
import os
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.getenv("API_URL", "http://localhost:7000").rstrip("/")


def request(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(BASE_URL + path, data=data, method=method,
                  headers={"Content-Type": "application/json"})
    try:
        response = urlopen(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


class ClientAPITests(unittest.TestCase):
    def setUp(self):
        self.payload = {"nom": "Test", "prenom": "Élodie",
                        "mail": "carpart-test@example.com", "nbCommande": 2}

    def create_client(self, payload):
        code, client = request("POST", "/clients", payload)
        self.assertEqual(code, 201, client)
        self.addCleanup(request, "DELETE", f"/clients/{client['id']}")
        return client

    def test_health(self):
        self.assertEqual(request("GET", "/health"),
                         (200, {"status": "ok", "database": "connected"}))

    def test_client_lifecycle(self):
        client = self.create_client(self.payload)
        path = f"/clients/{client['id']}"
        self.assertEqual(request("GET", path), (200, client))
        self.assertEqual(request("GET", "/clients?limit=1")[0], 200)
        changes = {"nom": "Dupont", "prenom": "Alice",
                   "mail": "alice@example.com", "nbCommande": 5}
        code, updated = request("PUT", path, changes)
        self.assertEqual(code, 200)
        self.assertEqual(updated, {"id": client["id"], **changes})
        code, updated = request("PUT", path, {"nbCommande": 0})
        self.assertEqual(code, 200)
        self.assertEqual(updated, {"id": client["id"], **changes, "nbCommande": 0})
        self.assertEqual(request("GET", path), (200, updated))
        self.assertEqual(request("DELETE", path)[0], 200)
        for method, body in (("GET", None), ("PUT", {"nbCommande": 1}), ("DELETE", None)):
            self.assertEqual(request(method, path, body)[0], 404)

    def test_default_order_count(self):
        self.payload.pop("nbCommande")
        self.assertEqual(self.create_client(self.payload)["nbCommande"], 0)

    def test_invalid_creation(self):
        for changes in ({"nom": "   "}, {"prenom": ""}, {"mail": "invalide"},
                        {"nbCommande": -1}, {"nbCommande": 1.5},
                        {"nbCommande": True}, {"nbCommande": 2147483648},
                        {"mail": None}):
            with self.subTest(changes=changes):
                self.assertEqual(request("POST", "/clients", {**self.payload, **changes})[0], 422)
        for field in ("nom", "prenom", "mail"):
            payload = {key: value for key, value in self.payload.items() if key != field}
            self.assertEqual(request("POST", "/clients", payload)[0], 422)

    def test_invalid_update_and_pagination(self):
        client = self.create_client(self.payload)
        path = f"/clients/{client['id']}"
        self.assertEqual(request("PUT", path, {})[0], 400)
        for payload in ({"nom": None}, {"mail": "invalide"}, {"nbCommande": -1},
                        {"nbCommande": 2.5}, {"prenom": " "}):
            self.assertEqual(request("PUT", path, payload)[0], 422)
        self.assertEqual(request("GET", path), (200, client))
        for path in ("/clients/abc", "/clients/0", "/clients?skip=-1",
                     "/clients?limit=0", "/clients?limit=1001"):
            self.assertEqual(request("GET", path)[0], 422)


if __name__ == "__main__":
    unittest.main()
