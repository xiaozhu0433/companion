# -*- coding: utf-8 -*-
"""companion · 最小可跑的「长期陪伴」服务（只用标准库）。

一个人格、会记事、会记约、有四个慢变量（激素账）。
数据全在一个 SQLite 文件里，不上云。

用法：
    python3 server.py                 # 读 config.json，起在 127.0.0.1:8388
    python3 server.py --port 9000
    python3 server.py --mock          # 不调模型，回声（先看界面用）
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import core.hormone as H          # noqa: E402
import core.oath as O             # noqa: E402
import core.store as S            # noqa: E402
from core import llm, prompt      # noqa: E402
from core.pages import HOME, CHAT, SETTINGS  # noqa: E402

CFG = {}
MOCK = False

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<style>
:root{{--ink:#2f2c28;--muted:#8a8578;--line:#e8e3d8;--paper:#fbfaf5;--accent:#6b5b8a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.75 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
  display:flex;flex-direction:column;height:100vh;height:100dvh}}
header{{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;
  align-items:baseline;gap:10px}}
header b{{font-size:17px;font-weight:600}}
header small{{color:var(--muted);font-size:12px}}
#log{{flex:1;overflow-y:auto;padding:16px 18px 8px}}
.m{{margin:0 0 14px;max-width:86%;white-space:pre-wrap;word-break:break-word}}
.me{{margin-left:auto;background:#f1ece2;border-radius:14px 14px 4px 14px;padding:9px 13px}}
.her{{background:#fff;border:1px solid var(--line);border-radius:14px 14px 14px 4px;padding:9px 13px}}
form{{display:grid;grid-template-columns:1fr auto;gap:8px;padding:10px 12px 14px;
  border-top:1px solid var(--line);background:var(--paper)}}
input{{width:100%;min-width:0;padding:12px 14px;border:1px solid var(--line);border-radius:12px;
  background:#fff;font:inherit;color:inherit}}
input:focus{{outline:2px solid #cfc6dd;outline-offset:1px}}
button{{padding:12px 18px;border:0;border-radius:12px;background:var(--accent);
  color:#fff;font:inherit;font-weight:600}}
button:disabled{{opacity:.5}}
#st{{padding:0 18px 8px;color:var(--muted);font-size:12px}}
</style></head><body>
<header><b>{title}</b><small id="st"></small></header>
<div id="log"></div>
<form id="f"><input id="q" placeholder="说点什么……" autocomplete="off">
<button id="b">说</button></form>
<script>
var log=document.getElementById('log'), st=document.getElementById('st');
function add(who,txt){{
  var d=document.createElement('div');
  d.className='m '+(who==='me'?'me':'her');
  d.textContent=txt; log.appendChild(d); log.scrollTop=log.scrollHeight;
}}
function state(s){{
  if(!s||!s.ok) return;
  st.textContent = (s.mood||'') + (s.words&&s.words.length ? (' · '+s.words.join(' ')) : '')
    + (s.oaths ? (' · 约 '+s.oaths+' 条') : '');
}}
fetch('/history?limit=40').then(function(r){{return r.json()}}).then(function(d){{
  (d.messages||[]).forEach(function(m){{ add(m.role==='user'?'me':'her', m.content); }});
  state(d.state);
}});
document.getElementById('f').addEventListener('submit',function(e){{
  e.preventDefault();
  var q=document.getElementById('q'), b=document.getElementById('b');
  var t=q.value.trim(); if(!t) return;
  add('me',t); q.value=''; b.disabled=true;
  fetch('/say',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{text:t}})}})
   .then(function(r){{return r.json()}})
   .then(function(d){{
     add('her', d.reply || ('（出错：'+(d.error||'没回话')+'）'));
     state(d.state);
   }}).catch(function(e){{ add('her','连不上了：'+e); }})
   .then(function(){{ b.disabled=false; q.focus(); }});
}});
</script></body></html>"""


def load_cfg():
    global CFG
    p = os.path.join(HERE, 'config.json')
    if not os.path.exists(p):
        raise SystemExit('没有 config.json —— 把 config.json.example 复制一份改名，填上 key')
    with open(p, encoding='utf-8') as f:
        CFG = json.load(f)
    CFG.setdefault('port', 8388)
    CFG.setdefault('name', '小屋')
    CFG.setdefault('persona', '')
    CFG.setdefault('her_name', '你')


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):      # 安静点，别把终端刷满
        pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path == '/':
            # 2026-11-02 她：「是不是得有个首页呀」—— 打开先看见人，再看见输入框
            return self._send(200, HOME.replace('{name}', CFG.get('name', '小屋')),
                              'text/html; charset=utf-8')
        if u.path == '/chat':
            return self._send(200, CHAT.replace('{name}', CFG.get('name', '小屋')),
                              'text/html; charset=utf-8')
        if u.path.startswith('/static/'):
            return self._static(u.path[len('/static/'):])
        if u.path == '/history':
            n = int((q.get('limit') or ['30'])[0])
            return self._send(200, {'ok': True, 'messages': S.recent(n),
                                    'state': state_payload()})
        if u.path == '/settings':
            return self._send(200, SETTINGS.replace('{name}', CFG.get('name', '陪伴')),
                              'text/html; charset=utf-8')
        if u.path == '/config':
            pub = {k: v for k, v in CFG.items() if k not in ('api_key',)}
            pub['api_key_set'] = bool(CFG.get('api_key'))
            return self._send(200, pub)
        if u.path == '/state':
            return self._send(200, state_payload())
        if u.path == '/health':
            return self._send(200, {'ok': True, 'mock': MOCK})
        return self._send(404, {'ok': False, 'error': 'not found'})

    def _static(self, rel):
        base = os.path.join(HERE, 'static')
        full = os.path.abspath(os.path.join(base, rel))
        if not full.startswith(base + os.sep) or not os.path.isfile(full):
            return self._send(404, {'ok': False, 'error': 'not found'})
        ctype = 'text/css; charset=utf-8' if full.endswith('.css') else 'application/octet-stream'
        with open(full, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n).decode('utf-8') or '{}')

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            data = self._body()
            if u.path == '/say':
                text = (data.get('text') or '').strip()
                if not text:
                    return self._send(400, {'ok': False, 'error': 'empty'})
                return self._send(200, handle_say(text))
            if u.path == '/oath':
                what = (data.get('what') or '').strip()
                if not what:
                    return self._send(400, {'ok': False, 'error': '约的内容是空的'})
                hours = float(data.get('hours') or 8)
                oid = O.add(what, hours)
                return self._send(200, {'ok': True, 'id': oid})
            if u.path == '/config':
                saved = save_config(data)
                return self._send(200, saved)
            if u.path == '/reset':
                n = S.clear_messages()
                return self._send(200, {'ok': True, 'deleted': n})
            return self._send(404, {'ok': False, 'error': 'not found'})
        except Exception as e:
            return self._send(500, {'ok': False, 'error': '%s: %s' % (type(e).__name__, str(e)[:200])})


def state_payload():
    snap = H.snapshot()
    m = H.mood()
    open_oaths = [o['what'] for o in O.rows(status='open', limit=5)]
    return {'ok': True, 'mood': m.get('label'), 'words': m.get('words') or [],
            'line': m.get('line'), 'oaths': len(O.rows(status='open', limit=50)),
            'open_oaths': open_oaths,
            'said_today': S.said_today(),
            'raw': {k: round(v, 1) for k, v in snap.items() if k in ('da', 'ot', 'cort', 'end')}}


def handle_say(text):
    S.add('user', text)
    H.observe_her(text)

    history = S.recent(int(CFG.get('history', 20)))
    msgs = prompt.build(CFG, history, H, O)
    if MOCK:
        reply = '（mock）我听见了：' + text
    else:
        reply = llm.chat(CFG, msgs)

    S.add('assistant', reply)
    H.observe_me(reply)
    return {'ok': True, 'reply': reply, 'state': state_payload()}


def save_config(data):
    """写 config.json（字段白名单），同时更新内存里的 CFG。

    api_key 传空 = 不改；传别的 = 覆盖。返回里永远不带 key。
    """
    allowed = ('name', 'her_name', 'persona', 'base_url', 'model',
               'temperature', 'max_tokens', 'history', 'port')
    for k in allowed:
        if k in data and data[k] not in (None, ''):
            if k in ('temperature',):
                CFG[k] = float(data[k])
            elif k in ('max_tokens', 'history', 'port'):
                CFG[k] = int(data[k])
            else:
                CFG[k] = str(data[k]).strip()
    key = (data.get('api_key') or '').strip()
    if key:
        CFG['api_key'] = key
    path = os.path.join(HERE, 'config.json')
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(CFG, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    pub = {k: v for k, v in CFG.items() if k != 'api_key'}
    pub['api_key_set'] = bool(CFG.get('api_key'))
    return {'ok': True, 'config': pub}


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=0)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--mock', action='store_true')
    a = ap.parse_args()
    MOCK = a.mock

    load_cfg()
    S.init(os.path.join(HERE, 'data.db'))
    H.init()
    O.init()

    port = a.port or int(CFG.get('port') or 8388)
    srv = ThreadingHTTPServer((a.host, port), Handler)
    print('companion 在 http://%s:%d' % (a.host, port))
    print('  模型: %s' % ('mock（不调接口）' if MOCK else (CFG.get('base_url') or '?')))
    print('  数据: %s' % os.path.join(HERE, 'data.db'))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n停了。')


if __name__ == '__main__':
    main()
