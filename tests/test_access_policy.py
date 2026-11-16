"""Tests for private Well-record ownership enforcement."""
import unittest

from security.access_policy import authorize_record_access


def claims(subject="user-a", scope=None):
    return {
        "sub": subject,
        "scope": ["well:read"] if scope is None else scope,
    }


class RecordAccessTests(unittest.TestCase):
    def test_owner_with_scope_is_allowed(self):
        self.assertTrue(authorize_record_access(
            claims("user-a"), record_owner_id="user-a"
        ))

    def test_different_user_is_denied(self):
        self.assertFalse(authorize_record_access(
            claims("user-a"), record_owner_id="user-b"
        ))

    def test_missing_claims_are_denied(self):
        self.assertFalse(authorize_record_access(
            None, record_owner_id="user-a"
        ))

    def test_missing_subject_is_denied(self):
        self.assertFalse(authorize_record_access(
            {"scope": ["well:read"]}, record_owner_id="user-a"
        ))

    def test_missing_scope_is_denied(self):
        self.assertFalse(authorize_record_access(
            claims("user-a", ["profile:read"]), record_owner_id="user-a"
        ))

    def test_blank_record_owner_is_denied(self):
        self.assertFalse(authorize_record_access(
            claims("user-a"), record_owner_id=" "
        ))

    def test_admin_label_does_not_implicitly_bypass_ownership(self):
        self.assertFalse(authorize_record_access(
            {"sub": "admin", "scope": ["well:read", "admin"]},
            record_owner_id="user-a"
        ))

    def test_malformed_scope_is_denied(self):
        self.assertFalse(authorize_record_access(
            {"sub": "user-a", "scope": None}, record_owner_id="user-a"
        ))


if __name__ == "__main__":
    unittest.main()
