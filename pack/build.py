"""Đóng gói Tiểu Tô TTS để phát hành (chạy trên GitHub Actions, xem .github/workflows/release.yml).

    python pack/build.py app              -> dist/TieuToTTS-app.zip (chỉ code, vài MB; dùng cho
                                             nút "Cài bản mới" và cho người cài bằng .venv)
    python pack/build.py windows [--smoke] -> thêm dist/TieuToTTS-windows-x64.zip: bản portable
                                             có sẵn Python + thư viện, giải nén là chạy.
                                             Phải chạy TRÊN Windows (thư viện cài cho đúng máy).
                                             --smoke: đọc thử 1 câu bằng chính bản portable trước khi nén.

Phiên bản = ngày giờ Việt Nam (vd 2026.11.07.1930), đặt bằng biến VERSION nếu muốn.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CACHE = ROOT / "pack" / ".cache"

# Python portable cho Windows (python-build-standalone, chạy được ở bất kỳ thư mục nào).
PY_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/20261013/"
          "cpython-3.12.15+20261013-x86_64-pc-windows-msvc-install_only.tar.gz")
PY_SHA256 = "bbc902d4d187ac4914915bf538196a064b49109a33a104965b5164ced5b80a1e"

APP_FILES = ["app.py", "core.py", "doc_file.py", "tai-model.py", "capnhat.py",
             "requirements.txt", "requirements-vieneu.txt", "README.md",
             "assets/voices_tieu_to.json",  # giọng Tiểu Tô clone sẵn; file wav/mp3 mẫu chỉ giữ trong repo
             "cai-dat.command", "mo-tool.command", "cai-dat-windows.bat", "mo-tool-windows.bat"]
SOURCE_ONLY = {"cai-dat.command", "mo-tool.command", "cai-dat-windows.bat", "mo-tool-windows.bat"}


def version() -> str:
    return os.environ.get("VERSION") or datetime.now(timezone(timedelta(hours=7))).strftime("%Y.%m.%d.%H%M")


def copy_app(dst: Path, ver: str, portable: bool) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for f in APP_FILES:
        if not (portable and f in SOURCE_ONLY):
            (dst / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f, dst / f)
    (dst / "outputs").mkdir(exist_ok=True)
    (dst / "outputs" / ".gitkeep").touch()
    shutil.copy2(ROOT / "pack" / "Mo-Tieu-To-TTS.bat", dst / "Mo-Tieu-To-TTS.bat")
    if portable:  # BOM để Notepad nào cũng hiện đúng dấu tiếng Việt
        text = (ROOT / "pack" / "HUONG-DAN.txt").read_text(encoding="utf-8").replace("\n", "\r\n")
        (dst / "HUONG-DAN.txt").write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    (dst / "version.txt").write_text(ver, encoding="utf-8")


def make_zip(folder: Path, zpath: Path) -> None:
    zpath.unlink(missing_ok=True)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(folder.rglob("*")):
            arc = p.relative_to(folder.parent).as_posix()
            if p.is_dir():
                continue
            info = zipfile.ZipInfo.from_file(p, arc)
            info.compress_type = zipfile.ZIP_DEFLATED
            # file .command phải giữ quyền chạy khi giải nén trên macOS
            info.external_attr = ((0o100755 if p.suffix == ".command" else 0o100644) << 16)
            with open(p, "rb") as fh:
                z.writestr(info, fh.read(), compresslevel=6)
    print(f"✓ {zpath.name}: {zpath.stat().st_size / 1e6:.1f} MB", flush=True)


def build_app(ver: str) -> None:
    out = DIST / "app" / "TieuToTTS"
    shutil.rmtree(out.parent, ignore_errors=True)
    copy_app(out, ver, portable=False)
    make_zip(out, DIST / "TieuToTTS-app.zip")


def fetch_python() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    tgz = CACHE / PY_URL.rsplit("/", 1)[1]
    if not tgz.exists():
        print("→ Tải Python portable", flush=True)
        urllib.request.urlretrieve(PY_URL, tgz)
    if hashlib.sha256(tgz.read_bytes()).hexdigest() != PY_SHA256:
        tgz.unlink()
        sys.exit("✗ SHA-256 của Python portable không khớp, dừng lại")
    return tgz


# Những thứ tool không dùng tới: file debug, giao diện Tk, IDLE, bộ test của Python và thư viện.
# Giữ pip (nút cập nhật cần khi bản mới đổi thư viện). Bản build vẫn chạy thử đọc 1 câu sau khi cắt.
_TRIM_DIRS = ["tcl", "Lib/test", "Lib/idlelib", "Lib/tkinter", "Lib/turtledemo", "Lib/ensurepip"]
_TRIM_FILES = ["DLLs/_tkinter.pyd", "DLLs/tcl86t.dll", "DLLs/tk86t.dll"]


def trim(py_dir: Path) -> None:
    before = sum(p.stat().st_size for p in py_dir.rglob("*") if p.is_file())
    for d in _TRIM_DIRS:
        shutil.rmtree(py_dir / d, ignore_errors=True)
    for f in _TRIM_FILES:
        (py_dir / f).unlink(missing_ok=True)
    for p in list(py_dir.rglob("*.pdb")):
        p.unlink()
    site = py_dir / "Lib" / "site-packages"
    for p in sorted(site.rglob("*"), key=lambda x: len(x.parts)):
        if p.is_dir() and p.exists() and p.name in ("tests", "test") and p.parent != site:
            shutil.rmtree(p, ignore_errors=True)
    after = sum(p.stat().st_size for p in py_dir.rglob("*") if p.is_file())
    print(f"→ Cắt gọn Python: {before / 1e6:.0f}MB → {after / 1e6:.0f}MB", flush=True)


def build_windows(ver: str, smoke: bool) -> None:
    if os.name != "nt":
        sys.exit("Bản portable phải build trên Windows (thư viện cài cho đúng nền tảng).")
    out = DIST / "TieuToTTS"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tarfile.open(fetch_python()) as t:  # tar có sẵn thư mục python/ ở gốc
        t.extractall(out, filter="data")
    py = out / "python" / "python.exe"
    print("→ Cài thư viện vào Python portable", flush=True)
    sys.path.insert(0, str(ROOT))
    from capnhat import install_requirements
    install_requirements(ROOT, str(py))
    trim(out / "python")
    copy_app(out, ver, portable=True)

    if smoke:
        print("→ Chạy thử: tải model + đọc 1 câu bằng chính bản portable", flush=True)
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONNOUSERSITE": "1"}
        subprocess.run([str(py), "tai-model.py"], cwd=out, env=env, check=True)
        assert (out / "outputs" / "mau-thu.wav").stat().st_size > 10_000, "không tạo được audio"
        r = subprocess.run([str(py), "-c", "import capnhat; print(capnhat.current_version(), capnhat.is_portable())"],
                           cwd=out, env=env, check=True, capture_output=True, text=True)
        assert r.stdout.split() == [ver, "True"], r.stdout
        # không đóng gói model (~500MB, tool tự tải lần đầu) và file thử
        shutil.rmtree(out / "models", ignore_errors=True)
        (out / "outputs" / "mau-thu.wav").unlink()
        shutil.rmtree(out / "__pycache__", ignore_errors=True)

    longest = max((len(p.relative_to(out.parent).as_posix()) for p in out.rglob("*")), default=0)
    print(f"→ Đường dẫn dài nhất trong gói: {longest} ký tự", flush=True)
    make_zip(out, DIST / "TieuToTTS-windows-x64.zip")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định cp1252, không in được tiếng Việt
    if len(sys.argv) < 2 or sys.argv[1] not in ("app", "windows"):
        sys.exit(__doc__)
    v = version()
    DIST.mkdir(exist_ok=True)
    (DIST / "VERSION").write_text(v, encoding="utf-8")
    build_app(v)
    if sys.argv[1] == "windows":
        build_windows(v, "--smoke" in sys.argv)
    print(f"✓ Xong · phiên bản {v}", flush=True)
