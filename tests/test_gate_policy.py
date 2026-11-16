"""Unit tests for the fail-closed Genesis Gate authorization policy."""
import unittest

from security.gate_policy import authorize_gate


NOW = 1_800_000_000
ISSUER = "https://auth.example.test"
AUDIENCE = "genesis-gate"
SCOPE = "gate:read"


def valid_claims():
    return {
        "iss": ISSUER,
        "sub": "synthetic-user-001",
        "jti": "synthetic-token-001",
        "aud": AUDIENCE,
        "exp": NOW + 300,
        "nbf": NOW - 10,
        "scope": [SCOPE],
    }


def allow_not_revoked(_token_id):
    return False


class GatePolicyTests(unittest.TestCase):
    def check(self, claims, *, revoked=allow_not_revoked, now=NOW):
        return authorize_gate(
            claims,
            required_scope=SCOPE,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=now,
            is_revoked=revoked,
        )

    def test_valid_claims_are_allowed(self):
        self.assertTrue(self.check(valid_claims()))

    def test_missing_claims_are_denied(self):
        self.assertFalse(self.check(None))

    def test_wrong_issuer_is_denied(self):
        claims = valid_claims()
        claims["iss"] = "https://untrusted.example.test"
        self.assertFalse(self.check(claims))

    def test_wrong_audience_is_denied(self):
        claims = valid_claims()
        claims["aud"] = "other-service"
        self.assertFalse(self.check(claims))

    def test_expired_token_is_denied(self):
        claims = valid_claims()
        claims["exp"] = NOW
        self.assertFalse(self.check(claims))

    def test_not_yet_valid_token_is_denied(self):
        claims = valid_claims()
        claims["nbf"] = NOW + 1
        self.assertFalse(self.check(claims))

    def test_missing_scope_is_denied(self):
        claims = valid_claims()
        claims["scope"] = ["profile:read"]
        self.assertFalse(self.check(claims))

    def test_revoked_token_is_denied(self):
        self.assertFalse(self.check(valid_claims(), revoked=lambda _jti: True))

    def test_revocation_service_failure_is_denied(self):
        def unavailable(_jti):
            raise RuntimeError("synthetic revocation service failure")
        self.assertFalse(self.check(valid_claims(), revoked=unavailable))

    def test_missing_token_identifier_is_denied(self):
        claims = valid_claims()
        claims.pop("jti")
        self.assertFalse(self.check(claims))

    def test_boolean_expiration_is_denied(self):
        claims = valid_claims()
        claims["exp"] = True
        self.assertFalse(self.check(claims))

    def test_non_finite_expiration_is_denied(self):
        claims = valid_claims()
        claims["exp"] = float("inf")
        self.assertFalse(self.check(claims))

    def test_non_finite_clock_is_denied(self):
        self.assertFalse(self.check(valid_claims(), now=float("nan")))


if __name__ == "__main__":
    unittest.main()
