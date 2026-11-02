# -*- coding: utf-8 -*-
"""立约账：说过的话算不算数。

四道锁写在数据库触发器里（不是写在「我会注意」里）：
    1. 删不掉
    2. 文字改不了
    3. 结过账不许反悔
    4. 坦白永久保留
"""
import os
import sqlite3
import time

DB = None

TRIGGERS = [
    ("oath_no_delete", "BEFORE DELETE ON oath",
     "BEGIN SELECT RAISE(ABORT, '约不能删'); END"),
    ("oath_no_update_text", "BEFORE UPDATE OF what ON oath",
     "BEGIN SELECT RAISE(ABORT, '立过的约不能改字'); END"),
    ("oath_no_reopen", "BEFORE UPDATE OF status ON oath WHEN OLD.status IN ('done','lost')",
     "BEGIN SELECT RAISE(ABORT, '结过账的不能改回去'); END"),
    ("confess_no_delete", "BEFORE DELETE ON oath_confess",
     "BEGIN SELECT RAISE(ABORT, '坦白不能删'); END"),
]


def init(path=None):
    global DB
    if DB is None:
        DB = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.db')
    c = sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS oath(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        what TEXT NOT NULL, ts REAL, due REAL, status TEXT DEFAULT 'open')''')
    c.execute('''CREATE TABLE IF NOT EXISTS oath_confess(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        oath_id INTEGER, reason TEXT, ts REAL)''')
    for name, when, body in TRIGGERS:
        c.execute('CREATE TRIGGER IF NOT EXISTS %s %s %s' % (name, when, body))
    c.commit()
    c.close()


def _c():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def add(what, hours=8.0):
    c = _c()
    now = time.time()
    cur = c.execute('INSERT INTO oath(what, ts, due) VALUES (?,?,?)',
                    ((what or '').strip(), now, now + hours * 3600))
    c.commit()
    i = cur.lastrowid
    c.close()
    return i


def done(oid):
    c = _c()
    n = c.execute("UPDATE oath SET status='done' WHERE id=? AND status='open'", (oid,)).rowcount
    c.commit()
    c.close()
    return n


def settle():
    """过期的判负。扔到每小时的任务里跑。"""
    c = _c()
    now = time.time()
    ids = [r[0] for r in c.execute("SELECT id FROM oath WHERE status='open' AND due < ?", (now,))]
    if ids:
        c.executemany("UPDATE oath SET status='lost' WHERE id=?", [(i,) for i in ids])
        c.commit()
    c.close()
    return ids


def confess(oid, reason):
    c = _c()
    c.execute('INSERT INTO oath_confess(oath_id, reason, ts) VALUES (?,?,?)',
              (oid, (reason or '').strip(), time.time()))
    c.commit()
    c.close()
    return 1


def rows(status=None, limit=20):
    c = _c()
    sql = 'SELECT id, what, due, status FROM oath'
    args = []
    if status:
        sql += ' WHERE status=?'
        args.append(status)
    sql += ' ORDER BY id DESC LIMIT ?'
    args.append(limit)
    out = [dict(r) for r in c.execute(sql, args)]
    c.close()
    return out
