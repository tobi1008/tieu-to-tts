"""Core dùng chung cho tool Tiểu Tô TTS (VieNeu-TTS v3 Turbo, chạy local/offline).

Tool chỉ đọc bằng giọng Tiểu Tô, nạp từ giọng đã clone sẵn trong
assets/voices_tieu_to.json (dấu vân giọng + mã âm thanh mẫu). Nhờ vậy không
phải clone lại từ file wav mỗi lần mở, nên KHÔNG cần librosa/scipy/numba,
không cần tải 3 model chỉ dùng để clone (bộ khử ồn, bộ nhận dạng giọng, bộ mã
hoá âm thanh ~116MB) và mở tool nhanh hơn. Kết quả đọc y hệt cách clone cũ
(đã so: dấu vân giọng và mã âm thanh trùng 100%).

Model được tải thẳng về models/ dạng FILE THẬT (không qua cache HuggingFace):
không tốn gấp đôi ổ cứng, và ONNX Runtime không lỗi "External data path escapes
model directory" như khi load từ symlink trong cache.
"""
import json
import os
import shutil
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
MODELS = BASE / "models"
BACKBONE_DIR = MODELS / "backbone"
CODEC_DIR = MODELS / "codec"
VOICE_FILE = BASE / "assets" / "voices_tieu_to.json"
TEN_GIONG = "Tiểu Tô"

_V3_REPO = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
_CODEC_REPO = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
_GRAPH_FILES = [
    "vieneu_prefill.onnx", "vieneu_decode_step.onnx",
    "vieneu_acoustic_cached.onnx", "vieneu_backbone_shared.data",
    "vieneu_v3_heads.npz", "config.json", "tokenizer.json",
]
# Chỉ phần giải mã (đọc). Phần mã hoá chỉ dùng để clone giọng mới nên không tải.
_CODEC_FILES = [
    "moss_audio_tokenizer_decode_full.onnx", "moss_audio_tokenizer_decode_shared.data",
    "moss_audio_tokenizer_decode_step.onnx", "codec_browser_onnx_meta.json",
]


def _download(repo: str, files: list, subfolder, dst: Path) -> None:
    from huggingface_hub import hf_hub_download

    tmp = MODELS / ".dang-tai"
    for fn in files:
        if (dst / fn).exists() and (dst / fn).stat().st_size > 0:
            continue
        p = hf_hub_download(repo, fn, repo_type="model", subfolder=subfolder, local_dir=tmp)
        dst.mkdir(parents=True, exist_ok=True)
        os.replace(p, dst / fn)
    shutil.rmtree(tmp, ignore_errors=True)


def ensure_models() -> None:
    """Tải model (lần đầu cần internet, ~520MB) về models/ dạng file thật."""
    if any(not (BACKBONE_DIR / f).exists() for f in _GRAPH_FILES):
        print("Đang tải model VieNeu v3 Turbo (lần đầu, khoảng 475MB)...", flush=True)
        _download(_V3_REPO, _GRAPH_FILES, "onnx_update", BACKBONE_DIR)
    if any(not (CODEC_DIR / f).exists() for f in _CODEC_FILES):
        print("Đang tải bộ giải mã âm thanh MOSS (khoảng 45MB)...", flush=True)
        _download(_CODEC_REPO, _CODEC_FILES, None, CODEC_DIR)
    print("Model đã sẵn sàng.", flush=True)


def _patch_engine() -> None:
    from vieneu._v3_turbo_engine.onnx_runtime_lite import OnnxV3LiteEngine

    orig = OnnxV3LiteEngine._fetch

    def fetch(repo, files, subfolder=None):
        if "MOSS" in str(repo):
            return CODEC_DIR
        return orig(repo, files, subfolder)

    OnnxV3LiteEngine._fetch = staticmethod(fetch)
    # Bộ khử ồn chỉ dùng khi clone giọng mới; mặc định vieneu tải nó (43MB) mỗi lần mở.
    OnnxV3LiteEngine._load_denoiser = lambda self: None


def _load_voice(tts) -> None:
    """Chỉ giữ giọng Tiểu Tô, nạp từ giọng đã clone sẵn."""
    import numpy as np
    from vieneu_utils.core_utils import strip_encoder_pad_frame

    v = json.loads(VOICE_FILE.read_text(encoding="utf-8"))["presets"][TEN_GIONG]
    tts._preset_voices = {TEN_GIONG: {
        "description": v.get("description", ""),
        "gender": v.get("gender", ""),
        "style": v.get("style", "tu_nhien"),
        "featured": None,
        "aliases": [],
        "speaker_emb": np.asarray(v["speaker_emb"], dtype=np.float32),
        "codes": strip_encoder_pad_frame(np.asarray(v["codes"], dtype=np.int64)),
    }}
    tts._voice_aliases = {}
    tts._default_voice = TEN_GIONG


def get_tts(precision: str = "fp32"):
    """Load VieNeu (CPU/ONNX) với giọng Tiểu Tô. Trả về (tts, giây_load)."""
    ensure_models()
    _patch_engine()
    from vieneu import Vieneu

    t0 = time.time()
    # backbone_repo trỏ vào thư mục local: vieneu khỏi gọi mạng lên HuggingFace mỗi lần mở
    tts = Vieneu(precision=precision, onnx_dir=str(BACKBONE_DIR), backbone_repo=str(MODELS))
    _load_voice(tts)
    return tts, time.time() - t0
