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
form{{display:flex;gap:8px;padding:10px 12px 14px;border-top:1px solid var(--line);
  background:var(--paper)}}
input{{flex:1;padding:12px 14px;border:1px solid var(--line);border-radius:12px;
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
            return self._send(200, PAGE.format(title=CFG.get('name', '小屋')), 'text/html; charset=utf-8')
        if u.path == '/history':
            n = int((q.get('limit') or ['30'])[0])
            return self._send(200, {'ok': True, 'messages': S.recent(n),
                                    'state': state_payload()})
        if u.path == '/state':
            return self._send(200, state_payload())
        if u.path == '/health':
            return self._send(200, {'ok': True, 'mock': MOCK})
        return self._send(404, {'ok': False, 'error': 'not found'})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != '/say':
            return self._send(404, {'ok': False, 'error': 'not found'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            data = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            text = (data.get('text') or '').strip()
            if not text:
                return self._send(400, {'ok': False, 'error': 'empty'})
            out = handle_say(text)
            return self._send(200, out)
        except Exception as e:
            return self._send(500, {'ok': False, 'error': '%s: %s' % (type(e).__name__, str(e)[:200])})


def state_payload():
    snap = H.snapshot()
    m = H.mood()
    return {'ok': True, 'mood': m.get('label'), 'words': m.get('words') or [],
            'line': m.get('line'), 'oaths': len(O.rows(status='open')),
            'said_today': S.said_today(), 'raw': {k: round(v, 1) for k, v in snap.items()
                                                  if k in ('da', 'ot', 'cort', 'end')}}


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
