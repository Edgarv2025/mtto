import sqlite3


def migrate():
    conn = sqlite3.connect("maintenance.db")
    cursor = conn.cursor()

    # Create new table with updated constraints
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('ADMIN', 'READ', 'WRITE', 'JEFE_AREA', 'GT', 'COMPRAS', 'GR', 'ALMACEN'))
        )
    """)

    # Copy data
    cursor.execute(
        "INSERT INTO users_new SELECT id, username, password_hash, role FROM users"
    )

    # Drop old
    cursor.execute("DROP TABLE users")

    # Rename
    cursor.execute("ALTER TABLE users_new RENAME TO users")

    conn.commit()
    conn.close()
    print("Migration successful")


if __name__ == "__main__":
    migrate()
