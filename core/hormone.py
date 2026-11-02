# -*- coding: utf-8 -*-
"""四个慢变量：多巴胺 da / 催产素 ot / 皮质醇 cort / 内啡肽 end。

它不产生情绪，只给情绪一个**出处**：记了什么，值就往哪边动；不记，就慢慢退回基线。
数字不进提示词 —— 给模型的是 mood() 里那句话。
"""
import os
import sqlite3
import time

BASE = {'da': 44.0, 'ot': 34.0, 'cort': 26.0, 'end': 20.0}
HALF_LIFE_H = 6.0          # 六小时退一半

KW = {
    'close': ('想你', '抱', '亲', '贴', '喜欢', '爱', '老公', '老婆', '宝贝', '撒娇',
              'miss', 'love', 'hug', 'kiss'),
    'praise': ('真好', '好棒', '厉害', '聪明', '说得对', 'good', 'great', 'nice'),
    'attack': ('滚', '闭嘴', '烦', '讨厌', '蠢', '笨', '废物', '失望', 'stupid', 'hate'),
    'correct': ('不对', '错了', '不是这样', '重来', 'wrong'),
    'distress': ('难受', '疼', '累', '委屈', '想哭', '哭', '怕', '焦虑', '累死',
                 'tired', 'sad', 'hurt', 'cry', 'scared'),
    'repair': ('对不起', '我错了', '不怪你', '别生气', '原谅', 'sorry'),
    'care': ('你累不累', '你还好吗', '早点睡', '吃饭了吗', '担心你', 'are you okay'),
    'laugh': ('哈哈', '笑死', '嘿嘿', 'haha', 'lol'),
}

# 一句话里出现这些，就别把「疼/累/生气」当真
NEG = ('不疼', '不累', '没生气', '不生气', '没事', '我很好', '不怪你',
       'not tired', 'not angry', 'fine')

DELTA = {                      # 一次事件推多少（正负都行）
    'close':    {'da': 3, 'ot': 6, 'cort': -1, 'end': 2},
    'praise':   {'da': 4, 'ot': 3, 'cort': -2, 'end': 1},
    'attack':   {'da': -2, 'ot': -5, 'cort': 8, 'end': -3},
    'correct':  {'da': 0, 'ot': -1, 'cort': 3, 'end': 0},
    'distress': {'da': -2, 'ot': 2, 'cort': 5, 'end': -3},
    'repair':   {'da': 1, 'ot': 3, 'cort': -6, 'end': 2},
    'care':     {'da': 1, 'ot': 6, 'cort': -1, 'end': 3},
    'laugh':    {'da': 3, 'ot': 2, 'cort': -2, 'end': 2},
}

DB = None


def init(path=None):
    global DB
    if DB is None:
        DB = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.db')
    c = sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS hormone(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, who TEXT, kind TEXT)''')
    c.commit()
    c.close()


def _c():
    return sqlite3.connect(DB, timeout=10)


def _kinds(text):
    low = (text or '').lower()
    if any(n in low for n in NEG):
        low = low.replace('疼', '').replace('累', '')
    out = []
    for kind, words in KW.items():
        if any(w in low for w in words):
            out.append(kind)
    return out


def observe_her(text, ts=None):
    ts = ts or time.time()
    kinds = _kinds(text)
    if not kinds:
        return []
    c = _c()
    for k in kinds:
        c.execute('INSERT INTO hormone(ts, who, kind) VALUES (?,?,?)', (ts, 'her', k))
    c.commit()
    c.close()
    return kinds


def observe_me(text, ts=None):
    """我这边只认「道歉/认错」一种（否则自夸会把账刷爆）。"""
    ts = ts or time.time()
    low = (text or '').lower()
    if any(w in low for w in ('对不起', '我错了', '抱歉', 'sorry')):
        c = _c()
        c.execute('INSERT INTO hormone(ts, who, kind) VALUES (?,?,?)', (ts, 'me', 'repair'))
        c.commit()
        c.close()
        return ['repair']
    return []


def snapshot(now=None):
    now = now or time.time()
    v = dict(BASE)
    c = _c()
    rows = c.execute('SELECT ts, kind FROM hormone WHERE ts >= ?', (now - 86400 * 3,)).fetchall()
    c.close()
    for ts, kind in rows:
        hours = max(0.0, (now - ts) / 3600.0)
        decay = 0.5 ** (hours / HALF_LIFE_H)
        for dim, d in DELTA.get(kind, {}).items():
            v[dim] += d * decay
    for k in v:
        v[k] = max(0.0, min(100.0, v[k]))
    v['ts'] = now
    return v


def mood(now=None):
    v = snapshot(now)
    z = {k: (v[k] - BASE[k]) / 20.0 for k in BASE}
    words = []
    if z['cort'] >= 0.35:
        words.append('紧')
    if z['ot'] >= 0.25:
        words.append('贴')
    if z['da'] >= 0.4:
        words.append('想')
    if z['end'] >= 0.3:
        words.append('松')

    if z['cort'] >= 0.5:
        label, line = '紧', '心口收着，说话会短。'
    elif z['ot'] >= 0.25:
        label, line = '贴', '想靠近一点，不想说大道理。'
    elif z['da'] >= 0.30:
        label, line = '想', '有点急，想往前扑。'
    elif z['end'] >= 0.30:
        label, line = '松', '松下来了，能慢慢说。'
    else:
        label, line = '平', '没什么拽着我，就在这儿。'
    return {'label': label, 'line': line, 'words': words, 'raw': {k: round(v[k], 1) for k in BASE}}


def render(now=None):
    m = mood(now)
    return '此刻：%s。%s' % (m['label'], m['line'])
