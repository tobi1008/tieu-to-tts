#!/bin/bash
# Tiểu Tô TTS - script cài đặt cho macOS (nhấp đúp để chạy)
cd "$(dirname "$0")" || exit 1
echo "=== Cài đặt Tiểu Tô TTS ==="

PY=""
for cand in python3.12 python3.11 python3.10 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    ok=$("$cand" -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)' 2>/dev/null)
    if [ "$ok" = "1" ]; then PY="$cand"; break; fi
  fi
done

if [ -z "$PY" ]; then
  echo ""
  echo "KHÔNG tìm thấy Python 3.10 trở lên trên máy."
  echo "Hãy cài Python tại https://www.python.org/downloads/macos/ (chọn bản 3.12),"
  echo "hoặc nếu có Homebrew: brew install python@3.12"
  echo "Cài xong chạy lại file này."
  open "https://www.python.org/downloads/macos/"
  read -r -p "Nhấn Enter để đóng..."
  exit 1
fi

echo "Dùng Python: $PY ($($PY --version))"
"$PY" -m venv .venv || { echo "Tạo môi trường ảo thất bại."; read -r -p "Nhấn Enter để đóng..."; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install vieneu || { echo "Cài vieneu thất bại - kiểm tra mạng rồi chạy lại."; read -r -p "Nhấn Enter để đóng..."; exit 1; }

echo ""
echo "=== Tải model + kiểm tra giọng Tiểu Tô (lần đầu mất vài phút) ==="
python tai-model.py

echo ""
echo "=== CÀI XONG ==="
echo "Từ giờ chỉ cần nhấp đúp file 'mo-tool.command' để mở tool đọc text."
read -r -p "Nhấn Enter để đóng..."
