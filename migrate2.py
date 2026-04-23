import sqlite3


def migrate():
    conn = sqlite3.connect("maintenance.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "ALTER TABLE maintenance_items ADD COLUMN priority TEXT DEFAULT 'Media'"
        )
        print("Column priority added to maintenance_items")
    except sqlite3.OperationalError as e:
        print(f"Error or column already exists: {e}")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
