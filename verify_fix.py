import sqlite3
conn = sqlite3.connect('database/cdrs.db')
c = conn.cursor()

print("=== CardStatistics (latest 3 rows) ===")
c.execute("SELECT * FROM CardStatistics ORDER BY StatisticsID DESC LIMIT 3")
for r in c.fetchall():
    print(f"  ID={r[0]} Run={r[1]} SIM_ord={r[2]} SIM_cards={r[3]} Bank_ord={r[4]} Bank_cards={r[5]} Tot_ord={r[6]} Tot_cards={r[7]}")

print("\n=== Totals ===")
c.execute("SELECT COALESCE(SUM(TotalCards),0) as tc, COALESCE(SUM(SIMOrders),0) as so, COALESCE(SUM(BankOrders),0) as bo FROM CardStatistics")
r = c.fetchone()
print(f"  SIM_orders={r[1]}, SIM_cards={r[1]*100}, Bank_orders={r[2]}, Bank_cards={r[2]*300}, Total_cards={r[0]}")

print("\n=== SIM_MULTIPLIER Setting ===")
c.execute("SELECT * FROM Settings WHERE SettingName='SIM_MULTIPLIER'")
print(f"  {c.fetchone()}")

print("\n=== All Data Verification ===")
c.execute("SELECT SUM(SIMOrders), SUM(SIMCards), SUM(BankOrders), SUM(BankCards), SUM(TotalCards) FROM CardStatistics")
r = c.fetchone()
expected_sim = r[0] * 100
expected_bank = r[1]
expected_total = expected_sim + r[3]
print(f"  SUM SIMOrders={r[0]} -> SIMCards should be {expected_sim}, is {r[1]}")
print(f"  SUM BankOrders={r[2]} -> BankCards should be {r[2]*300}, is {r[3]}")
if r[1] == expected_sim and r[3] == r[2]*300:
    print("  ✓ All multipliers correct (SIM=100, Bank=300)")
else:
    print("  ✗ Multipliers still wrong!")

conn.close()