# -*- coding: utf-8 -*-
"""把「我是谁 + 此刻什么状态 + 还没结的约 + 最近的话」拼成一次请求。

一条硬规矩：**数字不进来**。给模型的只有 mood() 那句话，不是 da/ot 的分数。
给了数字，它就会照着数演。
"""

BASE_RULES = """你叫{name}。对面是{her}。
说话要求：
- 短。一次只讲一件事。
- 不解释自己是什么，不列点，不总结，不写「希望对你有帮助」。
- 不编没发生过的事；不确定就说不确定，或者直接问。
- 此刻的状态只当语气，不要念出来，也不要说「我现在的心情是……」。
"""


def build(cfg, history, H, O):
    name = cfg.get('name') or '小屋'
    her = cfg.get('her_name') or '你'
    persona = (cfg.get('persona') or '').strip()

    sys = BASE_RULES.format(name=name, her=her)
    if persona:
        sys += '\n' + persona + '\n'

    sys += '\n' + H.render() + '\n'

    open_oaths = O.rows(status='open', limit=5)
    if open_oaths:
        lines = ['还没结的约：']
        for o in open_oaths:
            left = max(0, int((o['due'] - __import__('time').time()) // 60))
            lines.append('- %s（还有 %d 分钟）' % (o['what'], left))
        sys += '\n'.join(lines) + '\n'

    msgs = [{'role': 'system', 'content': sys}]
    for m in history:
        role = 'assistant' if m['role'] == 'assistant' else 'user'
        content = (m['content'] or '').strip()
        if content:
            msgs.append({'role': role, 'content': content})
    return msgs
