# -----------------------------------------------
# database.py — MySQL connection & user operations
# Uses XAMPP MySQL (host: localhost, port: 3306)
# -----------------------------------------------

import mysql.connector
from mysql.connector import Error
import bcrypt
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()


def _prehash(plain: str) -> str:
    """SHA-256 pre-hash → always 64 hex chars (well within bcrypt's 72-byte limit)."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ── Password helpers (using bcrypt directly — no passlib) ──
def hash_password(plain: str) -> str:
    prehashed = _prehash(plain).encode("utf-8")
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    prehashed = _prehash(plain).encode("utf-8")
    return bcrypt.checkpw(prehashed, hashed.encode("utf-8"))


# ── DB Config (reads from .env or uses XAMPP defaults) ──
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),        # XAMPP default: no password
    "database": os.getenv("DB_NAME",     "study_assistant"),
}


def get_connection():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Database connection failed: {e}")


# ── User operations ──

def create_user(username: str, email: str, plain_password: str) -> dict:
    """
    Insert a new user into the users table.
    Returns the created user dict (without password).
    Raises ValueError if username or email already exists.
    """
    hashed = hash_password(plain_password)
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "username": username, "email": email}
    except Error as e:
        # MySQL error 1062 = Duplicate entry
        if e.errno == 1062:
            msg = str(e)
            if "username" in msg:
                raise ValueError("Username already exists.")
            elif "email" in msg:
                raise ValueError("Email already registered.")
            else:
                raise ValueError("User already exists.")
        raise
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Return user row by email, or None if not found."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def authenticate_user(email: str, plain_password: str) -> dict | None:
    """
    Verify email + password.
    Returns user dict (without password) on success, None on failure.
    """
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(plain_password, user["password"]):
        return None
    # Remove password from returned data
    user.pop("password", None)
    return user
