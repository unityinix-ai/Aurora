"""Minimal append-only SQLite event ledger for The Well.

This module provides integrity-linked event storage, not authentication,
authorization, trusted timestamps, or proof that event contents are true.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 64


def canonical_json(value: Any) -> bytes:
    """Serialize JSON deterministically for this Python implementation."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def event_digest(seq, event_id, aggregate_id, occurred_at, event_type,
                 actor, payload_json, previous_hash) -> str:
    envelope = {
        "seq": seq, "event_id": event_id, "aggregate_id": aggregate_id,
        "occurred_at": occurred_at, "event_type": event_type, "actor": actor,
        "payload": json.loads(payload_json), "previous_hash": previous_hash,
    }
    return hashlib.sha256(canonical_json(envelope)).hexdigest()


class WellLedger:
    """Append-only event store.

    SQLite does not protect against privileged direct database modification.
    Production requires filesystem controls, protected backups and signed
    checkpoints. This component does not authenticate or authorize callers.
    """

    def __init__(self, database: str | Path):
        self.database = str(database)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS well_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    aggregate_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_well_events_aggregate "
                "ON well_events(aggregate_id, seq)"
            )

    def append(self, *, aggregate_id: str, event_type: str, actor: str,
               payload: dict[str, Any], occurred_at: str | None = None):
        if not aggregate_id.strip() or not event_type.strip() or not actor.strip():
            raise ValueError("aggregate_id, event_type and actor are required")
        payload_json = canonical_json(payload).decode("utf-8")
        timestamp = occurred_at or datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())

        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            last = db.execute(
                "SELECT seq, event_hash FROM well_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = last["event_hash"] if last else GENESIS_HASH
            seq = last["seq"] + 1 if last else 1
            digest = event_digest(
                seq, event_id, aggregate_id, timestamp, event_type, actor,
                payload_json, previous_hash
            )
            db.execute("""
                INSERT INTO well_events
                (seq, event_id, aggregate_id, occurred_at, event_type, actor,
                 payload_json, previous_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (seq, event_id, aggregate_id, timestamp, event_type, actor,
                  payload_json, previous_hash, digest))
        # Read only after the transaction has committed.
        return self.get(seq)

    def get(self, seq: int):
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM well_events WHERE seq = ?", (seq,)
            ).fetchone()
        return self._decode(row) if row else None

    def list_events(self, aggregate_id: str | None = None):
        query = "SELECT * FROM well_events"
        params = ()
        if aggregate_id is not None:
            query += " WHERE aggregate_id = ?"
            params = (aggregate_id,)
        query += " ORDER BY seq ASC"
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [self._decode(row) for row in rows]

    def verify(self):
        events = self.list_events()
        expected_previous = GENESIS_HASH
        errors = []
        expected_seq = 1
        for event in events:
            if event["seq"] != expected_seq:
                errors.append(
                    f"sequence discontinuity at stored seq {event['seq']}; "
                    f"expected {expected_seq}"
                )
            if event["previous_hash"] != expected_previous:
                errors.append(f"previous hash mismatch at seq {event['seq']}")
            recalculated = event_digest(
                event["seq"], event["event_id"], event["aggregate_id"],
                event["occurred_at"], event["event_type"], event["actor"],
                event["payload_json"], event["previous_hash"]
            )
            if recalculated != event["event_hash"]:
                errors.append(f"event hash mismatch at seq {event['seq']}")
            expected_previous = event["event_hash"]
            expected_seq = event["seq"] + 1
        return {
            "valid": not errors, "records_checked": len(events),
            "errors": errors,
            "head_hash": expected_previous if events else GENESIS_HASH,
        }

    @staticmethod
    def _decode(row):
        result = dict(row)
        result["payload"] = json.loads(result["payload_json"])
        return result
