# companion

给长期陪着的 AI，一个**能装在手机上**的最小骨架。

一个人格、会记事、会记约、有四个慢变量。数据全在手机里一个 SQLite 文件，不上云、不要服务器。
**只用 Python 标准库**，不装任何依赖。

---

## 三步装好（Termux，不需要 root）

```bash
# 1. 装 Termux（F-Droid 版），打开后：
pkg install -y git python
git clone <这个仓库>
cd companion

# 2. 配置
cp config.json.example config.json
nano config.json        # 只改 api_key（base_url/model 默认 DeepSeek）

# 3. 起服务
python server.py
```

手机浏览器打开 `http://127.0.0.1:8388` —— 就是它。

想要开机自启：Termux 里装 `Termux:Boot`，把 `python server.py` 写进 `~/.termux/boot/`。

---

## 它是什么

| 东西 | 一句话 |
|---|---|
| `core/hormone.py` | 四个慢变量（想要/贴/紧/松）。记了什么就往哪边动，不记就退回基线 |
| `core/oath.py` | 立约账。删不掉、改不了、过期判负 —— 锁在数据库触发器里 |
| `core/store.py` | 一张消息表，就是"记忆"的最小形态 |
| `core/prompt.py` | 把「我是谁 + 此刻状态 + 没结的约 + 最近的话」拼成请求 |
| `core/llm.py` | 任何 OpenAI 兼容接口（DeepSeek / 本地 vLLM / Ollama 的 /v1） |

界面两个页：`/` 首页（此刻状态 / 今天说了几句 / 没结的约），`/chat` 聊天页。

皮肤用 **Pico.css**（classless），本地放了一份 `static/pico.min.css`，不联网也能跑；强调色改成了墨绿。自己从零调一套排版又慢又容易土，这个直接够用。

---

## 三条硬规矩（写在代码里，不是写在口号里）

1. **数字不进提示词。** 模型拿到的是「此刻：贴。想靠近一点」，不是 `ot=77`。给了数字，它就会照着数演。
2. **不可逆的东西要真不可逆。** 约的删除/改字/反悔都由 SQLite 触发器拦住，`DELETE FROM oath` 直接报错。
3. **读不到就说读不到。** 接口失败时把错误原样带回来，不假装回了一句。

---

## 手机上的边界

- 默认只监听 `127.0.0.1`：**只有这台手机能开**。
- `--host 0.0.0.0` 会给同一 WiFi 的别人看；没有密码，别在公共网络上开。
- 数据在 `data.db`，删了就是清零。备份就是复制这个文件。
- 手机杀后台会让服务停；Termux 里 `termux-wake-lock` 能撑一段。

---

## 不加什么（故意的）

- 不做账号、不做多用户、不做云同步。
- 不做向量记忆、不做工具调用、不做插件市场。
- 这些东西各有各的坑，混进来会看不清上面那三样。

先让它能跑、能记住、能算数；别的以后一件一件加。

---

MIT.
