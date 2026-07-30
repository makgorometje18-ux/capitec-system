import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'cdrs.db')
print(f"DB path: {db_path}")
print(f"DB exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables in database: {tables}")

if 'CardStatistics' in tables:
    cursor.execute("PRAGMA table_info(CardStatistics)")
    cols = cursor.fetchall()
    print(f"CardStatistics columns: {[c[1] for c in cols]}")
else:
    print("CardStatistics table DOES NOT EXIST in database!")

# Check data
cursor.execute("SELECT COUNT(*) FROM CardStatistics")
count = cursor.fetchone()[0]
print(f"CardStatistics row count: {count}")

conn.close()