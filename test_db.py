import sqlite3
conn = sqlite3.connect('artifacts/surveillance.db')
print("Recent zone_intrusion alerts:")
for r in conn.execute('SELECT id, activity_type, event_state, snapshot_path, datetime(timestamp) FROM alerts WHERE activity_type="zone_intrusion" ORDER BY id DESC LIMIT 10'):
    print(f"ID:{r[0]} Type:{r[1]} State:{r[2]} Path:{r[3]} Time:{r[4]}")
conn.close()
