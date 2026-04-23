import sqlite3
import os

DB_PATH = "maintenance.db"

def reset_data():
    if not os.path.exists(DB_PATH):
        print("Base de datos no encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Borrar registros de trazabilidad y mantenimiento
        print("Borrando items de mantenimiento...")
        cursor.execute("DELETE FROM maintenance_items")
        
        print("Borrando encabezados de mantenimiento...")
        cursor.execute("DELETE FROM maintenance_records")
        
        # Reiniciar los contadores AUTOINCREMENT de esas tablas
        print("Reiniciando contadores autoincrementables...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='maintenance_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='maintenance_records'")
        
        # Opcional: ¿Se borran también productos y proveedores? 
        # Normalmente cuando se reinician "contadores" se borran solo transacciones, dejando catalogos intactos.
        # Solo dejaremos limpios los registros de transacciones.
        
        conn.commit()
        print("¡Datos transaccionales eliminados y contadores en cero! Usuarios, productos y proveedores permanecen intactos.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_data()
