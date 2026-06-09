from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_connection
from utils.response import success, error

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


@alerts_bp.route("/", methods=["GET"])
@jwt_required()
def list_alerts():
    user_id  = get_jwt_identity()
    only_unread = request.args.get("unread") == "true"
    severity    = request.args.get("severity")

    query  = """
        SELECT a.*, p.name AS project_name
        FROM alerts a
        JOIN projects p ON a.project_id = p.id
        WHERE p.user_id = ?
    """
    params = [user_id]
    if only_unread:
        query += " AND a.is_read = 0"
    if severity and severity != "all":
        query += " AND a.severity = ?"
        params.append(severity)
    query += " ORDER BY a.created_at DESC LIMIT 100"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return success([dict(r) for r in rows])


@alerts_bp.route("/<int:alert_id>/read", methods=["PATCH"])
@jwt_required()
def mark_read(alert_id):
    user_id = get_jwt_identity()
    conn = get_connection()
    row = conn.execute(
        "SELECT a.id FROM alerts a JOIN projects p ON a.project_id=p.id WHERE a.id=? AND p.user_id=?",
        (alert_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        return error("هشدار یافت نشد", 404)
    conn.execute("UPDATE alerts SET is_read=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
    return success(message="هشدار خوانده شد")


@alerts_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    conn = get_connection()
    conn.execute("""
        UPDATE alerts SET is_read=1
        WHERE project_id IN (SELECT id FROM projects WHERE user_id=?)
    """, (user_id,))
    conn.commit()
    conn.close()
    return success(message="همه هشدارها خوانده شد")