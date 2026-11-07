"""Đọc 1 file text dài (kịch bản 30-60 phút) thành 1 file audio.

Cách dùng:
    python doc_file.py kich-ban.txt
    python doc_file.py kich-ban.txt --output tap-01.wav

Cách hoạt động:
- Tự cắt text thành từng đoạn nhỏ theo câu/đoạn văn, đọc lần lượt.
- Mỗi đoạn đọc xong được lưu ngay vào thư mục <ten-file>_doan/ nên nếu bị
  tắt máy/ngắt giữa chừng, chạy lại lệnh cũ là tool đọc tiếp từ đoạn dở.
- Cuối cùng tự ghép tất cả thành 1 file wav (và mp3 nếu máy có ffmpeg),
  chèn khoảng lặng 0,3 giây giữa các đoạn, 0,7 giây khi hết 1 đoạn văn.
"""
import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from core import TEN_GIONG, get_tts

SR = 48000
MAX_CHUNK = 700  # ký tự tối đa mỗi đoạn đọc


def split_chunks(text: str):
    """Trả về list (đoạn_text, kết_thúc_đoạn_văn: bool)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for para in paragraphs:
        sentences = re.split(r"(?<=[.!?…])\s+", para.replace("\n", " ").strip())
        buf = ""
        for i, s in enumerate(sentences):
            s = s.strip()
            if not s:
                continue
            last = i == len(sentences) - 1
            if len(buf) + len(s) + 1 <= MAX_CHUNK:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    chunks.append((buf, False))
                buf = s
            if last and buf:
                chunks.append((buf, True))
                buf = ""
        if buf:
            chunks.append((buf, True))
    return chunks


def main():
    ap = argparse.ArgumentParser(description="Đọc file text dài bằng giọng Tiểu Tô")
    ap.add_argument("input", help="File .txt chứa kịch bản (UTF-8)")
    ap.add_argument("--output", default=None, help="File wav kết quả (mặc định: <ten-input>.wav)")
    ap.add_argument("--nghi-cau", type=float, default=0.3, help="Giây lặng giữa các đoạn")
    ap.add_argument("--nghi-doan", type=float, default=0.7, help="Giây lặng khi hết đoạn văn")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"Không thấy file: {src}")
    text = src.read_text(encoding="utf-8")
    out_path = Path(args.output) if args.output else src.with_suffix(".wav")
    work = src.parent / (src.stem + "_doan")
    work.mkdir(exist_ok=True)

    chunks = split_chunks(text)
    print(f"Tổng {len(text)} ký tự, cắt thành {len(chunks)} đoạn.", flush=True)

    tts, load_s = get_tts()
    print(f"Load model: {load_s:.1f} giây. Bắt đầu đọc bằng giọng '{TEN_GIONG}'...", flush=True)

    total_audio = 0.0
    total_time = 0.0
    read_count = 0
    for idx, (chunk_text, _) in enumerate(chunks):
        part = work / f"doan_{idx:04d}.wav"
        if part.exists() and part.stat().st_size > 1000:
            d = sf.info(str(part)).duration
            total_audio += d
            print(f"[{idx + 1}/{len(chunks)}] đã có, bỏ qua ({d:.1f}s audio)", flush=True)
            continue
        t1 = time.time()
        audio = tts.infer(chunk_text, voice=TEN_GIONG)
        elapsed = time.time() - t1
        tts.save(audio, str(part))
        dur = len(audio) / SR
        total_audio += dur
        total_time += elapsed
        read_count += 1
        done = idx + 1
        eta = (len(chunks) - done) * (total_time / max(read_count, 1))
        print(f"[{done}/{len(chunks)}] audio {dur:.1f}s | đọc mất {elapsed:.1f}s | "
              f"ước tính còn ~{eta / 60:.1f} phút", flush=True)

    print("Đang ghép các đoạn thành 1 file...", flush=True)
    pieces = []
    for idx, (_, end_para) in enumerate(chunks):
        data, sr = sf.read(str(work / f"doan_{idx:04d}.wav"), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        pieces.append(data)
        gap = args.nghi_doan if end_para else args.nghi_cau
        pieces.append(np.zeros(int(gap * SR), dtype=np.float32))
    full = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
    sf.write(str(out_path), full, SR)
    print(f"XONG: {out_path} — tổng {len(full) / SR / 60:.1f} phút audio", flush=True)

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        mp3 = out_path.with_suffix(".mp3")
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(out_path),
                        "-b:a", "128k", str(mp3)], check=False)
        if mp3.exists():
            print(f"Bản mp3: {mp3}", flush=True)


if __name__ == "__main__":
    main()
