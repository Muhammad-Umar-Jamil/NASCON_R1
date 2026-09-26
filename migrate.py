import sqlite3
try:
    conn = sqlite3.connect('app.db')
    conn.execute("ALTER TABLE settings ADD COLUMN api_endpoint VARCHAR NOT NULL DEFAULT 'openrouter'")
    conn.commit()
    conn.close()
    print("Column added successfully")
except Exception as e:
    print("Error:", e)
