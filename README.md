# 🎙️ VoxSales — Multi-Tenant AI Voice Sales Platform

VoxSales is a production-grade, multi-tenant AI voice agent platform optimized for India & global e-commerce/SaaS sales. Powered by zero-latency streaming architecture (Silero VAD + Faster-Whisper + Ollama LLM + Kokoro ONNX TTS), VoxSales enables automated outbound/inbound sales calls at <500ms voice-to-voice latency.

---

## ⚡ Tech Stack Architecture

- **Voice Pipeline**:
  - **VAD**: Silero VAD (ONNX, 32ms frame chunk processing)
  - **STT**: Faster-Whisper (`tiny.en` / `base`)
  - **LLM**: Ollama (`llama3.2:3b`) with streaming sentence generator
  - **TTS**: Kokoro ONNX offline speech synthesis
- **Backend & Transport**: FastAPI + WebSockets (`16kHz PCM mono audio`)
- **Database**: MongoDB (Multi-tenant document schemas)
- **Frontend Dashboard**: Dark-mode glassmorphic single-page web app
- **Telephony**: Swappable abstraction layer (Mock, Twilio, Exotel)

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed with model: `ollama pull llama3.2:3b`
- MongoDB Cluster URI (or local MongoDB)

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/noobcoder1906/massdrips-voice-agent.git
cd massdrips-voice-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Seed Mass Drips Test Data
```bash
python -m backend.scripts.seed_db
```

### 4. Run Server
```bash
python -m backend.main
```
Open **[http://localhost:8000/dashboard](http://localhost:8000/dashboard)** in your browser!

---

## 🐳 Docker Deployment

```bash
# Build and launch with Docker Compose
docker-compose up --build -d
```

---

## 📖 API Documentation

Interactive Swagger documentation is live at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### Key API Endpoints:
- `GET /` & `/dashboard` — Live Client Dashboard
- `POST /api/v1/calls/single` — Trigger single outbound call
- `GET /api/v1/campaigns` — Manage outreach campaigns
- `POST /api/v1/webhooks` — Register CRM webhook URL
- `POST /api/v1/smart/score-transcript` — AI lead scoring & post-call WhatsApp payloads
