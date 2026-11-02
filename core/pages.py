# -*- coding: utf-8 -*-
"""两个页面：首页 + 聊天页。皮用 Pico.css（classless），本地一份，离线也能跑。

为什么用现成的皮：自己从头调一套好看的排版，费时且容易土。
Pico 给的是默认就干净的语义排版，我们只补聊天气泡那一点。
"""

# Pico 的强调色用 CSS 变量改，别在它上面覆写一堆规则
THEME = """
<link rel="stylesheet" href="/static/pico.min.css">
<style>
html[data-theme=light]{
  --pico-primary:#3e5b4f;
  --pico-primary-hover:#334b41;
  --pico-primary-focus:rgba(62,91,79,.25);
  --pico-primary-background:#3e5b4f;
  --pico-primary-hover-background:#334b41;
  --pico-primary-border:#3e5b4f;
  --pico-primary-hover-border:#334b41;
  --pico-primary-underline:#3e5b4f;
  --pico-primary-inverse:#f7f4ea;
  --pico-border-radius:10px;
  --pico-font-family:-apple-system,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif;
}
body{background:#f7f4ea;color:#23211c;min-height:100dvh}
/* Pico 的按钮颜色变量链太绕，直接给按钮上色，别跟它绕 */
button,[role=button]{background:#3e5b4f;border-color:#3e5b4f;color:#f7f4ea}
button:hover,[role=button]:hover{background:#334b41;border-color:#334b41}
button:active,[role=button]:active{background:#2b3f36;border-color:#2b3f36}
.serif{font-family:'Noto Serif CJK SC','Songti SC','Source Han Serif SC',Georgia,serif}
.k{font-size:.72rem;letter-spacing:.22em;color:#7d7668;margin-bottom:.2rem}
.rule{height:1px;background:#e0d9c7;border:0;margin:1.6rem 0}
.state .v{font-size:1.7rem;line-height:1.3;margin:.2rem 0 0}
.state .line{color:#7d7668;font-size:.95rem;margin:.35rem 0 0}
.nums{display:flex;border-top:1px solid #e0d9c7;border-bottom:1px solid #e0d9c7}
.nums > div{flex:1;padding:1.1rem 0}
.nums > div + div{border-left:1px solid #e0d9c7;padding-left:1.2rem}
.nums .n{font-size:1.7rem;line-height:1.1}
.nums .t{font-size:.7rem;letter-spacing:.2em;color:#7d7668;margin-top:.3rem}
.oaths ul{margin:.6rem 0 0;padding-left:1.1rem}
.oaths li{font-size:.95rem;margin:.4rem 0}
/* 聊天 */
body.chat-body{height:100dvh;overflow:hidden}\nmain.chat{display:flex;flex-direction:column;height:100dvh;padding-bottom:0}
#log{flex:1;min-height:0;overflow-y:auto;padding:.4rem 0 1rem}
.m{max-width:84%;white-space:pre-wrap;word-break:break-word;font-size:.97rem;line-height:1.7;
  padding:.66rem .9rem;margin:0 0 .9rem;border-radius:12px}
.me{margin-left:auto;background:#efe9d9;border-radius:12px 12px 3px 12px}
.her{background:#fffdf6;border:1px solid #e0d9c7;border-radius:12px 12px 12px 3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""

HOME = """<!doctype html>
<html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name}</title>""" + THEME + """</head><body>
<main class="container">
  <hgroup>
    <h1 class="serif" style="margin-bottom:.2rem">{name}</h1>
    <p id="sub" style="color:#7d7668;font-size:.85rem;letter-spacing:.1em"></p>
  </hgroup>

  <hr class="rule">

  <section class="state">
    <div class="k">此刻</div>
    <div class="v serif" id="mood">·</div>
    <div class="line" id="line"></div>
  </section>

  <section class="nums">
    <div><div class="n serif" id="said">·</div><div class="t">今天你说了</div></div>
    <div><div class="n serif" id="oaths">·</div><div class="t">没结的约</div></div>
  </section>

  <section class="oaths" id="obox" hidden>
    <div class="k" style="margin-top:1.2rem">还没结的</div>
    <ul id="ol"></ul>
  </section>

  <div style="margin-top:2rem">
    <a href="/chat" role="button">进去说话</a>
  </div>
</main>
<script>
fetch('/state').then(function(r){return r.json()}).then(function(d){
  if(!d||!d.ok) return;
  document.getElementById('mood').textContent = d.mood || '·';
  document.getElementById('line').textContent = d.line || '';
  document.getElementById('said').textContent = d.said_today == null ? '·' : d.said_today;
  document.getElementById('oaths').textContent = d.oaths == null ? '·' : d.oaths;
  document.getElementById('sub').textContent = (d.words&&d.words.length) ? d.words.join(' · ') : '';
  var list = d.open_oaths || [];
  if(list.length){
    var box = document.getElementById('obox'), ul = document.getElementById('ol');
    box.hidden = false;
    list.forEach(function(o){ var li=document.createElement('li'); li.textContent=o; ul.appendChild(li); });
  }
}).catch(function(){ document.getElementById('sub').textContent='连不上'; });
</script></body></html>"""


CHAT = """<!doctype html>
<html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name}</title>""" + THEME + """</head><body>
<main class="container chat">
  <hgroup style="margin-bottom:.4rem;flex:none">
    <h2 class="serif" style="margin-bottom:.1rem">{name}</h2>
    <p id="st" style="color:#7d7668;font-size:.8rem;letter-spacing:.12em"></p>
  </hgroup>
  <div id="log"></div>
  <form id="f" style="display:grid;grid-template-columns:1fr auto;gap:.6rem;flex:none;margin:0 0 .6rem">
    <input id="q" placeholder="说点什么" autocomplete="off" aria-label="说点什么">
    <button id="b">说</button>
  </form>
</main>
<script>
var log=document.getElementById('log'), st=document.getElementById('st');
function add(who,txt){
  var d=document.createElement('div');
  d.className='m '+(who==='me'?'me':'her');
  d.textContent=txt; log.appendChild(d); log.scrollTop=log.scrollHeight;
}
function state(s){
  if(!s||!s.ok) return;
  st.textContent=(s.mood||'')+((s.words&&s.words.length)?(' · '+s.words.join(' ')):'');
}
fetch('/history?limit=60').then(function(r){return r.json()}).then(function(d){
  (d.messages||[]).forEach(function(m){ add(m.role==='user'?'me':'her', m.content); });
  state(d.state);
});
document.getElementById('f').addEventListener('submit',function(e){
  e.preventDefault();
  var q=document.getElementById('q'), b=document.getElementById('b');
  var t=q.value.trim(); if(!t) return;
  add('me',t); q.value=''; b.disabled=true;
  fetch('/say',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:t})})
   .then(function(r){return r.json()})
   .then(function(d){
     add('her', d.reply || ('（出错：'+(d.error||'没回话')+'）'));
     state(d.state);
   }).catch(function(e){ add('her','连不上了：'+e); })
   .then(function(){ b.disabled=false; q.focus(); });
});
</script></body></html>"""
