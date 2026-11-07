"""Giao diện web local cho tool Tiểu Tô TTS.
Chạy:  python app.py   ->  mở http://127.0.0.1:7860 trên trình duyệt.
Nhập text, bấm Đọc, nghe/tải file wav. Text dài (kịch bản 30-60 phút)
nên dùng doc_file.py để có tính năng đọc tiếp khi bị ngắt giữa chừng.
"""
import os
import threading
import time
from datetime import datetime
from pathlib import Path

# Một số máy có biến môi trường no_proxy chứa địa chỉ IPv6 trong ngoặc vuông
# khiến thư viện web (httpx/gradio) lỗi ngay khi khởi động. Chuẩn hoá lại cho chắc.
for _k in ("no_proxy", "NO_PROXY"):
    if _k in os.environ:
        os.environ[_k] = "localhost,127.0.0.1"

import gradio as gr

import capnhat
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


PHIEN_BAN = capnhat.current_version()


def kiem_tra(tu_dong: bool = False):
    """Trả về (thông báo, hiện nút Cài?, thông tin bản mới)."""
    try:
        info = capnhat.check()
    except Exception as e:  # mất mạng, GitHub chặn tạm... không làm phiền khi tự kiểm tra
        msg = "" if tu_dong else f"Không kiểm tra được cập nhật: {e}"
        return msg, gr.update(visible=False), None
    if not capnhat.is_newer(info["version"], PHIEN_BAN):
        return ("" if tu_dong else f"Bạn đang dùng bản mới nhất ({PHIEN_BAN})."), gr.update(visible=False), None
    notes = f"\n\n**Có gì mới:**\n{info['notes']}" if info["notes"] else ""
    if PHIEN_BAN == "dev":
        return (f"Bản mới nhất trên GitHub: **{info['version']}**. Bạn đang chạy từ mã nguồn (git) "
                f"nên cập nhật bằng lệnh `git pull`.{notes}"), gr.update(visible=False), None
    return (f"🎉 Có bản mới **{info['version']}** (bạn đang dùng {PHIEN_BAN}).{notes}\n\n"
            "Bấm **Cài bản mới** — model và các file audio đã tạo được giữ nguyên, "
            "tool tự khởi động lại sau khi cài."), gr.update(visible=True), info


def cai_dat(info):
    if not info:
        return "Bấm **Kiểm tra cập nhật** trước.", gr.update(visible=False)
    try:
        ver = capnhat.install(info)
    except Exception as e:
        return f"❌ Cập nhật thất bại: {e}", gr.update(visible=True)
    print(f"Đã cập nhật lên bản {ver}, đang khởi động lại...", flush=True)
    threading.Timer(1.5, lambda: os._exit(capnhat.RESTART_CODE)).start()
    return (f"✅ Đã cài bản **{ver}**. Tool đang khởi động lại — đợi khoảng 30 giây "
            "rồi bấm **F5** để tải lại trang."), gr.update(visible=False)


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
    with gr.Accordion(f"Cập nhật · phiên bản {PHIEN_BAN}", open=False):
        upd_msg = gr.Markdown()
        with gr.Row():
            btn_check = gr.Button("Kiểm tra cập nhật")
            btn_install = gr.Button("Cài bản mới", variant="primary", visible=False)
        upd_info = gr.State(None)
    btn_check.click(lambda: ("Đang kiểm tra...", gr.update(), None),
                    outputs=[upd_msg, btn_install, upd_info]).then(
        kiem_tra, outputs=[upd_msg, btn_install, upd_info])
    btn_install.click(lambda: ("Đang tải và cài bản mới, đừng đóng tool...", gr.update(visible=False)),
                      outputs=[upd_msg, btn_install]).then(
        cai_dat, inputs=[upd_info], outputs=[upd_msg, btn_install])
    if PHIEN_BAN != "dev":  # bản phát hành: mở trang là tự xem có bản mới không
        demo.load(lambda: kiem_tra(True), outputs=[upd_msg, btn_install, upd_info])

if __name__ == "__main__":
    # Khởi động lại sau khi cập nhật thì không mở thêm tab trình duyệt mới
    demo.launch(server_name="127.0.0.1", server_port=7860,
                inbrowser=not os.environ.get("TIEUTO_RESTART"))
