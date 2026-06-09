from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_connection
from utils.response import success, error
import secrets

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


def _enrich(row):
    d    = dict(row)
    conn = get_connection()
    d["total_logins"]  = conn.execute(
        "SELECT COUNT(*) FROM login_events WHERE project_id = ?", (d["id"],)
    ).fetchone()[0]
    d["failed_logins"] = conn.execute(
        "SELECT COUNT(*) FROM login_events WHERE project_id = ? AND status='failed'",
        (d["id"],)
    ).fetchone()[0]
    d["suspicious_logins"] = conn.execute(
        "SELECT COUNT(*) FROM login_events WHERE project_id = ? AND status='suspicious'",
        (d["id"],)
    ).fetchone()[0]
    last = conn.execute(
        "SELECT created_at FROM login_events WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
        (d["id"],)
    ).fetchone()
    d["last_activity"] = last["created_at"] if last else None
    d["unread_alerts"] = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE project_id = ? AND is_read = 0", (d["id"],)
    ).fetchone()[0]
    conn.close()
    return d


@projects_bp.route("/", methods=["GET"])
@jwt_required()
def list_projects():
    user_id = get_jwt_identity()
    conn    = get_connection()
    rows    = conn.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return success([_enrich(r) for r in rows])


@projects_bp.route("/", methods=["POST"])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    name    = data.get("name", "").strip()
    if not name:
        return error("نام پروژه الزامی است", 400)

    api_key = "sk-" + secrets.token_hex(12)
    conn    = get_connection()
    cur     = conn.execute(
        "INSERT INTO projects (user_id, name, api_key, status) VALUES (?,?,?,'online')",
        (user_id, name, api_key)
    )
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.commit()
    conn.close()
    return success(_enrich(row), "پروژه ایجاد شد", 201)


@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    conn    = get_connection()
    row     = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    ).fetchone()
    conn.close()
    if not row:
        return error("پروژه یافت نشد", 404)
    return success(_enrich(row))


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    conn    = get_connection()
    row     = conn.execute(
        "SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        return error("پروژه یافت نشد", 404)
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return success(message="پروژه حذف شد")


@projects_bp.route("/<int:project_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(project_id):
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    status  = data.get("status", "")
    if status not in ("online", "offline", "warning"):
        return error("وضعیت نامعتبر", 400)
    conn = get_connection()
    row  = conn.execute(
        "SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        return error("پروژه یافت نشد", 404)
    conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()
    return success(message="وضعیت به‌روز شد")