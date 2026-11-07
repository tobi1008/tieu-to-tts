"""Kiểm tra và cài bản mới của tool từ GitHub Releases.

Mỗi lần push code lên nhánh main, GitHub Actions (.github/workflows/release.yml) tự
đóng gói và phát hành 1 bản mới, kèm file TieuToTTS-app.zip chỉ chứa code (vài MB).
Nút "Kiểm tra cập nhật" so phiên bản trong version.txt với bản mới nhất; bấm "Cài bản
mới" thì tool tải gói code đó, chép đè lên thư mục hiện tại (model, audio đã tạo,
Python/thư viện đều giữ nguyên) rồi tự khởi động lại.

Bản chạy thẳng từ git (không có version.txt) là bản "dev": vẫn xem được có bản mới,
nhưng cập nhật bằng `git pull` chứ không tự cài.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
UPDATE_REPO = os.environ.get("UPDATE_REPO", "tobi1008/tieu-to-tts")
APP_ASSET = "TieuToTTS-app.zip"
RESTART_CODE = 3  # các file mở tool thấy mã thoát này thì chạy lại app.py

# Bản Windows portable có thư mục python/ riêng và mở bằng Mo-Tieu-To-TTS.bat:
# không chép các script cài đặt dành cho bản cài bằng .venv vào đó cho khỏi rối.
_SOURCE_ONLY = {"cai-dat.command", "mo-tool.command", "cai-dat-windows.bat", "mo-tool-windows.bat"}
_UA = {"User-Agent": "tieu-to-tts-updater", "Accept": "application/vnd.github+json"}


REQ_FILES = ("requirements.txt", "requirements-vieneu.txt")


def _read(p: Path) -> bytes:
    return p.read_bytes() if p.exists() else b""


def install_requirements(folder: Path, python: str) -> None:
    """Cài thư viện: requirements.txt bình thường, vieneu thì --no-deps (khỏi kéo librosa...)."""
    base = [python, "-m", "pip", "install", "--disable-pip-version-check", "--no-warn-script-location"]
    for args in (["-r", str(folder / "requirements.txt")],
                 ["--no-deps", "-r", str(folder / "requirements-vieneu.txt")]):
        r = subprocess.run(base + args, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("cài thư viện thất bại:\n" + (r.stderr or r.stdout)[-1500:])


def current_version() -> str:
    try:
        return (BASE / "version.txt").read_text(encoding="utf-8").strip() or "dev"
    except OSError:
        return "dev"


def is_portable() -> bool:
    return (BASE / "python" / "python.exe").exists()


def _key(v: str):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def is_newer(latest: str, current: str) -> bool:
    return current == "dev" or _key(latest) > _key(current)


def check() -> dict:
    """Hỏi GitHub bản mới nhất. Trả về dict: version, url, sha256, notes, page."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest", headers=_UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        rel = json.load(r)
    asset = next((a for a in rel.get("assets", []) if a.get("name") == APP_ASSET), None)
    if not asset:
        raise RuntimeError(f"bản phát hành {rel.get('tag_name')} không có file {APP_ASSET}")
    return {
        "version": str(rel["tag_name"]).lstrip("v"),
        "url": asset["browser_download_url"],
        "sha256": (asset.get("digest") or "").removeprefix("sha256:"),
        "notes": str(rel.get("body") or "").strip()[:2000],
        "page": rel.get("html_url", f"https://github.com/{UPDATE_REPO}/releases/latest"),
    }


def _find_root(folder: Path) -> Path:
    for p in [folder, *folder.iterdir()]:
        if p.is_dir() and (p / "version.txt").exists() and (p / "app.py").exists():
            return p
    raise RuntimeError("gói cập nhật không đúng cấu trúc")


def install(info: dict, log=print) -> str:
    """Tải + cài bản mới. Trả về phiên bản vừa cài. Lỗi thì raise, file cũ giữ nguyên."""
    if current_version() == "dev":
        raise RuntimeError("đây là bản chạy từ mã nguồn (git) — cập nhật bằng lệnh `git pull`")
    if not is_newer(info["version"], current_version()):
        raise RuntimeError("đang dùng bản mới nhất rồi")

    with tempfile.TemporaryDirectory(prefix="tieuto-update-") as tmp:
        tmp = Path(tmp)
        log(f"Đang tải bản {info['version']}...")
        req = urllib.request.Request(info["url"], headers={"User-Agent": _UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        if info.get("sha256") and hashlib.sha256(data).hexdigest() != info["sha256"]:
            raise RuntimeError("file tải về bị lỗi (SHA-256 không khớp), thử lại sau")
        zpath = tmp / "update.zip"
        zpath.write_bytes(data)
        with zipfile.ZipFile(zpath) as z:
            for name in z.namelist():  # chặn đường dẫn kiểu ../ thoát ra ngoài thư mục
                if name.startswith(("/", "\\")) or ".." in Path(name).parts:
                    raise RuntimeError("gói cập nhật chứa đường dẫn không hợp lệ")
            z.extractall(tmp / "x")
        src = _find_root(tmp / "x")

        # Bản mới cần thư viện khác (file requirements đổi) -> cài trước, lỗi thì dừng,
        # chưa đụng tới file nào của bản đang chạy.
        if any(_read(src / f) != _read(BASE / f) for f in REQ_FILES):
            log("Bản mới cần thư viện mới, đang cài (có thể mất vài phút)...")
            install_requirements(src, sys.executable)

        portable = is_portable()
        files = [p for p in src.rglob("*") if p.is_file() and p.name != "version.txt"]
        for p in files:
            rel = p.relative_to(src)
            if portable and rel.as_posix() in _SOURCE_ONLY:
                continue
            dst = BASE / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            part = dst.with_name(dst.name + ".moi")
            shutil.copyfile(p, part)
            os.replace(part, dst)
            if dst.suffix == ".command":
                dst.chmod(0o755)
        # version.txt ghi cuối cùng: cài dở chừng thì lần sau vẫn thấy có bản mới để cài lại
        shutil.copyfile(src / "version.txt", BASE / "version.txt")
    log(f"Đã cài xong bản {info['version']}.")
    return info["version"]
