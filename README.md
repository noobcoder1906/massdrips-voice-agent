# Mass Drips Voice Agent — Multi-Tenant AI Voice Sales Platform

Mass Drips Voice Agent is a production-grade, multi-tenant AI voice agent platform optimized for India & global e-commerce/SaaS sales. Powered by a highly modular zero-latency streaming architecture, the agent handles real-time natural conversations, product/catalog lookups, and appointment bookings using a cloned human voice.

---

## 🏗️ Modular Tech Stack Architecture

We use a **Modular Stack** rather than a generic all-in-one managed API. This drastically cuts costs (~10x cheaper at scale) and gives us absolute control over voice identity and speed.

- **Telephony & Transport**: Twilio + FastAPI + WebSockets (`16kHz PCM mono audio`)
- **VAD (Voice Activity Detection)**: Silero VAD (ONNX, 32ms frame processing)
- **STT (Speech-to-Text)**: Groq Whisper / Deepgram for ultra-low latency transcription
- **Intent Routing (The Manager)**: **Laya Router** 
  - Intercepts intents (e.g., `product_inquiry`, `bundle_inquiry`) *before* the LLM.
  - Handles dynamic catalog search (e.g., fuzzy matching "Ajith" -> "AK The Don's Edition").
  - Injects factual context to prevent LLM hallucinations.
- **LLM (The Brain)**: **Groq API** (Llama-3)
  - Blazing fast inference engine.
  - Takes Laya's structured context and generates conversational responses.
- **TTS (The Voice)**: **Chatterbox TTS + Edge-TTS Dual-Track Pipeline**
  - **Chatterbox**: Synthesizes the actual cloned human voice (derived from a Voicebox reference).
  - **Edge-TTS**: Fallback provider for instant 200ms initial response.
  - **Dual-Track**: edge_tts speaks the first sentence instantly while Chatterbox pre-synthesizes the rest in the background, achieving zero perceived latency.

- **Database**: MongoDB (Multi-tenant document schemas)
- **Frontend Dashboard**: Dark-mode glassmorphic single-page web app

---

## 🚀 Deployment & SaaS Roadmap

For scaling into a SaaS, running the custom Chatterbox TTS on a CPU is too slow (~30-60s latency). Here is the scaling strategy:

- **Phase 1 (Proof of Concept)**: Rent a cheap AWS EC2 Spot instance (`g4dn.xlarge` with NVIDIA T4) or a RunPod Community GPU (~$0.20/hr). This brings TTS latency down to ~300ms, making the cloned voice fully real-time.
- **Phase 2 (Serverless SaaS Scale)**: Split the architecture. The FastAPI backend runs on a cheap $5/month cloud server (always on). The Chatterbox TTS is moved to a **Serverless GPU** provider (like Modal or RunPod Serverless) so it spins up instantly, charges only by the millisecond of active voice generation, and scales infinitely.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- MongoDB Cluster URI (or local MongoDB)
- Groq API Key

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/noobcoder1906/massdrips-voice-agent.git
cd massdrips-voice-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file and configure:
```env
GROQ_API_KEY=your_key
MONGODB_URI=your_uri
TTS_PROVIDER=edge_tts  # Switch to 'chatterbox_clone' when running on a GPU
```

### 4. Seed Mass Drips Test Data
```bash
python -m backend.scripts.seed_db
```

### 5. Run Server
```bash
uvicorn backend.main:app --reload
```
Open **http://localhost:8000/dashboard** in your browser!

---

## 🐋 Docker Deployment

```bash
# Build and launch with Docker Compose
docker-compose up --build -d
```
