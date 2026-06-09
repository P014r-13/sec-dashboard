from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import get_connection
from utils.response import success, error
from utils.security import create_alert_if_needed

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.route("/", methods=["GET"])
@jwt_required()
def list_events():
    user_id    = get_jwt_identity()
    project_id = request.args.get("project_id")
    status     = request.args.get("status")
    search     = request.args.get("search", "")
    limit      = min(int(request.args.get("limit", 50)), 200)
    offset     = int(request.args.get("offset", 0))

    query  = """
        SELECT e.*, p.name AS project_name
        FROM login_events e
        JOIN projects p ON e.project_id = p.id
        WHERE p.user_id = ?
    """
    params = [user_id]

    if project_id:
        query += " AND e.project_id = ?"
        params.append(project_id)
    if status and status != "all":
        query += " AND e.status = ?"
        params.append(status)
    if search:
        query += " AND (e.user_email LIKE ? OR e.ip LIKE ? OR p.name LIKE ?)"
        like    = f"%{search}%"
        params += [like, like, like]

    count_query  = query.replace(
        "SELECT e.*, p.name AS project_name", "SELECT COUNT(*)"
    )
    total        = get_connection().execute(count_query, params).fetchone()[0]

    query += " ORDER BY e.created_at DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return success({"events": [dict(r) for r in rows], "total": total})


@events_bp.route("/ingest", methods=["POST"])
def ingest_event():
    """
    پروژه‌های خارجی این endpoint رو صدا می‌زنن.
    Header:  X-Api-Key: sk-...
    Body:    { user_email, ip, country, device, status }
    """
    api_key = request.headers.get("X-Api-Key", "")
    if not api_key:
        return error("API Key الزامی است", 401)

    conn    = get_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE api_key = ?", (api_key,)
    ).fetchone()
    conn.close()

    if not project:
        return error("API Key نامعتبر است", 401)

    data       = request.get_json() or {}
    user_email = data.get("user_email", "unknown")
    ip         = data.get("ip", "0.0.0.0")
    country    = data.get("country", "Unknown")
    device     = data.get("device", "Unknown")
    status     = data.get("status", "success")

    if status not in ("success", "failed", "suspicious"):
        return error("وضعیت نامعتبر است", 400)

    conn = get_connection()
    conn.execute(
        "INSERT INTO login_events (project_id, user_email, ip, country, device, status) VALUES (?,?,?,?,?,?)",
        (project["id"], user_email, ip, country, device, status)
    )
    conn.commit()
    conn.close()

    create_alert_if_needed(project["id"], ip, country, status)
    return success(message="رویداد ثبت شد", status=201)


@events_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    user_id    = get_jwt_identity()
    project_id = request.args.get("project_id")

    base   = """
        FROM login_events e
        JOIN projects p ON e.project_id = p.id
        WHERE p.user_id = ?
    """
    params = [user_id]
    if project_id:
        base  += " AND e.project_id = ?"
        params.append(project_id)

    conn = get_connection()

    total      = conn.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
    failed     = conn.execute(f"SELECT COUNT(*) {base} AND e.status='failed'",     params).fetchone()[0]
    suspicious = conn.execute(f"SELECT COUNT(*) {base} AND e.status='suspicious'", params).fetchone()[0]

    weekly = conn.execute(f"""
        SELECT
            strftime('%w', e.created_at) AS dow,
            strftime('%d/%m', e.created_at) AS label,
            SUM(CASE WHEN e.status='success'    THEN 1 ELSE 0 END) AS success,
            SUM(CASE WHEN e.status='failed'     THEN 1 ELSE 0 END) AS failed,
            SUM(CASE WHEN e.status='suspicious' THEN 1 ELSE 0 END) AS suspicious
        {base}
          AND e.created_at >= datetime('now', '-7 days')
        GROUP BY strftime('%Y-%m-%d', e.created_at)
        ORDER BY e.created_at
    """, params).fetchall()

    top_ips = conn.execute(f"""
        SELECT e.ip, COUNT(*) AS count,
               SUM(CASE WHEN e.status='failed' THEN 1 ELSE 0 END) AS failed_count
        {base}
        GROUP BY e.ip
        ORDER BY count DESC
        LIMIT 5
    """, params).fetchall()

    conn.close()
    return success({
        "total":      total,
        "failed":     failed,
        "suspicious": suspicious,
        "weekly":     [dict(r) for r in weekly],
        "top_ips":    [dict(r) for r in top_ips],
    })