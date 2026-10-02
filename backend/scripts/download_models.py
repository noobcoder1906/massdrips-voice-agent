"""
backend/scripts/download_models.py

Downloads required Kokoro ONNX model files:
  - kokoro-v1.0.onnx (~325MB)
  - voices-v1.0.bin  (~27MB)
"""

import os
import sys
import urllib.request

MODELS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin":  "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}

def download_with_progress(url: str, output_path: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 1024 * 1024 # 1MB

        with open(output_path, "wb") as f:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                f.write(buffer)
                percent = (downloaded / total_size * 100) if total_size else 0
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  -> Downloading {os.path.basename(output_path)}: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.1f}%)")
                sys.stdout.flush()
    print("\n  [DONE] Saved to", output_path)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "voice", "models")
    os.makedirs(target_dir, exist_ok=True)

    print("=" * 60)
    print("VoxSales Model Downloader (Kokoro Neural TTS)")
    print("=" * 60)

    for filename, url in MODELS.items():
        out_file = os.path.join(target_dir, filename)
        if os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
            print(f"[EXISTS] {filename} already downloaded in {target_dir}")
            continue

        print(f"\n[DOWNLOADING] {filename} ...")
        try:
            download_with_progress(url, out_file)
        except Exception as e:
            print(f"\n[ERROR] Failed to download {filename}: {e}")

    print("\n=== All models verified and ready! ===")

if __name__ == "__main__":
    main()
