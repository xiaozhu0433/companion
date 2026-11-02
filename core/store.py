# -*- coding: utf-8 -*-
"""最小存储：一个 SQLite 文件，一张消息表。"""
import os
import sqlite3
import time

DB = None


def init(path):
    global DB
    DB = path
    c = sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, role TEXT, content TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS ix_msg_ts ON messages(ts)')
    c.commit()
    c.close()


def _c():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def add(role, content):
    c = _c()
    c.execute('INSERT INTO messages(ts, role, content) VALUES (?,?,?)', (time.time(), role, content))
    c.commit()
    c.close()


def recent(n=30):
    c = _c()
    rows = c.execute('SELECT role, content, ts FROM messages ORDER BY id DESC LIMIT ?', (n,)).fetchall()
    c.close()
    return [{'role': r['role'], 'content': r['content'], 'ts': r['ts']} for r in reversed(rows)]


def said_today():
    t0 = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    c = _c()
    n = c.execute("SELECT count(*) FROM messages WHERE role='user' AND ts>=?", (t0,)).fetchone()[0]
    c.close()
    return n


def clear_messages():
    """只清聊天记录；约和激素账都不动。"""
    c = _c()
    n = c.execute('SELECT count(*) FROM messages').fetchone()[0]
    c.execute('DELETE FROM messages')
    c.commit()
    c.close()
    return n
