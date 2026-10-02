# VoxSales — Setup Guide

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Use 3.12 ideally |
| Ollama | Latest | [Install](https://ollama.com) |
| MongoDB Atlas | Free tier OK | Or local MongoDB |
| Node.js | 18+ | For the React dashboard |
| Git | Any | |

---

## Step 1 — Clone & Virtual Environment

```bash
git clone https://github.com/noobcoder1906/massdrips-voice-agent.git
cd massdrips-voice-agent

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

---

## Step 2 — Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   MONGO_URI — your MongoDB Atlas connection string
#   OLLAMA_HOST — usually http://localhost:11434
#   TELEPHONY_PROVIDER=mock  (for local testing without real phone calls)
```

---

## Step 3 — Download AI Models

### Ollama LLM
```bash
# Start Ollama (keep running in background)
ollama serve

# Pull the LLM model (~2GB, one-time)
ollama pull llama3.2:3b
```

### Kokoro TTS (ONNX)
```bash
# Run the model downloader script (downloads ~97MB total)
python -m backend.scripts.download_models
```

This downloads `kokoro-v1.0.onnx` and `voices-v1.0.bin` into the repo root.

> **Note:** Whisper STT (`base` model, ~145MB) auto-downloads on first call.

---

## Step 4 — Seed the Database

```bash
python -m backend.scripts.seed_db
```

This creates:
- **Mass Drips** tenant with `Aria` persona (Hinglish, friendly)
- 5 sample leads
- 8 sample products (hoodies, tees, cargo pants, etc.)
- MongoDB indexes

**Important:** Note the `Tenant ID` printed — you'll need it for WebSocket tests.

---

## Step 5 — Start the Backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit:
- **API Docs**: http://localhost:8000/docs
- **Dashboard** (legacy HTML): http://localhost:8000/dashboard

---

## Step 6 — Start the React Dashboard (Optional)

```bash
cd voxsales-app
npm install
npm run dev
```

Visit: http://localhost:5173

---

## Step 7 — Test the Voice WebSocket

Update `test_ws_client.py` with your tenant_id and lead_id from Step 4, then:

```bash
python test_ws_client.py
```

This simulates a voice call by sending text to the WebSocket. You'll see:
- Transcript echoed back
- Agent text response
- `audio_start` / `audio_end` events (PCM audio bytes in between)

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: apscheduler` | `pip install apscheduler` |
| `FileNotFoundError: kokoro-v1.0.onnx` | Run `python -m backend.scripts.download_models` |
| `Connection refused (11434)` | Run `ollama serve` in a separate terminal |
| `MongoDB connection failed` | Check `MONGO_URI` in `.env` — rotate password if exposed |
| `Whisper CUDA error` | Set `WHISPER_DEVICE=cpu` in `.env` |

---

## Architecture

```
Client (browser/phone)
    ↓ Binary PCM audio (16kHz, 16-bit, mono)
WebSocket /ws/voice/{tenant_id}/{lead_id}
    ↓
Silero VAD (32ms frames, ONNX)    → detects speech segments
    ↓
Faster-Whisper STT                → transcribes speech to text
    ↓
Laya Router (~33ms)               → routes intent (DNC, objection, general)
    ↓
Ollama LLM (llama3.2:3b)          → streaming sentence-level response
    ↓
Kokoro TTS (ONNX, offline)        → speech synthesis, 16kHz PCM
    ↓
WebSocket binary frames           → back to client for playback
```

Total pipeline latency target: **< 500ms** (GPU) / **< 900ms** (CPU)
