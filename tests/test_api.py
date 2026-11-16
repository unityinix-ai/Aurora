import unittest

from fastapi.testclient import TestClient

from api.app import app


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.previous_authenticator = app.state.authenticator
        self.previous_model = app.state.model_adapter
        app.state.authenticator = None
        app.state.model_adapter = None
        self.client = TestClient(app)

    def tearDown(self):
        app.state.authenticator = self.previous_authenticator
        app.state.model_adapter = self.previous_model

    def authenticate_as(self, scopes):
        app.state.authenticator = lambda _token: {"sub": "alice", "scope": scopes}

    def test_private_route_denies_without_authentication(self):
        response = self.client.get("/search?q=example")
        self.assertEqual(response.status_code, 401)

    def test_chat_requires_authentication(self):
        response = self.client.post(
            "/chat", json={"message": "hello", "consent": True}
        )
        self.assertEqual(response.status_code, 401)

    def test_personas_are_allow_listed(self):
        response = self.client.get("/personas")
        self.assertEqual(response.status_code, 200)
        self.assertIn("orochimaru", [item["key"] for item in response.json()])

    def test_read_scope_is_required(self):
        self.authenticate_as([])
        response = self.client.get(
            "/search?q=example", headers={"Authorization": "Bearer synthetic"}
        )
        self.assertEqual(response.status_code, 403)

    def test_write_scope_is_required(self):
        self.authenticate_as(["well:read"])
        response = self.client.post(
            "/observations",
            headers={"Authorization": "Bearer synthetic"},
            json={"source_ref": "test:1", "text": "example"},
        )
        self.assertEqual(response.status_code, 403)

    def test_chat_requires_explicit_consent(self):
        self.authenticate_as(["well:chat"])
        response = self.client.post(
            "/chat",
            headers={"Authorization": "Bearer synthetic"},
            json={"message": "hello", "consent": False},
        )
        self.assertEqual(response.status_code, 400)

    def test_no_model_fails_closed(self):
        self.authenticate_as(["well:chat"])
        response = self.client.post(
            "/chat",
            headers={"Authorization": "Bearer synthetic"},
            json={"message": "hello", "consent": True},
        )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
