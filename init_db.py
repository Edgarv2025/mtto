import os
import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = "maintenance.db"


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # User table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('ADMIN', 'READ', 'WRITE', 'JEFE_AREA', 'GT', 'COMPRAS', 'GR', 'ALMACEN'))
        )
    """)

    # Product table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            unit_of_measure TEXT NOT NULL
        )
    """)

    # Maintenance Record table (Encabezado)
    cursor.execute("""
        CREATE TABLE maintenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consecutive_no INTEGER UNIQUE NOT NULL,
            date TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            storekeeper TEXT NOT NULL,
            destination TEXT NOT NULL
        )
    """)

    # Maintenance Item table (associated with a Record)
    cursor.execute("""
        CREATE TABLE maintenance_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            product_code TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_of_measure TEXT NOT NULL,
            observaciones_solicitante TEXT,
            
            -- Trazabilidad / Estado actual
            status TEXT NOT NULL DEFAULT 'PENDIENTE_GT',
            
            -- Aprobación GT
            aprobado_gt BOOLEAN,
            observaciones_gt TEXT,
            
            -- Cotizaciones (Compras)
            prov1 TEXT, v_unit1 REAL, v_tot1 REAL,
            prov2 TEXT, v_unit2 REAL, v_tot2 REAL,
            prov3 TEXT, v_unit3 REAL, v_tot3 REAL,
            
            -- Aprobación GR
            aprobado_gr BOOLEAN,
            observaciones_gr TEXT,
            
            -- Compra Efectiva (Compras)
            fecha_compra TEXT,
            prov_compra TEXT,
            orden_compra TEXT,
            
            -- Recepción (Almacén)
            fecha_llegada TEXT,
            cant_llegada REAL,
            
            FOREIGN KEY (record_id) REFERENCES maintenance_records (id),
            FOREIGN KEY (product_code) REFERENCES products (code)
        )
    """)

    # Create dummy Users for all roles
    roles = {
        "admin": "ADMIN",
        "escritura": "WRITE",
        "lectura": "READ",
        "jefe": "JEFE_AREA",
        "tecnica": "GT",
        "compras": "COMPRAS",
        "regional": "GR",
        "almacen": "ALMACEN",
    }

    for user, role in roles.items():
        hash_pw = generate_password_hash(f"{user}123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (user, hash_pw, role),
        )

    conn.commit()
    conn.close()
    print("Database initialized successfully with new ERP roles and tracking tables.")


if __name__ == "__main__":
    init_db()
