import re
from database.db import get_connection

SUSPICIOUS_IPS = {"5.79.71.225", "91.108.4.10", "185.220.101.45"}
BRUTE_FORCE_THRESHOLD = 5
BRUTE_FORCE_WINDOW_MIN = 10

def is_suspicious_ip(ip: str) -> bool:
    return ip in SUSPICIOUS_IPS

def check_brute_force(project_id: int, ip: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM login_events
        WHERE project_id = ?
          AND ip = ?
          AND status = 'failed'
          AND created_at >= datetime('now', ? )
    """, (project_id, ip, f"-{BRUTE_FORCE_WINDOW_MIN} minutes"))
    count = cur.fetchone()[0]
    conn.close()
    return count >= BRUTE_FORCE_THRESHOLD

def create_alert_if_needed(project_id: int, ip: str, country: str, status: str):
    conn = get_connection()
    cur = conn.cursor()

    if status == "suspicious" or is_suspicious_ip(ip):
        cur.execute("""
            INSERT INTO alerts (project_id, type, message, severity)
            VALUES (?, 'suspicious_ip', ?, 'high')
        """, (project_id, f"لاگین از IP مشکوک: {ip}"))

    if check_brute_force(project_id, ip):
        cur.execute("""
            INSERT INTO alerts (project_id, type, message, severity)
            VALUES (?, 'brute_force', ?, 'critical')
        """, (project_id, f"تلاش‌های مکرر ناموفق از IP: {ip}"))

    conn.commit()
    conn.close()