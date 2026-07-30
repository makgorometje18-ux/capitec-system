import sqlite3
conn = sqlite3.connect('database/cdrs.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT Username, Role, FirstLogin, AccountStatus FROM Users')
rows = cur.fetchall()
print('Users in DB:')
for r in rows:
    print(f"  {r['Username']} | {r['Role']} | FirstLogin={r['FirstLogin']} | {r['AccountStatus']}")
conn.close()