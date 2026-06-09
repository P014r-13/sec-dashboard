from flask_bcrypt import Bcrypt
from database.db import get_connection
import secrets, datetime

bcrypt = Bcrypt()

def seed():
    conn = get_connection()
    cur = conn.cursor()

    # check already seeded
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        print("Already seeded, skipping.")
        conn.close()
        return

    # admin user
    pw = bcrypt.generate_password_hash("admin123").decode("utf-8")
    cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("admin@example.com", pw))
    user_id = cur.lastrowid

    # settings
    cur.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))

    # projects
    projects = [
        ("E-Commerce App", "online"),
        ("Admin Panel",    "warning"),
        ("Mobile API",     "online"),
        ("Internal Tools", "offline"),
    ]
    project_ids = []
    for name, status in projects:
        key = "sk-" + secrets.token_hex(4)
        cur.execute(
            "INSERT INTO projects (user_id, name, api_key, status) VALUES (?, ?, ?, ?)",
            (user_id, name, key, status)
        )
        project_ids.append(cur.lastrowid)

    # login events
    events = [
        (project_ids[0], "ali@example.com",    "185.220.101.45", "🇮🇷 Iran",        "Chrome / Windows", "success"),
        (project_ids[1], "admin@myapp.com",    "91.108.4.10",    "🇩🇪 Germany",     "Firefox / Linux",  "suspicious"),
        (project_ids[2], "reza@test.com",      "5.79.71.225",    "🇳🇱 Netherlands", "Safari / iOS",     "failed"),
        (project_ids[0], "sara@example.com",   "78.46.90.12",    "🇮🇷 Iran",        "Chrome / macOS",   "success"),
        (project_ids[1], "admin@myapp.com",    "91.108.4.10",    "🇩🇪 Germany",     "Firefox / Linux",  "failed"),
        (project_ids[1], "admin@myapp.com",    "91.108.4.10",    "🇩🇪 Germany",     "Firefox / Linux",  "failed"),
        (project_ids[2], "karim@mobile.io",    "188.40.13.76",   "🇫🇷 France",      "App / Android",    "success"),
        (project_ids[3], "devops@internal.com","10.0.0.1",       "🇮🇷 Iran",        "Chrome / Ubuntu",  "success"),
    ]
    for pid, email, ip, country, device, status in events:
        cur.execute(
            "INSERT INTO login_events (project_id, user_email, ip, country, device, status) VALUES (?,?,?,?,?,?)",
            (pid, email, ip, country, device, status)
        )

    # alerts
    alerts = [
        (project_ids[1], "brute_force",   "۵ تلاش ناموفق متوالی از IP: 91.108.4.10", "critical"),
        (project_ids[0], "new_location",  "لاگین از موقعیت جدید: آلمان",             "medium"),
        (project_ids[2], "suspicious_ip", "لاگین از IP مشکوک: 5.79.71.225",          "high"),
        (project_ids[1], "multiple_fail", "۱۲ لاگین ناموفق در ۱ ساعت اخیر",          "high"),
    ]
    for pid, atype, msg, severity in alerts:
        cur.execute(
            "INSERT INTO alerts (project_id, type, message, severity) VALUES (?,?,?,?)",
            (pid, atype, msg, severity)
        )

    conn.commit()
    conn.close()
    print("✓ Seed data inserted — email: admin@example.com | password: admin123")