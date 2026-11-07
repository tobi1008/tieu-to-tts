#!/bin/bash
# Mở giao diện Tiểu Tô TTS trên trình duyệt (macOS - nhấp đúp để chạy)
cd "$(dirname "$0")" || exit 1
if [ ! -d ".venv" ]; then
  echo "Chưa cài đặt. Hãy chạy file 'cai-dat.command' trước."
  read -r -p "Nhấn Enter để đóng..."
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "Tool sẽ mở tại http://127.0.0.1:7860 - giữ cửa sổ này mở khi đang dùng, đóng là tắt tool."
python app.py
