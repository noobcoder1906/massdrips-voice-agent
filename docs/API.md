# VoxSales — API Documentation Reference

## Base URL
- Local: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎙️ Real-time Voice WebSocket

### `WS /ws/voice/{tenant_id}/{lead_id}`
Connects the live 4-stage pipeline (VAD → STT → LLM → TTS).

#### **Client to Server:**
- **Binary PCM Audio Frames**: 16kHz, 16-bit Mono PCM (640 bytes / 20ms chunks)
- **JSON Control Messages**:
  ```json
  { "type": "transcript", "text": "Hi, do you have black acid wash tees?" }
  ```

#### **Server to Client:**
- **Binary PCM Audio Frames**: AI speech synthesis stream
- **JSON Event Stream**:
  ```json
  { "type": "transcript", "text": "Customer speech transcription" }
  { "type": "agent_text", "text": "Agent response text" }
  { "type": "audio_start" }
  { "type": "audio_end" }
  ```

---

## 🏢 Tenants

### `POST /api/v1/tenants`
Create a new brand tenant.
```json
{
  "name": "Mass Drips",
  "slug": "mass-drips",
  "email": "admin@massdrips.com",
  "persona": {
    "agent_name": "Aria",
    "language": "hinglish",
    "tone": "friendly",
    "agent_type": "sales",
    "max_words": 60
  }
}
```

### `GET /api/v1/tenants/{tenant_id}`
Get tenant details and active persona config.

---

## 🎯 Leads

### `POST /api/v1/leads`
Create lead record.
```json
{
  "tenant_id": "mass-drips",
  "name": "Rahul Sharma",
  "phone": "+91-9876543210",
  "interests": ["acid wash", "hoodies"],
  "language": "hinglish",
  "tags": ["warm-lead"]
}
```

### `GET /api/v1/leads?tenant_id=mass-drips`
List leads for a tenant.

---

## 📦 Products

### `POST /api/v1/products`
Add product to catalog.
```json
{
  "tenant_id": "mass-drips",
  "name": "Acid Wash Oversized Tee",
  "price": 1299,
  "in_stock": true,
  "description": "240 GSM French Terry 100% Cotton",
  "tags": ["oversized", "acid wash"]
}
```

### `GET /api/v1/products?tenant_id=mass-drips`
Get live catalog for prompt context injection.

---

## 📢 Campaigns

### `POST /api/v1/campaigns`
Create and schedule an automated outbound calling campaign.
```json
{
  "tenant_id": "mass-drips",
  "name": "Monsoon Drop 2 Launch",
  "target_tag": "warm-lead",
  "concurrency_limit": 5,
  "scheduled_at": "2026-10-02T15:00:00Z"
}
```

### `GET /api/v1/campaigns?tenant_id=mass-drips`
List all campaigns and status (`draft`, `scheduled`, `active`, `completed`).

---

## 📊 Analytics & Calls

### `GET /api/v1/calls?tenant_id=mass-drips`
List past call logs with duration, sentiment, and transcripts.

### `GET /api/v1/smart/score/{call_id}`
Run AI post-call evaluation to calculate lead score delta and action recommendations.
