"""
scripts/download_models.py

Downloads required AI model files that are too large for git:
  - kokoro-v1.0.onnx   (Kokoro TTS model)
  - voices-v1.0.bin    (Kokoro voice embeddings)

Silero VAD model (silero_vad.onnx) is already in the repo at
backend/voice/models/silero_vad.onnx.

Usage:
  python -m backend.scripts.download_models
"""

import os
import sys

MODELS_TO_DOWNLOAD = [
    {
        "repo_id": "hexgrad/Kokoro-82M-ONNX",
        "filename": "kokoro-v1.0.onnx",
        "local_dir": ".",
        "desc": "Kokoro TTS ONNX model (~85MB)",
    },
    {
        "repo_id": "hexgrad/Kokoro-82M-ONNX",
        "filename": "voices-v1.0.bin",
        "local_dir": ".",
        "desc": "Kokoro voice embeddings (~12MB)",
    },
]


def download_models():
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("ERROR: huggingface_hub not installed.")
        print("Run: pip install huggingface_hub")
        sys.exit(1)

    print("=" * 55)
    print("VoxSales — Model Downloader")
    print("=" * 55)

    for model in MODELS_TO_DOWNLOAD:
        target = os.path.join(model["local_dir"], model["filename"])
        if os.path.exists(target):
            size_mb = os.path.getsize(target) / (1024 * 1024)
            print(f"[SKIP] {model['filename']} already exists ({size_mb:.1f} MB)")
            continue

        print(f"[DOWNLOADING] {model['desc']} ...")
        try:
            path = hf_hub_download(
                repo_id=model["repo_id"],
                filename=model["filename"],
                local_dir=model["local_dir"],
            )
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"[OK] {model['filename']} ({size_mb:.1f} MB) → {path}")
        except Exception as e:
            print(f"[ERROR] Failed to download {model['filename']}: {e}")
            sys.exit(1)

    print("\n✅ All models ready. You can now start the server:")
    print("   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    download_models()
