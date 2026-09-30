# 🚀 VoxSales — Autonomous AI Voice Sales Agent Platform

## Project Plan v3.0 — Multi-Tenant SaaS Edition

> **Vision:** Build a sellable, multi-tenant AI voice agent platform where **any business**
> can sign up, upload their product catalog, configure a sales persona, and launch
> autonomous outbound calling campaigns — all powered by open-source AI.
>
> **Mass Drips is Client #1.** Every other business is the next customer.
>
> Think **Bland AI + Retell AI**, but self-hosted, open-source AI backbone, and YOU own
> the platform.

---

## 🎯 What VoxSales Is (The Product)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         VOXSALES — FOR ANY BUSINESS                          │
│                                                                              │
│  🏪 Client: "Mass Drips" (Streetwear)                                        │
│     → Agent pitches oversized hoodies, handles sizing Q&A, offers discounts  │
│                                                                              │
│  🏥 Client: "HealthFirst Clinic" (Healthcare)                                │
│     → Agent calls patients for appointment reminders & follow-ups            │
│                                                                              │
│  🏫 Client: "SkillBridge Academy" (EdTech)                                   │
│     → Agent calls prospective students, explains courses, enrolls them       │
│                                                                              │
│  🏠 Client: "HomeLux Realty" (Real Estate)                                   │
│     → Agent calls leads about new property listings, schedules site visits   │
│                                                                              │
│  🍕 Client: "FoodDash" (D2C Food)                                            │
│     → Agent calls past customers with new menu items & combo offers          │
│                                                                              │
│  SAME PLATFORM. DIFFERENT PERSONA. DIFFERENT CATALOG. INFINITE SCALE.        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 💰 Business Model (How You Make Money)

| Plan | Pricing | What They Get |
| :--- | :--- | :--- |
| **Starter** | ₹4,999/mo (~$60) | 500 calls/mo, 1 agent persona, basic dashboard |
| **Growth** | ₹14,999/mo (~$180) | 3,000 calls/mo, 3 personas, analytics, A/B testing |
| **Enterprise** | ₹49,999/mo (~$600) | Unlimited calls, white-label, API access, custom voices |
| **Pay-as-you-go** | ₹2/min (~$0.025) | No commitment, billed per minute of call time |

**Your Margins:**
- Telephony cost (Twilio/Exotel): ~₹0.50/min
- AI compute (self-hosted): ~₹0.10/min
- **Your revenue: ₹2.00/min → 70%+ gross margin**

**Revenue Example:**
- 20 clients × Growth plan = ₹3,00,000/mo (~$3,600/mo)
- Infrastructure cost: ~₹50,000/mo
- **Net profit: ~₹2,50,000/mo (~$3,000/mo)**

---

## 📐 Architecture (Multi-Tenant SaaS)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CLIENT-FACING LAYER                                    │
│                                                                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────────────┐   │
│  │ Landing Page │  │ Client Dashboard │  │ Public API (REST + WebSocket) │   │
│  │ (Marketing) │  │ (Multi-tenant)   │  │ (For integrations)            │   │
│  └─────────────┘  └────────┬─────────┘  └──────────────┬────────────────┘   │
│                             │                           │                     │
└─────────────────────────────┼───────────────────────────┼─────────────────────┘
                              │ Auth (JWT + Tenant ID)    │
                              ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        PLATFORM BACKEND (FastAPI)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                     TENANT ISOLATION LAYER                            │    │
│  │  Every request is scoped to tenant_id. Data is never shared.         │    │
│  │  Each tenant has: own catalog, personas, campaigns, leads, calls     │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐     │
│  │ Auth Service   │  │ Tenant Manager │  │ Billing & Usage Tracker    │     │
│  │ (JWT + Roles)  │  │ (CRUD tenants) │  │ (Minutes, calls, limits)  │     │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘     │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐     │
│  │ Campaign       │  │ Lead Manager   │  │ Telephony Orchestrator     │     │
│  │ Engine         │  │ (Per-tenant)   │  │ (Twilio / Exotel / SIP)   │     │
│  └───────┬────────┘  └────────────────┘  └─────────────┬──────────────┘     │
│          │                                              │                    │
│          │         ┌────────────────────────────────────┘                    │
│          ▼         ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                    AI VOICE PIPELINE (Shared Infrastructure)          │    │
│  │                                                                      │    │
│  │  ┌───────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────┐  │    │
│  │  │ Silero    │─▶│ Faster-  │─▶│ Intent     │─▶│ Ollama LLM       │  │    │
│  │  │ VAD       │  │ Whisper  │  │ Router     │  │ (Tenant Persona) │  │    │
│  │  └───────────┘  └──────────┘  └────────────┘  └────────┬─────────┘  │    │
│  │                                                         │            │    │
│  │                                              ┌──────────┘            │    │
│  │                                              ▼                       │    │
│  │                                   ┌────────────────────┐             │    │
│  │                                   │ Kokoro / Piper TTS │             │    │
│  │                                   └────────────────────┘             │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER (Tenant-Isolated)                       │    │
│  │  MongoDB:      tenants, users, leads, campaigns, calls, billing        │    │
│  │  ChromaDB:   per-tenant product vectors (RAG)                        │    │
│  │  S3/MinIO:   call recordings (per-tenant folders)                    │    │
│  │  Redis:      session cache, rate limiting, real-time pub/sub         │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                    ADMIN PANEL (Platform Owner — YOU)                 │    │
│  │  - Manage all tenants        - View platform-wide analytics          │    │
│  │  - Monitor system health     - Manage billing & invoices             │    │
│  │  - Override tenant settings  - View all call logs                    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
voice-agent/
├── PROJECT_PLAN.md
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── alembic.ini                  # DB migrations config
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Settings & env
│   ├── database.py              # MongoDB async driver (Motor)
│   ├── models.py                # Pydantic models (tenants, users, leads, etc.)
│   ├── dependencies.py          # Auth + tenant context injection
│   │
│   ├── auth/                    # === AUTHENTICATION ===
│   │   ├── __init__.py
│   │   ├── jwt.py               # JWT token create/verify
│   │   ├── password.py          # Bcrypt hashing
│   │   └── routes.py            # Login, register, refresh token
│   │
│   ├── tenants/                 # === MULTI-TENANCY ===
│   │   ├── __init__.py
│   │   ├── manager.py           # Create/update/delete tenants
│   │   ├── middleware.py         # Tenant context middleware (extract from JWT)
│   │   └── routes.py            # Tenant settings API
│   │
│   ├── voice/                   # === VOICE PIPELINE (SHARED) ===
│   │   ├── __init__.py
│   │   ├── vad.py               # Silero VAD
│   │   ├── stt.py               # Faster-Whisper
│   │   ├── tts.py               # Kokoro / Piper TTS
│   │   └── audio_utils.py       # PCM/mulaw conversion
│   │
│   ├── agent/                   # === AI AGENT (TENANT-CONFIGURED) ===
│   │   ├── __init__.py
│   │   ├── router.py            # Jev-style intent router
│   │   ├── llm.py               # Ollama client
│   │   ├── persona.py           # Dynamic persona loader (per-tenant)
│   │   ├── tools.py             # Generic tool executor
│   │   ├── tool_registry.py     # Register custom tools per tenant
│   │   ├── objection_handler.py # Configurable objection responses
│   │   └── conversation.py      # State machine + memory
│   │
│   ├── catalog/                 # === PRODUCT CATALOG (PER-TENANT) ===
│   │   ├── __init__.py
│   │   ├── manager.py           # CRUD products (API upload / CSV import)
│   │   ├── vector_store.py      # ChromaDB per-tenant collections
│   │   └── routes.py            # Product catalog API
│   │
│   ├── telephony/               # === OUTBOUND CALLING ===
│   │   ├── __init__.py
│   │   ├── provider.py          # Abstract telephony provider interface
│   │   ├── twilio_provider.py   # Twilio implementation
│   │   ├── exotel_provider.py   # Exotel implementation (India)
│   │   ├── sip_provider.py      # Asterisk/FreeSWITCH SIP
│   │   ├── call_handler.py      # Bi-directional audio stream
│   │   └── recording.py         # Call recording + S3 upload
│   │
│   ├── campaigns/               # === CAMPAIGN ENGINE ===
│   │   ├── __init__.py
│   │   ├── manager.py           # Campaign CRUD
│   │   ├── scheduler.py         # Smart call scheduling
│   │   ├── lead_scorer.py       # AI lead scoring
│   │   ├── csv_parser.py        # Lead CSV upload
│   │   └── routes.py            # Campaign API
│   │
│   ├── analytics/               # === ANALYTICS & REPORTING ===
│   │   ├── __init__.py
│   │   ├── metrics.py           # Conversion, duration, sentiment metrics
│   │   ├── sentiment.py         # Real-time sentiment analysis
│   │   ├── reports.py           # Exportable reports (PDF/CSV)
│   │   └── routes.py            # Analytics API
│   │
│   ├── billing/                 # === USAGE TRACKING & BILLING ===
│   │   ├── __init__.py
│   │   ├── tracker.py           # Track minutes, calls per tenant
│   │   ├── plans.py             # Plan definitions & limits
│   │   ├── invoices.py          # Invoice generation
│   │   └── routes.py            # Billing API
│   │
│   ├── notifications/           # === POST-CALL ACTIONS ===
│   │   ├── __init__.py
│   │   ├── whatsapp.py          # WhatsApp message sender
│   │   ├── sms.py               # SMS sender
│   │   ├── email.py             # Email sender
│   │   └── webhook.py           # Webhook callbacks to client's CRM
│   │
│   ├── ws/                      # === WEBSOCKETS ===
│   │   ├── __init__.py
│   │   └── live_monitor.py      # Real-time call monitoring
│   │
│   ├── api/                     # === PUBLIC REST API ===
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── campaigns.py
│   │   │   ├── leads.py
│   │   │   ├── calls.py
│   │   │   ├── catalog.py
│   │   │   ├── analytics.py
│   │   │   └── settings.py
│   │   └── webhooks/
│   │       ├── twilio.py        # Twilio status callbacks
│   │       └── exotel.py        # Exotel callbacks
│   │
│   └── admin/                   # === PLATFORM ADMIN (YOUR PANEL) ===
│       ├── __init__.py
│       ├── routes.py            # Admin-only endpoints
│       └── superadmin.py        # Platform-wide management
│
├── frontend/
│   ├── index.html               # Landing page (marketing)
│   │
│   ├── dashboard/               # === CLIENT DASHBOARD ===
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── styles.css
│   │   └── pages/
│   │       ├── onboarding.js    # Setup wizard (catalog, persona, telephony)
│   │       ├── campaigns.js     # Campaign manager
│   │       ├── leads.js         # Lead management
│   │       ├── live-calls.js    # Real-time call monitor
│   │       ├── analytics.js     # Charts & metrics
│   │       ├── call-history.js  # Past calls & transcripts
│   │       ├── catalog.js       # Product catalog editor
│   │       ├── persona.js       # Agent persona configurator
│   │       ├── settings.js      # Account & billing settings
│   │       └── api-keys.js      # API key management
│   │
│   └── admin/                   # === YOUR ADMIN PANEL ===
│       ├── index.html
│       ├── app.js
│       └── pages/
│           ├── tenants.js       # All clients overview
│           ├── billing.js       # Revenue & invoicing
│           ├── system.js        # Server health monitoring
│           └── logs.js          # Platform-wide call logs
│
├── migrations/                  # === DATABASE MIGRATIONS ===
│   └── versions/
│
└── scripts/
    ├── setup_models.sh
    ├── seed_demo_tenant.py      # Create demo "Mass Drips" tenant
    ├── sample_leads.csv
    └── test_call.py
```

---

## 🔧 Technology Stack

| Layer | Technology | Why |
| :--- | :--- | :--- |
| **VAD** | Silero VAD v5 | Fastest open-source VAD, 30ms per chunk |
| **STT** | Faster-Whisper | 4x faster than OpenAI Whisper, multilingual |
| **Intent Router** | Sentence-Transformers | Sub-15ms routing, no LLM needed |
| **LLM** | Ollama (Llama 3.2 / Qwen 2.5) | Free, local, fast, tool-calling support |
| **TTS** | Kokoro-82M / Piper | Natural voice, sub-100ms generation |
| **RAG** | ChromaDB | Per-tenant vector collections |
| **Database** | PostgreSQL | Multi-tenant, ACID, battle-tested |
| **Cache** | Redis | Sessions, rate limiting, pub/sub |
| **Storage** | MinIO (S3-compatible) | Call recordings, self-hosted |
| **Backend** | FastAPI + Uvicorn | Async, WebSockets, OpenAPI docs |
| **Auth** | JWT + bcrypt | Stateless, scalable |
| **Telephony** | Twilio / Exotel / Asterisk | Pluggable provider interface |
| **Dashboard** | Vanilla JS + Chart.js | No framework overhead |
| **Deploy** | Docker Compose + Nginx | One-command deployment |

---

## 🏗️ Implementation Phases

### Phase 1: Core Voice Pipeline
**Goal:** Audio in → STT → LLM → TTS → audio out.

The shared AI backbone that every tenant uses:
- Silero VAD for speech boundary detection
- Faster-Whisper for transcription
- Ollama LLM for response generation
- Kokoro TTS for voice synthesis
- Full-duplex audio streaming

**Deliverable:** Working voice loop testable via local microphone.

---

### Phase 2: Multi-Tenant Foundation
**Goal:** Tenant isolation, auth, and per-tenant configuration.

**Database Models (Pydantic / MongoDB):**
```python
from pydantic import BaseModel, Field

class Tenant(BaseModel):
    id: str = Field(alias="_id")
    name: str                        # "Mass Drips"
    slug: str                        # "mass-drips"
    plan: str = "starter"
    # ... nested dicts and arrays are native to Mongo

class Lead(BaseModel):
    id: str = Field(alias="_id")
    tenant_id: str
    phone: str
    interests: list[str]             # ["hoodies", "tees"]
    conversation_history: list[dict] # Embed past calls directly in the lead document!
```

**Tenant Isolation Middleware (MongoDB):**
```python
# Every API request is scoped to the tenant's ObjectId
async def get_current_tenant(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt(token)
    tenant = await db.tenants.find_one({"_id": ObjectId(payload["tenant_id"])})
    if not tenant:
        raise HTTPException(403, "Tenant not found")
    return tenant
```

**Deliverable:** Signup → create tenant → configure persona → upload catalog.

---

### Phase 3: Client Onboarding Wizard
**Goal:** Any business can set up their agent in under 10 minutes.

**Setup Flow (4 Steps):**

**Step 1 — Business Profile:**
```
┌─────────────────────────────────────────────┐
│  Tell us about your business                │
│                                             │
│  Business Name: [Mass Drips            ]    │
│  Industry:      [Fashion & Apparel     ▼]   │
│  Website:       [massdrips.com         ]    │
│  Country:       [India                 ▼]   │
│  Language:      [English + Hindi       ▼]   │
└─────────────────────────────────────────────┘
```

**Step 2 — Product Catalog & Knowledge Base:**
```
┌─────────────────────────────────────────────┐
│  Upload your product catalog                │
│                                             │
│  [📁 Upload CSV]  or  [🔗 Connect API]      │
│                                             │
│  [PRO FEATURE] URL Auto-Scraper             │
│  Paste your website URL and we'll scrape    │
│  your products, FAQs, and policies:         │
│  [https://massdrips.com               ] [Go]│
│                                             │
│  ✅ 18 products imported                    │
│  ✅ 42 FAQ answers vectorized into RAG      │
└─────────────────────────────────────────────┘
```

**Step 3 — Agent Persona:**
```
┌─────────────────────────────────────────────┐
│  Configure your AI agent                    │
│                                             │
│  Agent Name: [DripBot                  ]    │
│  Voice:      [🔊 af_heart (Female)     ▼]   │
│  Personality: ☑ Energetic  ☑ Friendly       │
│               ☐ Formal     ☑ Persuasive     │
│                                             │
│  Opening Script:                            │
│  "Hey {lead_name}! This is {agent_name}     │
│   from {business_name}..."                  │
│                                             │
│  [▶ Test Call to My Phone]                  │
└─────────────────────────────────────────────┘
```

**Step 4 — Connect Phone Number:**
```
┌─────────────────────────────────────────────┐
│  Connect your calling provider              │
│                                             │
│  ○ Twilio  (Global, $0.013/min)             │
│  ○ Exotel  (India, ₹0.50/min)              │
│  ○ Plivo   (Global, $0.010/min)             │
│  ○ Custom SIP Trunk                         │
│                                             │
│  Twilio SID:  [AC123...             ]       │
│  Auth Token:  [••••••••             ]       │
│  Phone:       [+1234567890          ]       │
│                                             │
│  [✓ Verify Connection]                      │
└─────────────────────────────────────────────┘
```

**Deliverable:** Self-serve onboarding that any non-technical business owner can complete.

---

### Phase 4: Conversation Engine (Tenant-Configured)
**Goal:** Dynamic sales conversations powered by per-tenant personas and catalogs.

**How tenant config drives conversation:**
```python
# Each call loads the tenant's specific configuration
async def handle_call(tenant_id: str, lead_id: str):
    tenant = get_tenant(tenant_id)
    persona = get_persona(tenant_id)
    catalog = get_products(tenant_id)
    lead = get_lead(tenant_id, lead_id)

    # System prompt is dynamically built from tenant config
    system_prompt = f"""
    You are {persona.name}, the AI voice assistant for {tenant.name}.
    Industry: {tenant.industry}
    {persona.system_prompt}

    Available products:
    {format_catalog(catalog)}

    Customer info:
    Name: {lead.name}, City: {lead.city}
    Interests: {lead.interests}
    Past conversations: {lead.conversation_history}

    {persona.personality_instructions}
    """
```

**Deliverable:** Same platform, completely different conversations per client.

---

### Phase 5: Telephony Integration (Pluggable Providers)
**Goal:** Outbound calling via pluggable telephony providers.

**Provider Interface (Pluggable):**
```python
class TelephonyProvider(ABC):
    """Abstract interface — swap Twilio/Exotel/SIP without changing agent code."""

    @abstractmethod
    async def initiate_call(self, to_number: str, from_number: str,
                            webhook_url: str) -> str:
        """Start outbound call. Returns call_sid."""
        pass

    @abstractmethod
    async def connect_media_stream(self, call_sid: str,
                                    websocket_url: str) -> None:
        """Connect bi-directional audio stream."""
        pass

    @abstractmethod
    async def end_call(self, call_sid: str) -> None:
        """Hang up the call."""
        pass

    @abstractmethod
    def get_cost_per_minute(self) -> float:
        """Return cost per minute for billing."""
        pass

class TwilioProvider(TelephonyProvider): ...
class ExotelProvider(TelephonyProvider): ...
class SIPProvider(TelephonyProvider): ...
```

**Deliverable:** Make real outbound calls with swappable providers.

---

### Phase 6: Campaign Engine + Scheduling
**Goal:** Bulk campaigns with smart scheduling and retry logic.

Features:
- Upload CSV of leads → assign to campaign
- Smart scheduling (time zones, business hours, DND compliance)
- Concurrency control (max N simultaneous calls per tenant)
- Retry logic (no answer → retry with exponential backoff)
- Pause/resume campaigns
- A/B test different opening scripts

**Deliverable:** Launch a campaign → agent auto-calls 500 leads over 3 days.

---

### Phase 7: Live Dashboard + Analytics
**Goal:** Real-time monitoring and business intelligence.

**Dashboard Pages:**
1. **Campaign Overview** — Progress, conversion rate, calls remaining
2. **Live Call Monitor** — Real-time transcript, sentiment, "listen in" mode
3. **Analytics** — Conversion rates, avg duration, best products, heatmaps
4. **Call History** — Full transcripts, recordings, AI summaries, outcomes
5. **Lead Management** — Lead scores, statuses, conversation history
6. **Product Catalog** — CRUD products, bulk import, sync from API
7. **Agent Config** — Persona editor, voice selector, script builder
8. **Settings** — Billing, API keys, webhooks, team members

**Deliverable:** Production-ready client dashboard.

---

### Phase 8: Smart Features (Premium Tier)
**Goal:** Features that justify Enterprise & Pro pricing.

- **AI Lead Scoring** — Auto-score 0-100 after every call
- **Auto-Scraper (Pro)** — Input a website URL, and the system automatically crawls, chunks, and indexes FAQs, policies, and products into the tenant's ChromaDB RAG.
- **Auto Lead Generator (Pro)** — Instead of uploading CSVs, clients can input a prompt (e.g. "Dentists in Bengaluru") and the platform will scrape Google Maps/Directories for phone numbers and auto-populate the Campaign lead queue!
- **Smart Follow-ups** — Auto-schedule callbacks for "maybe" leads
- **Conversation Memory** — Remember past calls per lead across campaigns
- **Dynamic Pricing** — Escalating discounts based on objection intensity
- **Post-Call Actions** — WhatsApp/SMS/Email with product links + discount codes
- **Webhook Callbacks** — Push call results to client's CRM (HubSpot, Zoho, etc.)
- **Sentiment Analysis** — Real-time mood tracking during calls
- **Call Quality Detection** — Auto-suggest callback if audio is poor
- **A/B Script Testing** — Test different scripts, track which converts better
- **Voice Cloning** — Let clients upload their own voice (future: using OpenVoice)

**Deliverable:** Enterprise-grade features that differentiate from competitors.

---

### Phase 9: Public API + Webhook System
**Goal:** Let developers integrate VoxSales into their own apps.

**API Endpoints (v1):**
```
Authentication:
  POST   /api/v1/auth/login
  POST   /api/v1/auth/register

Catalog:
  GET    /api/v1/catalog/products
  POST   /api/v1/catalog/products
  PUT    /api/v1/catalog/products/{id}
  DELETE /api/v1/catalog/products/{id}
  POST   /api/v1/catalog/import-csv

Leads:
  GET    /api/v1/leads
  POST   /api/v1/leads
  POST   /api/v1/leads/import-csv
  GET    /api/v1/leads/{id}

Campaigns:
  GET    /api/v1/campaigns
  POST   /api/v1/campaigns
  POST   /api/v1/campaigns/{id}/start
  POST   /api/v1/campaigns/{id}/pause
  GET    /api/v1/campaigns/{id}/analytics

Calls:
  GET    /api/v1/calls
  GET    /api/v1/calls/{id}/transcript
  GET    /api/v1/calls/{id}/recording
  POST   /api/v1/calls/single          # Trigger single call via API

Webhooks:
  POST   /api/v1/webhooks              # Register webhook URL
  Events: call.started, call.completed, lead.converted, campaign.completed

Analytics:
  GET    /api/v1/analytics/overview
  GET    /api/v1/analytics/conversion
  GET    /api/v1/analytics/sentiment
```

**Deliverable:** Fully documented REST API for developer integrations.

---

### Phase 10: Docker + Production Deployment
**Goal:** One-command deployment to AWS.

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/voxsales
      - REDIS_URL=redis://redis:6379
      - OLLAMA_HOST=http://ollama:11434
    depends_on: [db, redis, ollama, minio]

  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices: [{capabilities: [gpu]}]  # Optional GPU

  db:
    image: postgres:16-alpine
    volumes: [pg_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    volumes: [minio_data:/data]

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
```

---

## 📊 Competitive Positioning

| Feature | VoxSales (You) | Bland AI | Retell AI | Vapi |
| :--- | :--- | :--- | :--- | :--- |
| **Pricing** | ₹2/min ($0.025) | $0.09/min | $0.08/min | $0.05/min |
| **Self-hosted option** | ✅ Yes | ❌ | ❌ | ❌ |
| **Open-source AI** | ✅ Fully | ❌ Closed | ❌ Closed | ❌ Closed |
| **India-optimized** | ✅ Hinglish, Exotel | ❌ | ❌ | ❌ |
| **Multi-tenant** | ✅ Built-in | ❌ | ❌ | ✅ |
| **White-label** | ✅ Enterprise | ❌ | ❌ | ❌ |
| **Per-tenant personas** | ✅ | ✅ | ✅ | ✅ |
| **Indian languages** | ✅ Hindi, Tamil, Telugu | Limited | Limited | Limited |
| **Objection handling** | ✅ Configurable | Basic | Basic | Basic |
| **Lead scoring** | ✅ AI-powered | ❌ | ❌ | ❌ |

**Your moat:** India-first, Hindi/Hinglish native, self-hostable, 70% cheaper.

---

## ⚡ Performance Targets

| Metric | Target |
| :--- | :--- |
| Voice-to-voice latency | < 500ms (GPU) / < 900ms (CPU) |
| Concurrent calls per server | 5-10 (CPU) / 20-50 (GPU) |
| Tenant onboarding time | < 10 minutes |
| Daily call capacity | 500-2,000 calls/server |
| API response time | < 100ms (p95) |
| Dashboard load time | < 2 seconds |

---

## 🚀 Build Order

```
Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5
 (Voice)    (Multi-     (Onboard)   (Convo      (Telephony)
            Tenant)                  Engine)

Phase 6 ──▶ Phase 7 ──▶ Phase 8 ──▶ Phase 9 ──▶ Phase 10
(Campaigns) (Dashboard) (Smart)     (API)       (Deploy)
```

**Estimated Timeline:**
- Phase 1-2: ~4 hours (voice pipeline + multi-tenant foundation)
- Phase 3-4: ~4 hours (onboarding + conversation engine)
- Phase 5-6: ~4 hours (telephony + campaigns)
- Phase 7-8: ~5 hours (dashboard + smart features)
- Phase 9-10: ~3 hours (API + deployment)

**Total: ~20-25 hours of focused building.**

---

## 📋 Prerequisites

```bash
# Python 3.11+
python --version

# Ollama
ollama pull llama3.2:3b

# PostgreSQL (via Docker)
docker run -d --name voxsales-db -p 5432:5432 \
  -e POSTGRES_PASSWORD=voxsales postgres:16-alpine

# Redis (via Docker)
docker run -d --name voxsales-redis -p 6379:6379 redis:7-alpine

# Twilio free trial (for testing calls)
# https://www.twilio.com/try-twilio
```

---

> **Mass Drips is Client #1. The rest of the market is your opportunity.**
> **Hit Proceed to start building Phase 1.**
