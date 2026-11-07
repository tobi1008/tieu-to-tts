"""Giao diện web local cho tool Tiểu Tô TTS.
Chạy:  python app.py   ->  mở http://127.0.0.1:7860 trên trình duyệt.
Nhập text, bấm Đọc, nghe/tải file wav. Text dài (kịch bản 30-60 phút)
nên dùng doc_file.py để có tính năng đọc tiếp khi bị ngắt giữa chừng.
"""
import os
import time
from datetime import datetime
from pathlib import Path

# Một số máy có biến môi trường no_proxy chứa địa chỉ IPv6 trong ngoặc vuông
# khiến thư viện web (httpx/gradio) lỗi ngay khi khởi động. Chuẩn hoá lại cho chắc.
for _k in ("no_proxy", "NO_PROXY"):
    if _k in os.environ:
        os.environ[_k] = "localhost,127.0.0.1"

import gradio as gr

from core import BASE, TEN_GIONG, get_tts

print("Đang load model (lần đầu có thể mất vài phút để tải model)...", flush=True)
tts, load_s = get_tts()
print(f"Đã sẵn sàng sau {load_s:.1f} giây. Giọng mặc định: {TEN_GIONG}", flush=True)

_preset_names = []
for item in tts.list_preset_voices():
    try:
        _preset_names.append(item[1])
    except Exception:
        _preset_names.append(str(item))
_choices = [TEN_GIONG] + [n for n in _preset_names if n != TEN_GIONG]

OUT_DIR = BASE / "outputs"
OUT_DIR.mkdir(exist_ok=True)


def doc(text: str, voice: str):
    text = (text or "").strip()
    if not text:
        return None, "Chưa nhập text."
    t1 = time.time()
    audio = tts.infer(text, voice=voice or TEN_GIONG)
    elapsed = time.time() - t1
    name = f"doc_{datetime.now():%Y%m%d_%H%M%S}.wav"
    path = OUT_DIR / name
    tts.save(audio, str(path))
    dur = len(audio) / 48000
    return str(path), (f"Xong: audio {dur:.1f} giây, tạo mất {elapsed:.1f} giây "
                       f"(RTF {elapsed / dur:.2f}). File: outputs/{name}")


with gr.Blocks(title="Tiểu Tô TTS - đọc text bằng giọng clone") as demo:
    gr.Markdown("# Tiểu Tô TTS\nNhập text tiếng Việt, nghe giọng Tiểu Tô đọc. "
                "Mọi thứ chạy ngay trên máy của bạn, không gửi đi đâu cả.")
    with gr.Row():
        voice = gr.Dropdown(choices=_choices, value=TEN_GIONG, label="Giọng đọc")
    text = gr.Textbox(lines=8, label="Text cần đọc",
                      placeholder="Dán đoạn text vào đây...")
    btn = gr.Button("Đọc", variant="primary")
    audio_out = gr.Audio(label="Kết quả", type="filepath")
    status = gr.Textbox(label="Trạng thái", interactive=False)
    btn.click(doc, inputs=[text, voice], outputs=[audio_out, status])
    gr.Markdown("Mẹo: kịch bản dài 30-60 phút thì mở Terminal trong thư mục này và chạy "
                "`python doc_file.py kich-ban.txt` — tool sẽ đọc từng đoạn, lưu lại từng đoạn "
                "nên bị tắt giữa chừng cũng đọc tiếp được, cuối cùng tự ghép thành 1 file.")

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
