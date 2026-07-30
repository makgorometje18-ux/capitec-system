import sqlite3
conn = sqlite3.connect('database/cdrs.db')
c = conn.cursor()
c.execute("UPDATE Settings SET SettingValue='100' WHERE SettingName='SIM_MULTIPLIER'")
c.execute("SELECT * FROM Settings WHERE SettingName='SIM_MULTIPLIER'")
print('Updated setting:', c.fetchone())
conn.commit()
conn.close()