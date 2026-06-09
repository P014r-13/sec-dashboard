from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from database.db import get_connection
from utils.response import success, error
from datetime import timedelta

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()


@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return error("ایمیل و رمز عبور الزامی است", 400)
    if len(password) < 8:
        return error("رمز عبور حداقل ۸ کاراکتر باشد", 400)

    conn = get_connection()
    exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if exists:
        conn.close()
        return error("این ایمیل قبلاً ثبت شده است", 409)

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    cur    = conn.execute(
        "INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed)
    )
    user_id = cur.lastrowid
    conn.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    token = create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(hours=1)
    )
    return success(
        {"token": token, "user": {"id": user_id, "email": email}},
        "ثبت‌نام موفق",
        201
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return error("ایمیل و رمز عبور الزامی است", 400)

    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return error("ایمیل یا رمز عبور اشتباه است", 401)

    token = create_access_token(
        identity=str(user["id"]),
        expires_delta=timedelta(hours=1)
    )
    return success({
        "token": token,
        "user": {"id": user["id"], "email": user["email"]}
    }, "ورود موفق")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    conn