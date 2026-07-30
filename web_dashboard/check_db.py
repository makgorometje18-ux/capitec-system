import sqlite3
import sys
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'cdrs.db')

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [t[0] for t in cursor.fetchall()]

print("=== DATABASE TABLES ===")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<30} {count:>5} rows")

# Show sample data for key tables
print("\n=== SAMPLE DATA ===")

if 'WorkbookHistory' in tables:
    cursor.execute("SELECT * FROM WorkbookHistory LIMIT 1")
    row = cursor.fetchone()
    if row:
        cols = [desc[0] for desc in cursor.description]
        print(f"\nWorkbookHistory sample:")
        for col in cols:
            print(f"  {col}: {row[cols.index(col)]}")

if 'ValidationRun' in tables:
    cursor.execute("SELECT * FROM ValidationRun LIMIT 1")
    row = cursor.fetchone()
    if row:
        cols = [desc[0] for desc in cursor.description]
        print(f"\nValidationRun sample:")
        for col in cols:
            print(f"  {col}: {row[cols.index(col)]}")

if 'Settings' in tables:
    cursor.execute("SELECT * FROM Settings")
    rows = cursor.fetchall()
    print(f"\nSettings:")
    for row in rows:
        print(f"  {row[1]}: {row[2]}")

conn.close()
