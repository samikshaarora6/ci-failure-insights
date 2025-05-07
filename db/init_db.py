import sqlite3

def init_db():
    conn = sqlite3.connect('failures.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo TEXT,
            pr_number INTEGER,
            job_name TEXT,
            error_message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
