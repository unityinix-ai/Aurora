import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from security.jwt_auth import JWTVerifier


ISSUER = "https://identity.example.test/"
AUDIENCE = "aurora-api"


class JWTVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.verifier = JWTVerifier(
            jwks_url="https://identity.example.test/.well-known/jwks.json",
            issuer=ISSUER,
            audience=AUDIENCE,
        )
        self.verifier.jwks.get_signing_key_from_jwt = (
            lambda _token: SimpleNamespace(key=self.private_key.public_key())
        )

    def make_token(self, **overrides):
        now = datetime.now(timezone.utc)
        claims = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "synthetic-user",
            "exp": now + timedelta(minutes=5),
            "nbf": now - timedelta(seconds=5),
            "scope": "well:read well:write",
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private_key, algorithm="RS256")

    def test_valid_signature_and_claims_are_accepted(self):
        claims = asyncio.run(self.verifier(self.make_token()))
        self.assertEqual(claims["sub"], "synthetic-user")
        self.assertEqual(claims["scope"], ["well:read", "well:write"])

    def test_wrong_issuer_is_rejected(self):
        with self.assertRaises(jwt.InvalidIssuerError):
            asyncio.run(self.verifier(self.make_token(iss="https://other.example.test/")))

    def test_wrong_audience_is_rejected(self):
        with self.assertRaises(jwt.InvalidAudienceError):
            asyncio.run(self.verifier(self.make_token(aud="other-api")))

    def test_expired_token_is_rejected(self):
        old = datetime.now(timezone.utc) - timedelta(minutes=5)
        with self.assertRaises(jwt.ExpiredSignatureError):
            asyncio.run(self.verifier(self.make_token(exp=old)))

    def test_signature_from_another_key_is_rejected(self):
        token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": "synthetic-user",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            self.other_private_key,
            algorithm="RS256",
        )
        with self.assertRaises(jwt.InvalidSignatureError):
            asyncio.run(self.verifier(token))

    def test_hmac_algorithm_is_rejected(self):
        token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": "synthetic-user",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            "synthetic-secret",
            algorithm="HS256",
        )
        with self.assertRaises(jwt.InvalidAlgorithmError):
            asyncio.run(self.verifier(token))

    def test_http_jwks_url_is_rejected(self):
        with self.assertRaises(ValueError):
            JWTVerifier(
                jwks_url="http://identity.example.test/jwks",
                issuer=ISSUER,
                audience=AUDIENCE,
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
