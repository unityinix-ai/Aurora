import sqlite3
import tempfile
import unittest
from pathlib import Path

from well.ledger import WellLedger


class WellLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "well.sqlite3"
        self.ledger = WellLedger(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_append_and_verify(self):
        first = self.ledger.append(
            aggregate_id="conversation-1",
            event_type="observation.recorded",
            actor="user",
            payload={"text": "A source-backed observation", "status": "observed"},
        )
        second = self.ledger.append(
            aggregate_id="conversation-1",
            event_type="pattern.proposed",
            actor="well-engine",
            payload={"supports": [first["event_id"]], "confidence": 0.7},
        )
        self.assertEqual(first["seq"], 1)
        self.assertEqual(second["seq"], 2)
        self.assertEqual(second["previous_hash"], first["event_hash"])
        self.assertTrue(self.ledger.verify()["valid"])
        self.assertEqual(self.ledger.verify()["records_checked"], 2)

    def test_aggregate_filter(self):
        self.ledger.append(
            aggregate_id="a", event_type="note", actor="user", payload={"n": 1}
        )
        self.ledger.append(
            aggregate_id="b", event_type="note", actor="user", payload={"n": 2}
        )
        self.assertEqual(len(self.ledger.list_events("a")), 1)

    def test_rejects_missing_required_fields(self):
        with self.assertRaises(ValueError):
            self.ledger.append(
                aggregate_id="", event_type="note", actor="user", payload={}
            )

    def test_payload_is_canonicalized(self):
        event = self.ledger.append(
            aggregate_id="a",
            event_type="note",
            actor="user",
            payload={"z": 1, "a": {"y": 2, "b": 3}},
        )
        self.assertEqual(event["payload_json"], '{"a":{"b":3,"y":2},"z":1}')

    def test_detects_payload_tampering(self):
        self.ledger.append(
            aggregate_id="a", event_type="note", actor="user", payload={"value": "original"}
        )
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE well_events SET payload_json = ? WHERE seq = 1",
                ('{"value":"altered"}',),
            )
        report = self.ledger.verify()
        self.assertFalse(report["valid"])
        self.assertIn("event hash mismatch at seq 1", report["errors"])

    def test_detects_chain_link_tampering(self):
        first = self.ledger.append(
            aggregate_id="a", event_type="note", actor="user", payload={"n": 1}
        )
        self.ledger.append(
            aggregate_id="a", event_type="note", actor="user", payload={"n": 2}
        )
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE well_events SET previous_hash = ? WHERE seq = 2",
                ("f" * 64,),
            )
        report = self.ledger.verify()
        self.assertFalse(report["valid"])
        self.assertIn("previous hash mismatch at seq 2", report["errors"])


if __name__ == "__main__":
    unittest.main()
