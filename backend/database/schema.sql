PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         TEXT    NOT NULL,
    api_key      TEXT    NOT NULL UNIQUE,
    status       TEXT    NOT NULL DEFAULT 'online' CHECK(status IN ('online','offline','warning')),
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS login_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_email   TEXT    NOT NULL,
    ip           TEXT    NOT NULL,
    country      TEXT    NOT NULL DEFAULT 'Unknown',
    device       TEXT    NOT NULL DEFAULT 'Unknown',
    status       TEXT    NOT NULL CHECK(status IN ('success','failed','suspicious')),
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type         TEXT    NOT NULL CHECK(type IN ('brute_force','new_location','multiple_fail','suspicious_ip')),
    message      TEXT    NOT NULL,
    severity     TEXT    NOT NULL CHECK(severity IN ('low','medium','high','critical')),
    is_read      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    session_timeout_min  INTEGER NOT NULL DEFAULT 60,
    ip_whitelist         TEXT    NOT NULL DEFAULT '',
    notify_email         INTEGER NOT NULL DEFAULT 1,
    notify_webhook       INTEGER NOT NULL DEFAULT 0,
    notify_brute_force   INTEGER NOT NULL DEFAULT 1,
    notify_new_location  INTEGER NOT NULL DEFAULT 1,
    notify_suspicious_ip INTEGER NOT NULL DEFAULT 1,
    webhook_url          TEXT    NOT NULL DEFAULT '',
    updated_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);