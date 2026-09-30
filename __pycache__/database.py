# database.py
import sqlite3
from datetime import datetime

DB = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        credits INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        muted INTEGER DEFAULT 0,
        total_searches INTEGER DEFAULT 0,
        referred_by INTEGER DEFAULT 0,
        joined_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY,
        amount INTEGER,
        used INTEGER DEFAULT 0,
        used_by INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        api_type TEXT,
        query TEXT,
        result TEXT,
        timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users(user_id, credits, joined_at) VALUES(?,?,?)",
                  (uid, 5, datetime.now().isoformat()))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()
    conn.close()
    return row

def update_credits(uid, delta):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (delta, uid))
    conn.commit()
    conn.close()

def set_ban(uid, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET banned=? WHERE user_id=?", (status, uid))
    conn.commit()
    conn.close()

def set_mute(uid, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET muted=? WHERE user_id=?", (status, uid))
    conn.commit()
    conn.close()

def log_search(uid, api_type, query, result):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""INSERT INTO history(user_id, api_type, query, result, timestamp)
                 VALUES(?,?,?,?,?)""",
              (uid, api_type, query, str(result)[:500], datetime.now().isoformat()))
    c.execute("UPDATE users SET total_searches = total_searches + 1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_history(uid, limit=10):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT api_type, query, timestamp FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
              (uid, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def all_users():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def count_users():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    n = c.fetchone()[0]
    conn.close()
    return n

def add_admin(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (uid,))
    conn.commit()
    conn.close()

def del_admin(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def is_admin(uid):
    from config import OWNER_ID
    if uid == OWNER_ID:
        return True
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    ok = c.fetchone() is not None
    conn.close()
    return ok

def gen_code(code, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO codes(code, amount) VALUES(?,?)", (code, amount))
    conn.commit()
    conn.close()

def redeem_code(code, uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT amount, used FROM codes WHERE code=?", (code,))
    row = c.fetchone()
    if not row or row[1]:
        conn.close()
        return None
    c.execute("UPDATE codes SET used=1, used_by=? WHERE code=?", (uid, code))
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (row[0], uid))
    conn.commit()
    conn.close()
    return row[0]

def get_setting(key, default=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else default

def set_setting(key, value):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))
    conn.commit()
    conn.close()