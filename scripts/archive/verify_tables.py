import sqlite3
conn = sqlite3.connect('skillos.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
count = cursor.fetchone()[0]
print(f'Total tables: {count}')
conn.close()
