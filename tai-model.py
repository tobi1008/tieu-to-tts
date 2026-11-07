"""Chạy 1 lần sau khi cài: tải model + nạp giọng Tiểu Tô + đọc thử 1 câu
để đo tốc độ thật trên máy của bạn. Kết quả lưu ở outputs/mau-thu.wav"""
import time
from pathlib import Path

from core import BASE, TEN_GIONG, get_tts

CAU_THU = ("Xin chào, mình là Tiểu Tô đây. Đây là câu đọc thử để kiểm tra "
           "giọng clone và đo tốc độ tạo audio trên máy của bạn.")

if __name__ == "__main__":
    tts, load_s = get_tts()
    print(f"Load model + nạp giọng {TEN_GIONG}: {load_s:.1f} giây", flush=True)
    t1 = time.time()
    audio = tts.infer(CAU_THU, voice=TEN_GIONG)
    elapsed = time.time() - t1
    out = BASE / "outputs" / "mau-thu.wav"
    out.parent.mkdir(exist_ok=True)
    tts.save(audio, str(out))
    dur = len(audio) / 48000
    print(f"Đọc thử: audio {dur:.1f} giây | tạo mất {elapsed:.1f} giây | "
          f"hệ số RTF {elapsed / dur:.2f} (nhỏ hơn 1 = nhanh hơn thời gian thực)", flush=True)
    print(f"Đã lưu: {out}", flush=True)
    print("Máy của bạn tạo 30 phút audio sẽ mất khoảng "
          f"{30 * elapsed / dur:.0f} phút ở chế độ này.", flush=True)
