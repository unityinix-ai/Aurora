import sqlite3,sys
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit("usage: backup_db.py SOURCE DESTINATION")
src,dst=Path(sys.argv[1]),Path(sys.argv[2])
if not src.is_file():raise SystemExit("source database not found")
dst.parent.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(src) as a,sqlite3.connect(dst) as b:a.backup(b)
print("backup created:",dst)
