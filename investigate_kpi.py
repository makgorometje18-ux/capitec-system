"""
Investigate KPI data flow issues.
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database/cdrs.db')
c = conn.cursor()

today = datetime.now().strftime('%Y-%m-%d')

# 1. Total Workbooks vs Today's Validations
c.execute("SELECT COUNT(DISTINCT ID) FROM WorkbookHistory WHERE DATE(ProcessDate) = ?", (today,))
wb = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM ValidationRun WHERE DATE(StartTime) = ?", (today,))
vr = c.fetchone()[0]
print(f"=== KPI COMPARISON ===")
print(f"Total Workbooks (today): {wb}")
print(f"Today's Validations:     {vr}")
print(f"Difference: {vr - wb}")
print()

# 2. CardStatistics data
c.execute("""
    SELECT 
        COALESCE(SUM(SIMOrders), 0) as sim_orders,
        COALESCE(SUM(SIMCards), 0) as sim_cards,
        COALESCE(SUM(BankOrders), 0) as bank_orders,
        COALESCE(SUM(BankCards), 0) as bank_cards,
        COALESCE(SUM(TotalCards), 0) as total_cards
    FROM CardStatistics
""")
row = c.fetchone()
print(f"=== CARD STATISTICS (ALL TIME) ===")
print(f"SIM Orders:  {row[0]}")
print(f"SIM Cards:   {row[1]}  (SIM Orders x 100 = {row[0] * 100})")
print(f"Bank Orders: {row[2]}")
print(f"Bank Cards:  {row[3]}  (Bank Orders x 300 = {row[2] * 300})")
print(f"Total Cards: {row[4]}  (SIM Cards + Bank Cards = {row[1] + row[3]})")
print()

# 3. What the API currently returns (missing sim_cards, bank_cards)
print(f"=== API CURRENTLY RETURNS ===")
print(f"sim_orders:     {row[0]}")
print(f"bank_orders:    {row[2]}")
print(f"cards_processed: {row[4]}")
print(f"sim_cards:      MISSING from API response")
print(f"bank_cards:     MISSING from API response")
print()

# 4. Check if SIM Cards label is actually showing sim_orders
print(f"=== LABEL MISMATCH ===")
print(f"HTML label 'SIM Cards' -> id='simOrders' -> shows data.sim_orders ({row[0]})")
print(f"HTML label 'Bank Cards' -> id='bankOrders' -> shows data.bank_orders ({row[2]})")
print(f"SIM Cards should show: {row[1]} (SIM cards, not orders)")
print(f"Bank Cards should show: {row[3]} (Bank cards, not orders)")
print()

# 5. Cards Processed check
print(f"=== CARDS PROCESSED ===")
print(f"Current cards_processed (TotalCards): {row[4]}")
print(f"Expected (SIM Cards + Bank Cards):    {row[1] + row[3]}")
print(f"Match: {row[4] == row[1] + row[3]}")
print()

# 6. Check if there are today-only CardStatistics
c.execute("""
    SELECT COUNT(*) FROM CardStatistics cs
    JOIN ValidationRun vr ON cs.RunID = vr.RunID
    WHERE DATE(vr.StartTime) = ?
""", (today,))
today_cs = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM CardStatistics")
all_cs = c.fetchone()[0]
print(f"CardStatistics rows (all time): {all_cs}")
print(f"CardStatistics rows (today):    {today_cs}")

conn.close()