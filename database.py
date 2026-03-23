import sqlite3

def init_db():
    conn = sqlite3.connect("numberplate.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT,
            plate_text TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_record(image_name, plate_text):
    conn = sqlite3.connect("numberplate.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO records (image_name, plate_text) VALUES (?, ?)",
        (image_name, plate_text)
    )

    conn.commit()
    conn.close()

def get_all_records():
    conn = sqlite3.connect("numberplate.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM records ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows