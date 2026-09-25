"""
Authentication: password hashing (bcrypt), signup/login, session state helpers.
"""
import bcrypt
import streamlit as st
import db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def signup(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    existing = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    if existing:
        return False, "That username is already taken."
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, hash_password(password)),
    )
    return True, "Account created."


def login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    user = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not user or not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    return True, "Logged in."


def logout():
    for key in ("user_id", "username"):
        st.session_state.pop(key, None)


def current_user_id():
    return st.session_state.get("user_id")


def require_login():
    """Call at the top of every page. Redirects to app.py if not logged in."""
    if not current_user_id():
        st.warning("Please log in first.")
        st.stop()
