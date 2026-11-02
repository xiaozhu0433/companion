#!/data/data/com.termux/files/usr/bin/bash
# companion 在 Termux 里的一键安装（不需要 root）
set -e

echo "== 1/4 装 Python =="
pkg install -y python >/dev/null

echo "== 2/4 建目录 =="
mkdir -p ~/companion
cd ~/companion

echo "== 3/4 配置 =="
if [ ! -f config.json ]; then
  cp config.json.example config.json
  echo "  已生成 config.json —— 现在去填 api_key（别的可以不动）"
  echo "  改完再跑一次这个脚本，或者直接 python server.py"
  exit 0
fi

echo "== 4/4 起服务 =="
echo "  地址：http://127.0.0.1:8388"
echo "  （手机浏览器打开；想给同一 WiFi 的其他设备看，用 --host 0.0.0.0，但要知道别人也能开）"
python server.py
