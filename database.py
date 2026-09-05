import sqlite3
from datetime import datetime

DATABASE_NAME = "finance.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'RUB',
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]

    if "currency" not in columns:
        cursor.execute("""
            ALTER TABLE transactions
            ADD COLUMN currency TEXT NOT NULL DEFAULT 'RUB'
        """)

    connection.commit()
    connection.close()


def add_user(telegram_id, language):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users
        (telegram_id, language, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET language = excluded.language
    """, (
        telegram_id,
        language,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


def get_user_language(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT language
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


def change_language(telegram_id, language):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
    """, (
        language,
        telegram_id
    ))

    connection.commit()
    connection.close()


def add_transaction(
    telegram_id,
    amount,
    currency,
    transaction_type,
    category,
    comment=""
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (
            telegram_id,
            amount,
            currency,
            type,
            category,
            comment,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id,
        amount,
        currency,
        transaction_type,
        category,
        comment,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


def get_transactions(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            amount,
            currency,
            type,
            category,
            comment,
            created_at
        FROM transactions
        WHERE telegram_id = ?
        ORDER BY created_at DESC
    """, (telegram_id,))

    transactions = cursor.fetchall()

    connection.close()

    return transactions


def get_transactions_between(
    telegram_id,
    start_date,
    end_date
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            amount,
            currency,
            type,
            category,
            comment,
            created_at
        FROM transactions
        WHERE telegram_id = ?
        AND created_at >= ?
        AND created_at < ?
        ORDER BY created_at DESC
    """, (
        telegram_id,
        start_date,
        end_date
    ))

    transactions = cursor.fetchall()

    connection.close()

    return transactions


def delete_all_transactions(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE telegram_id = ?
    """, (telegram_id,))

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count


def delete_transactions_between(
    telegram_id,
    start_date,
    end_date
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE telegram_id = ?
        AND created_at >= ?
        AND created_at < ?
    """, (
        telegram_id,
        start_date,
        end_date
    ))

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count


def delete_transactions_by_type_between(
    telegram_id,
    transaction_type,
    start_date,
    end_date
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE telegram_id = ?
        AND type = ?
        AND created_at >= ?
        AND created_at < ?
    """, (
        telegram_id,
        transaction_type,
        start_date,
        end_date
    ))

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count


def delete_transactions_by_type(telegram_id, transaction_type):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE telegram_id = ?
        AND type = ?
    """, (
        telegram_id,
        transaction_type
    ))

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count