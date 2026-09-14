import sqlite3
from werkzeug.security import generate_password_hash


DATABASE = "students.db"


def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_db_connection()


    # =========================
    # USERS TABLE
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)


    # =========================
    # STUDENTS TABLE
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            section TEXT NOT NULL
        )
    """)


    # =========================
    # DEFAULT ADMIN
    # =========================

    existing_user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    ).fetchone()


    if existing_user is None:

        password_hash = generate_password_hash("admin123")

        conn.execute(
            """
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
            """,
            (
                "admin",
                password_hash,
                "Admin"
            )
        )


    conn.commit()

    conn.close()