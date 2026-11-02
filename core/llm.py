# -*- coding: utf-8 -*-
"""模型调用：任何 OpenAI 兼容接口都行（DeepSeek / 本地 vLLM / Ollama 的 /v1）。

只用标准库。出错时把真话带回来，别假装回了一句。
"""
import json
import urllib.error
import urllib.request


def chat(cfg, messages, timeout=90):
    base = (cfg.get('base_url') or '').rstrip('/')
    key = cfg.get('api_key') or ''
    model = cfg.get('model') or ''
    if not base or not model:
        raise RuntimeError('config.json 里 base_url / model 没填')
    body = json.dumps({
        'model': model,
        'messages': messages,
        'temperature': float(cfg.get('temperature', 0.7)),
        'max_tokens': int(cfg.get('max_tokens', 800)),
    }).encode('utf-8')
    req = urllib.request.Request(base + '/chat/completions', data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer ' + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode('utf-8', 'ignore'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'ignore')[:300]
        raise RuntimeError('接口 %s：%s' % (e.code, detail))
    except urllib.error.URLError as e:
        raise RuntimeError('连不上 %s：%s' % (base, e.reason))

    try:
        return (d['choices'][0]['message']['content'] or '').strip()
    except Exception:
        raise RuntimeError('返回里没有 choices：' + json.dumps(d, ensure_ascii=False)[:200])
