import sqlite3
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_app_db():
    conn = get_db_connection()
    # Crear tabla suppliers si no existe
    conn.execute("""CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nit TEXT UNIQUE,
        name TEXT,
        contact TEXT
    )""")

    # ALTER TABLES (columnas dinámicas si no existen)
    try:
        conn.execute("ALTER TABLE suppliers ADD COLUMN contact_name TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE suppliers ADD COLUMN phone TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE maintenance_items ADD COLUMN fecha_aprob_jefe TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE maintenance_items ADD COLUMN fecha_aprob_gt TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE maintenance_items ADD COLUMN fecha_aprob_gr TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE maintenance_items ADD COLUMN observaciones_recepcion TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
