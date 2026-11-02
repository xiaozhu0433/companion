# -*- coding: utf-8 -*-
"""三个页面：首页 / 聊天 / 设置。皮用 Pico.css（本地一份，离线可用）。

原则（2026-11-02 她指出来的）：**界面上出现的每一样，都必须真能用**。
立约以前只在代码里，界面上没有入口，却摆在首页显示条数 —— 那是假的。现在补成真入口。
"""

THEME = """
<link rel="stylesheet" href="/static/pico.min.css">
<style>
html[data-theme=light]{
  --pico-primary:#3e5b4f;
  --pico-primary-hover:#334b41;
  --pico-primary-focus:rgba(62,91,79,.25);
  --pico-border-radius:10px;
  --pico-font-family:-apple-system,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif;
}
body{background:#f7f4ea;color:#23211c;min-height:100dvh}
.serif{font-family:'Noto Serif CJK SC','Songti SC','Source Han Serif SC',Georgia,serif}
.k{font-size:.72rem;letter-spacing:.2em;color:#7d7668;margin-bottom:.2rem}
.rule{height:1px;background:#e0d9c7;border:0;margin:1.6rem 0}
button,[role=button]{background:#3e5b4f;border-color:#3e5b4f;color:#f7f4ea}
button:hover,[role=button]:hover{background:#334b41;border-color:#334b41}
button:active,[role=button]:active{background:#2b3f36;border-color:#2b3f36}
button.secondary{background:transparent;color:#5c574d;border:1px solid #cfc7b4}
button.secondary:hover{background:#efe9d9;color:#3b372f;border-color:#c3bba6}
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
body.chat-body{height:100dvh;overflow:hidden}
main.chat{display:flex;flex-direction:column;height:100dvh;padding-bottom:0}
#log{flex:1;min-height:0;overflow-y:auto;padding:.4rem 0 1rem;
  -webkit-mask-image:linear-gradient(to bottom,transparent 0,#000 14px);
  mask-image:linear-gradient(to bottom,transparent 0,#000 14px)}
.m{max-width:84%;white-space:pre-wrap;word-break:break-word;font-size:.97rem;line-height:1.7;
  padding:.66rem .9rem;margin:0 0 .9rem;border-radius:12px}
.me{margin-left:auto;background:#efe9d9;border-radius:12px 12px 3px 12px}
.her{background:#fffdf6;border:1px solid #e0d9c7;border-radius:12px 12px 12px 3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""

NAV = """
<nav style="margin-bottom:1rem">
  <ul><li><a href="/" style="text-decoration:none">{name}</a></li></ul>
  <ul><li><a href="/chat">说话</a></li><li><a href="/settings">设置</a></li></ul>
</nav>
"""

HOME = """<!doctype html>
<html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name}</title>""" + THEME + """</head><body>
<main class="container">
""" + NAV + """
  <div id="sub" style="color:#7d7668;font-size:.85rem;letter-spacing:.1em"></div>
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
    <div class="k" style="margin-top:1.1rem">还没结的</div>
    <ul id="ol"></ul>
  </section>

  <details style="margin-top:1.2rem">
    <summary style="font-size:.92rem;color:#5c574d">立一条约</summary>
    <form id="of" style="margin-top:.8rem">
      <input id="ow" placeholder="答应的事，写清楚" aria-label="约的内容" required>
      <div style="display:grid;grid-template-columns:1fr auto;gap:.6rem;margin-top:.6rem">
        <input id="oh" type="number" min="1" max="720" value="8" aria-label="小时数">
        <button type="submit">立</button>
      </div>
      <small id="omsg" style="color:#7d7668"></small>
    </form>
  </details>

  <div style="margin-top:1.6rem">
    <a href="/chat" role="button">进去说话</a>
  </div>
</main>
<script>
function load(){
  fetch('/state').then(function(r){return r.json()}).then(function(d){
    if(!d||!d.ok) return;
    document.getElementById('mood').textContent = d.mood || '·';
    document.getElementById('line').textContent = d.line || '';
    document.getElementById('said').textContent = d.said_today == null ? '·' : d.said_today;
    document.getElementById('oaths').textContent = d.oaths == null ? '·' : d.oaths;
    document.getElementById('sub').textContent = (d.words&&d.words.length) ? d.words.join(' · ') : '';
    var ul = document.getElementById('ol'), box = document.getElementById('obox');
    ul.innerHTML = '';
    var list = d.open_oaths || [];
    box.hidden = !list.length;
    list.forEach(function(o){ var li=document.createElement('li'); li.textContent=o; ul.appendChild(li); });
  }).catch(function(){ document.getElementById('sub').textContent='连不上'; });
}
load();
document.getElementById('of').addEventListener('submit',function(e){
  e.preventDefault();
  var w=document.getElementById('ow'), h=document.getElementById('oh'), msg=document.getElementById('omsg');
  var v=w.value.trim(); if(!v) return;
  fetch('/oath',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({what:v,hours:parseFloat(h.value)||8})})
   .then(function(r){return r.json()})
   .then(function(d){
     if(d&&d.ok){ msg.textContent='立下了'; w.value=''; load(); }
     else { msg.textContent='没立上：'+((d&&d.error)||'未知原因'); }
   }).catch(function(e){ msg.textContent='连不上：'+e; });
});
</script></body></html>"""


CHAT = """<!doctype html>
<html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name}</title>""" + THEME + """</head><body class="chat-body">
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


SETTINGS = """<!doctype html>
<html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>设置</title>""" + THEME + """</head><body>
<main class="container">
""" + NAV + """
  <h3 style="margin-bottom:1rem">设置</h3>
  <form id="sf">
    <label>它叫什么
      <input id="name" autocomplete="off">
    </label>
    <label>它怎么称呼你
      <input id="her" autocomplete="off">
    </label>
    <label>它是什么样（一段人格描述）
      <textarea id="persona" rows="4"></textarea>
    </label>
    <label>接口地址（OpenAI 兼容）
      <input id="base" autocomplete="off" spellcheck="false">
    </label>
    <label>模型名
      <input id="model" autocomplete="off" spellcheck="false">
    </label>
    <label>API Key（留空 = 不改）
      <input id="key" type="password" autocomplete="off" placeholder="sk-...">
    </label>
    <p id="msg" style="color:#7d7668;font-size:.9rem"></p>
    <button type="submit">保存</button>
  </form>

  <hr class="rule">

  <h4 style="margin-bottom:.4rem">清空</h4>
  <p style="color:#7d7668;font-size:.9rem">只删聊天记录，约和激素账都留着。</p>
  <button id="reset" class="secondary">清空聊天记录</button>
</main>
<script>
function val(id){ return document.getElementById(id).value.trim(); }
fetch('/config').then(function(r){return r.json()}).then(function(c){
  document.getElementById('name').value = c.name || '';
  document.getElementById('her').value = c.her_name || '';
  document.getElementById('persona').value = c.persona || '';
  document.getElementById('base').value = c.base_url || '';
  document.getElementById('model').value = c.model || '';
  document.getElementById('key').placeholder = c.api_key_set ? '已设置（留空不改）' : 'sk-...';
});
document.getElementById('sf').addEventListener('submit',function(e){
  e.preventDefault();
  var body={name:val('name'),her_name:val('her'),persona:val('persona'),
            base_url:val('base'),model:val('model'),api_key:val('key')};
  fetch('/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
   .then(function(r){return r.json()})
   .then(function(d){ document.getElementById('msg').textContent = d.ok ? '存好了' : ('没存上：'+(d.error||'未知')); });
});
document.getElementById('reset').addEventListener('click',function(){
  if(!confirm('清空所有聊天记录？这个不能撤销。')) return;
  fetch('/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})
   .then(function(r){return r.json()})
   .then(function(d){ document.getElementById('msg').textContent = d.ok ? '清空了' : '没清成'; });
});
</script></body></html>"""
