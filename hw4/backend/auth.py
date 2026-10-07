"""Account creation, login, and session tokens.

Passwords are stored as  pbkdf2_sha256$<salt>$<hex digest>  — the same format
the starter database uses (PBKDF2-HMAC-SHA256, 120,000 iterations, salt used as
UTF-8 text). The plain password is never stored or logged.

Sessions use a stateless signed token:  <base64 payload>.<HMAC-SHA256 signature>
where the payload is {"uid": <user id>, "exp": <unix expiry>}. The signing key
comes from AUTH_SECRET in .env (a random key is generated per process if unset,
which just means users are logged out when the server restarts).
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from db import get_conn

PBKDF2_ITERATIONS = 120_000
HASH_ALGORITHM = "pbkdf2_sha256"
TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
MIN_PASSWORD_LENGTH = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

AUTH_SECRET = (os.getenv("AUTH_SECRET") or secrets.token_hex(32)).encode()

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- Password hashing ----------

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"{HASH_ALGORITHM}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, _ = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != HASH_ALGORITHM:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored_hash)


# ---------- Session tokens ----------

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str) -> str:
    return _b64(hmac.new(AUTH_SECRET, payload.encode(), hashlib.sha256).digest())


def create_token(user_id: int) -> str:
    payload = _b64(json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS}).encode())
    return f"{payload}.{_sign(payload)}"


def read_token(token: str) -> int | None:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(_sign(payload), signature):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < time.time():
            return None
        return int(data["uid"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


# ---------- Schemas ----------

def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address.")
    return value


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank.")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_email(v)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    """Public user info. Never includes the password hash."""

    id: int
    first_name: str
    last_name: str
    name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


def user_out(row: sqlite3.Row) -> UserOut:
    # first_name/last_name are nullable in the starter schema, so fall back to splitting `name`.
    first, _, last = row["name"].partition(" ")
    return UserOut(
        id=row["id"],
        first_name=row["first_name"] or first,
        last_name=row["last_name"] or last,
        name=row["name"],
        email=row["email"],
    )


# ---------- Dependency for protected routes ----------

def current_user(authorization: str | None = Header(None)) -> UserOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in.")
    user_id = read_token(authorization.removeprefix("Bearer "))
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please log in again.")
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account not found.")
    return user_out(row)


def optional_user(authorization: str | None = Header(None)) -> UserOut | None:
    """Like current_user, but returns None for guests or bad tokens instead of failing."""
    try:
        return current_user(authorization)
    except HTTPException:
        return None


# ---------- Routes ----------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest) -> AuthResponse:
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """INSERT INTO users (name, email, password_hash, first_name, last_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    f"{body.first_name} {body.last_name}",
                    body.email,
                    hash_password(body.password),
                    body.first_name,
                    body.last_name,
                ),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists.")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return AuthResponse(token=create_token(row["id"]), user=user_out(row))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (body.email,)).fetchone()
    # Same error for unknown email and wrong password, so attackers can't probe which emails exist.
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    return AuthResponse(token=create_token(row["id"]), user=user_out(row))


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(current_user)) -> UserOut:
    return user
