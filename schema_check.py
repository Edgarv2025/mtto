import sqlite3


def print_schemas():
    conn = sqlite3.connect("D:\\PROGRAMACION\\Mtto\\maintenance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"--- Table: {row[0]} ---")
        print(row[1])
        print("\n")


if __name__ == "__main__":
    print_schemas()
