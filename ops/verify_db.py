import sqlite3,sys
from well.ledger import WellLedger
if len(sys.argv)!=2:raise SystemExit("usage: verify_db.py DATABASE")
with sqlite3.connect(sys.argv[1]) as db:ok=db.execute("PRAGMA integrity_check").fetchone()[0]
print({"sqlite_integrity":ok})
if ok!="ok":raise SystemExit(1)
r=WellLedger(sys.argv[1]).verify();print(r)
if not r["valid"]:raise SystemExit(1)
