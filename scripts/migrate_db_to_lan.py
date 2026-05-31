import os
import sys
from pathlib import Path
from typing import Dict

import mysql.connector
from dotenv import dotenv_values


def load_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")
    return {k: v for k, v in dotenv_values(path).items() if k}


def get_connection(config: Dict[str, str]):
    return mysql.connector.connect(
        host=config.get("DB_HOST"),
        port=int(config.get("DB_PORT", 3306)),
        user=config.get("DB_USER"),
        password=config.get("DB_PASS"),
        database=config.get("DB_NAME"),
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False,
    )


def validate_env(config: Dict[str, str], name: str):
    required = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASS", "DB_NAME"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError(f"Missing {name} settings: {', '.join(missing)}")


def get_table_list(conn):
    with conn.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        return [row[0] for row in cursor.fetchall()]


def migrate_table_structure(src_conn, tgt_conn, table_name):
    with src_conn.cursor() as cursor:
        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        create_stmt = cursor.fetchone()[1]

    with tgt_conn.cursor() as cursor:
        cursor.execute(f"SET FOREIGN_KEY_CHECKS=0")
        cursor.execute(create_stmt)
        cursor.execute(f"SET FOREIGN_KEY_CHECKS=1")


def migrate_table_data(src_conn, tgt_conn, table_name):
    with src_conn.cursor(dictionary=True) as src_cursor:
        src_cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = src_cursor.fetchall()

        if not rows:
            return

        columns = list(rows[0].keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_list = ", ".join([f"`{col}`" for col in columns])
        insert_sql = f"INSERT INTO `{table_name}` ({column_list}) VALUES ({placeholders})"

        with tgt_conn.cursor() as tgt_cursor:
            batch_size = 200
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                values = [tuple(row[col] for col in columns) for row in batch]
                tgt_cursor.executemany(insert_sql, values)
            tgt_conn.commit()


def ensure_target_empty(conn):
    tables = get_table_list(conn)
    if tables:
        raise RuntimeError(
            "Target database already contains tables. "
            "Please migrate into an empty target database or drop existing tables first."
        )


def main():
    root = Path(__file__).resolve().parent.parent
    source_env_path = root / ".env"
    target_env_path = root / ".env.lan"

    source_config = load_env_file(source_env_path)
    target_config = load_env_file(target_env_path)

    validate_env(source_config, "source")
    validate_env(target_config, "target")

    print("Loading source database from .env and target database from .env.lan...")

    src_conn = get_connection(source_config)
    tgt_conn = get_connection(target_config)

    try:
        ensure_target_empty(tgt_conn)

        tables = get_table_list(src_conn)
        if not tables:
            print("No tables found in source database. Nothing to migrate.")
            return

        print(f"Found {len(tables)} tables in source database.")
        for table in tables:
            print(f"Migrating structure for table: {table}")
            migrate_table_structure(src_conn, tgt_conn, table)
            print(f"Migrating data for table: {table}")
            migrate_table_data(src_conn, tgt_conn, table)

        print("Migration complete. All tables and data have been copied to the target LAN database.")

    except Exception as exc:
        print(f"Migration failed: {exc}")
        sys.exit(1)
    finally:
        if src_conn.is_connected():
            src_conn.close()
        if tgt_conn.is_connected():
            tgt_conn.close()


if __name__ == "__main__":
    main()
