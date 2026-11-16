import os
import unittest
from unittest.mock import patch

from security.jwt_auth import JWTVerifier


class JWTVerifierConfigurationTests(unittest.TestCase):
    def test_http_jwks_url_is_rejected(self):
        with self.assertRaises(ValueError):
            JWTVerifier(
                jwks_url="http://identity.example.test/jwks",
                issuer="https://identity.example.test/",
                audience="aurora-api",
            )

    def test_empty_environment_disables_verifier(self):
        names = ("JWT_JWKS_URL", "JWT_ISSUER", "JWT_AUDIENCE")
        with patch.dict(os.environ, {name: "" for name in names}, clear=False):
            self.assertIsNone(JWTVerifier.from_env())

    def test_partial_environment_fails_startup(self):
        values = {
            "JWT_JWKS_URL": "https://identity.example.test/jwks",
            "JWT_ISSUER": "",
            "JWT_AUDIENCE": "",
        }
        with patch.dict(os.environ, values, clear=False):
            with self.assertRaises(RuntimeError):
                JWTVerifier.from_env()


if __name__ == "__main__":
    unittest.main()
