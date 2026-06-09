from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_connection
from utils.response import success, error

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@settings_bp.route("/", methods=["GET"])
@jwt_required()
def get_settings():
    user_id = get_jwt_identity()
    conn = get_connection()
    row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return error("تنظیمات یافت نشد", 404)
    return success(dict(row))


@settings_bp.route("/", methods=["PUT"])
@jwt_required()
def update_settings():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    fields = {
        "session_timeout_min":  data.get("session_timeout_min"),
        "ip_whitelist":         data.get("ip_whitelist"),
        "notify_email":         data.get("notify_email"),
        "notify_webhook":       data.get("notify_webhook"),
        "notify_brute_force":   data.get("notify_brute_force"),
        "notify_new_location":  data.get("notify_new_location"),
        "notify_suspicious_ip": data.get("notify_suspicious_ip"),
        "webhook_url":          data.get("webhook_url"),
    }
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        return error("هیچ فیلدی برای به‌روزرسانی ارسال نشد", 400)

    updates["updated_at"] = "datetime('now')"
    set_clause = ", ".join(f"{k} = ?" for k in updates if k != "updated_at")
    set_clause += ", updated_at = datetime('now')"
    values = [v for k, v in updates.items() if k != "updated_at"]
    values.append(user_id)

    conn = get_connection()
    conn.execute(f"UPDATE settings SET {set_clause} WHERE user_id = ?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return success(dict(row), "تنظیمات ذخیره شد")