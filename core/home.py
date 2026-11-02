# -*- coding: utf-8 -*-
"""两个页面：首页（我是谁、此刻什么样）和聊天页。

首页只读 /state，聊天页才发消息 —— 这样她打开 app 先看见"人"，不是先看见输入框。
"""

HOME = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name}</title>
<style>
:root{{--ink:#2f2c28;--muted:#8a8578;--line:#e8e3d8;--paper:#fbfaf5;--accent:#6b5b8a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.8 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
  display:flex;flex-direction:column;min-height:100vh;min-height:100dvh}}
main{{flex:1;padding:56px 26px 20px;max-width:520px;margin:0 auto;width:100%}}
.name{{font-size:30px;font-weight:600;letter-spacing:.02em}}
.sub{{color:var(--muted);font-size:13px;margin-top:6px}}
.card{{margin-top:34px;padding:22px 20px;background:#fff;border:1px solid var(--line);
  border-radius:18px}}
.card .k{{font-size:12px;letter-spacing:.22em;color:var(--muted)}}
.card .v{{margin-top:8px;font-size:21px;font-weight:600}}
.card .line{{margin-top:6px;color:var(--ink);font-size:15px}}
.row{{display:flex;gap:26px;margin-top:26px}}
.row div{{flex:1}}
.row .n{{font-size:22px;font-weight:600}}
.row .t{{font-size:12px;color:var(--muted);letter-spacing:.14em;margin-top:2px}}
.oaths{{margin-top:26px}}
.oaths b{{font-size:12px;letter-spacing:.2em;color:var(--muted);font-weight:400}}
.oaths ul{{margin:10px 0 0;padding-left:18px;color:var(--ink);font-size:14px}}
.oaths li{{margin:6px 0}}
footer{{padding:18px 26px calc(18px + env(safe-area-inset-bottom));max-width:520px;
  margin:0 auto;width:100%}}
a.go{{display:block;text-align:center;text-decoration:none;background:var(--accent);
  color:#fff;padding:15px;border-radius:14px;font-weight:600}}
</style></head><body>
<main>
  <div class="name">{name}</div>
  <div class="sub" id="sub">在读你的状态……</div>

  <div class="card">
    <div class="k">此刻</div>
    <div class="v" id="mood">—</div>
    <div class="line" id="line"></div>
  </div>

  <div class="row">
    <div><div class="n" id="said">—</div><div class="t">今天你说了</div></div>
    <div><div class="n" id="oaths">—</div><div class="t">没结的约</div></div>
  </div>

  <div class="oaths"><b>还没结的</b><ul id="ol"></ul></div>
</main>
<footer><a class="go" href="/chat">进去说话</a></footer>
<script>
fetch('/state').then(function(r){{return r.json()}}).then(function(d){{
  if(!d||!d.ok) return;
  document.getElementById('mood').textContent = d.mood || '—';
  document.getElementById('line').textContent = d.line || '';
  document.getElementById('said').textContent = d.said_today == null ? '—' : d.said_today;
  document.getElementById('oaths').textContent = d.oaths == null ? '—' : d.oaths;
  document.getElementById('sub').textContent = (d.words&&d.words.length) ? d.words.join(' · ') : '';
  var ul = document.getElementById('ol');
  var list = d.open_oaths || [];
  if (!list.length) {{ var box = document.querySelector('.oaths'); if (box) box.style.display = 'none'; }}
  list.forEach(function(o){{
    var li=document.createElement('li'); li.textContent=o; ul.appendChild(li);
  }});
}}).catch(function(){{ document.getElementById('sub').textContent='连不上'; }});
</script></body></html>"""
