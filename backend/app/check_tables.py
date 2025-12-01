# check_tables_sql.py
import sqlite3
import os


def check_tables():
    db_path = os.getenv("DATABASE_URL", "sqlite:///./evolution.db").replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем все таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("Таблицы в базе данных:")
    for table in tables:
        print(f"\n📋 Таблица: {table[0]}")
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")

    conn.close()


if __name__ == "__main__":
    check_tables()