"""Core dùng chung cho tool Tiểu Tô TTS (VieNeu-TTS v3 Turbo, chạy local/offline).

Việc quan trọng nhất ở đây: tải model về dạng FILE THẬT trong thư mục models/
của tool. Nếu để HuggingFace cache mặc định (symlink), ONNX Runtime sẽ lỗi
"External data path escapes model directory" khi load model có file .data rời.
"""
import shutil
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
MODELS = BASE / "models"
BACKBONE_DIR = MODELS / "backbone"
CODEC_DIR = MODELS / "codec"
REF_TIEU_TO = BASE / "assets" / "ref-tieu-to.wav"
TEN_GIONG = "Tiểu Tô"

_V3_REPO = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
_CODEC_REPO = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
_GRAPH_FILES = [
    "vieneu_prefill.onnx", "vieneu_decode_step.onnx",
    "vieneu_acoustic_cached.onnx", "vieneu_backbone_shared.data",
    "vieneu_v3_heads.npz", "config.json", "tokenizer.json",
]
_CODEC_FILES = [
    "moss_audio_tokenizer_decode_full.onnx", "moss_audio_tokenizer_decode_shared.data",
    "moss_audio_tokenizer_decode_step.onnx", "codec_browser_onnx_meta.json",
    "moss_audio_tokenizer_encode.onnx", "moss_audio_tokenizer_encode.data",
]


def _copy_real(src: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.stat().st_size == 0:
        shutil.copyfile(src, dst)  # copyfile đi theo symlink -> ra file thật


def ensure_models() -> None:
    """Tải model (lần đầu cần internet, ~550MB) về models/ dạng file thật."""
    from huggingface_hub import hf_hub_download

    missing = [f for f in _GRAPH_FILES if not (BACKBONE_DIR / f).exists()]
    if missing:
        print("Đang tải model VieNeu v3 Turbo (lần đầu, khoảng 450MB)...", flush=True)
        for fn in _GRAPH_FILES:
            p = hf_hub_download(_V3_REPO, fn, repo_type="model", subfolder="onnx_update")
            _copy_real(p, BACKBONE_DIR / fn)
    missing = [f for f in _CODEC_FILES if not (CODEC_DIR / f).exists()]
    if missing:
        print("Đang tải bộ giải mã âm thanh MOSS (khoảng 90MB)...", flush=True)
        for fn in _CODEC_FILES:
            p = hf_hub_download(_CODEC_REPO, fn, repo_type="model")
            _copy_real(p, CODEC_DIR / fn)
    print("Model đã sẵn sàng.", flush=True)


def _patch_codec_fetch() -> None:
    from vieneu._v3_turbo_engine.onnx_runtime_lite import OnnxV3LiteEngine

    orig = OnnxV3LiteEngine._fetch

    def patched(repo, files, subfolder=None):
        if "MOSS" in str(repo):
            return CODEC_DIR
        return orig(repo, files, subfolder)

    OnnxV3LiteEngine._fetch = staticmethod(patched)


def get_tts(precision: str = "fp32"):
    """Load VieNeu (CPU/ONNX) và đăng ký sẵn giọng Tiểu Tô. Trả về (tts, giây_load)."""
    ensure_models()
    _patch_codec_fetch()
    from vieneu import Vieneu

    t0 = time.time()
    tts = Vieneu(precision=precision, onnx_dir=str(BACKBONE_DIR))
    if TEN_GIONG not in str(tts.list_preset_voices()):
        tts.add_voice(TEN_GIONG, str(REF_TIEU_TO), denoise=True,
                      description="Giọng clone Tiểu Tô (đăng ký tự động từ file mẫu)")
    return tts, time.time() - t0
