# Apex Sales AI — Backend

Backend API foundation, Dual Database Infrastructure, Domain Data Model, Repositories, Services, and REST API routes for the **Apex Sales AI** platform.

---

## 1. Overview
The Apex Sales AI backend provides a modular FastAPI architecture with dual database support and a complete domain application layer:
- **MongoDB**: Primary application database for domain models, leads, businesses, research, website audits, outreach, conversations, campaigns, agent execution history, and AI generation tracking.
- **SQLite**: Asynchronous local/system database for operational state, worker checkpoints, and metadata.

---

## 2. Virtual Environment Setup

To set up a Python virtual environment:

### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Requirements

```bash
pip install -r requirements.txt
```

---

## 4. Environment Configuration

Copy `.env.example` to create `.env`:

```bash
cp .env.example .env
```

### Database Environment Variables
- `MONGODB_URI`: Connection string for MongoDB instance (e.g. `mongodb+srv://user:pass@cluster.mongodb.net`).
- `MONGODB_DATABASE`: Default database name (default: `apex_sales`).
- `MONGODB_SERVER_SELECTION_TIMEOUT_MS`: Connection timeout in milliseconds (default: `5000`).
- `SQLITE_DATABASE_PATH`: Relative or absolute path for SQLite file (default: `./data/apex_sales.sqlite3`).

*(Never commit your `.env` file containing real credentials to source control.)*

---

## 5. Domain Architecture & Application Layer (Phase 4)

The backend strictly separates responsibilities into four layers:

```
API ROUTES (/api/v1) → SERVICES → REPOSITORIES → MONGODB
```

### Repositories (`app/repositories/`)
- Encapsulate persistence operations (`create`, `get_by_id`, `update_by_id`, `delete_by_id`, `count`, `list_paginated`).
- Repositories perform MongoDB queries only and contain zero AI, LLM, or external service calls.

### Services (`app/services/`)
- Encapsulate business logic, domain validation, reference verification, input normalization (domain/phone/name), and duplicate detection.
- Coordinate multiple repositories safely.

### API Routes (`app/api/routes/`)
- Expose RESTful JSON endpoints under `/api/v1`.
- Enforce strict request/response validation using API Pydantic request models (`app/schemas/api.py`).
- Implement pagination (`page`, `page_size`) and structured JSON error responses.

### Currently Available REST Endpoints (`/api/v1`):
- `POST /api/v1/businesses`: Create business (with duplicate check & normalization).
- `GET /api/v1/businesses`: List/search businesses (paginated).
- `GET /api/v1/businesses/{business_id}`: Get business by ID.
- `PATCH /api/v1/businesses/{business_id}`: Update business details.
- `POST /api/v1/leads`: Create lead (verifies associated business exists).
- `GET /api/v1/leads`: List leads (filterable by status, stage, score, business_id; paginated).
- `GET /api/v1/leads/{lead_id}`: Get lead details.
- `PATCH /api/v1/leads/{lead_id}`: Update lead state.
- `POST /api/v1/leads/{lead_id}/intelligence`: Orchestrate business verification, research, and website audit.
- `POST /api/v1/leads/{lead_id}/qualify`: Run AI lead qualification using OmniRoute and structured evidence.
- `POST /api/v1/leads/{lead_id}/pitch`: Generate personalized outreach draft (EMAIL, WHATSAPP, MANUAL) stored as DRAFT.
- `POST /api/v1/research`: Record business research data.
- `GET /api/v1/research/{research_id}`: Get research record.
- `GET /api/v1/businesses/{business_id}/research`: List research for a business.
- `POST /api/v1/website-audits`: Store website audit scores (0-100 validated).
- `GET /api/v1/website-audits/{audit_id}`: Get audit record.
- `GET /api/v1/businesses/{business_id}/website-audits`: List audits for a business.
- `POST /api/v1/outreach`: Create outreach record (defaults to `DRAFT`).
- `GET /api/v1/outreach/{outreach_id}`: Get outreach record.
- `GET /api/v1/leads/{lead_id}/outreach`: List outreach history for a lead.
- `PATCH /api/v1/outreach/{outreach_id}`: Update draft outreach (rejects direct transitions to `SENT`).
- `POST /api/v1/conversations`: Record communication conversation.
- `GET /api/v1/conversations/{conversation_id}`: Get conversation details.
- `GET /api/v1/leads/{lead_id}/conversation`: List conversations for a lead.
- `PATCH /api/v1/conversations/{conversation_id}`: Update conversation status/intent.
- `POST /api/v1/acquisition/search`: Search candidate business records (provider-independent candidate search).
- `POST /api/v1/acquisition/import`: Import selected candidates with Phase 6 deduplication and DO_NOT_CONTACT protection.
- `GET /api/v1/dashboard/summary`: Aggregate sales metrics summary (total businesses, leads, statuses, score breakdown, draft outreach).
- `GET /api/v1/sales/leads`: Pipeline lead listing with rich filtering (status, stage, score, service, city, category, verification, website/audit/pitch flags) and safe sorting.
- `GET /api/v1/sales/leads/{lead_id}`: Unified lead detail read-model composed from business, research, audit, qualification, outreach history, readiness flags, next recommended action, and prepared contact action data.
- `GET /api/v1/sales/leads/{lead_id}/timeline`: Lightweight chronological activity timeline.
- `POST /api/v1/sales/leads/{lead_id}/prepare`: Inspect action readiness flags and recommended next step.
- `POST /api/v1/sales/leads/{lead_id}/actions/{action_type}`: Trigger explicit sales actions (`RUN_INTELLIGENCE`, `QUALIFY`, `GENERATE_PITCH`).

*Note: `agent_runs` and `ai_generations` are internal persistence infrastructure and are not exposed as public API routes.*


---

## 6. Running the Development Server

Start the Uvicorn development server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, access:
- **API Base URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 7. Health & Readiness Endpoints

### Process Health (`GET /health`)
Verifies that the API process is alive. Functions independently of database state.

```bash
curl http://127.0.0.1:8000/health
```

Expected Response:
```json
{
  "status": "ok",
  "service": "apex-api",
  "version": "0.1.0"
}
```

### Infrastructure Readiness (`GET /ready`)
Checks database connectivity for MongoDB and SQLite.

```bash
curl http://127.0.0.1:8000/ready
```

---

## 8. Running Tests

Run unit and domain schema tests using `pytest`:

```bash
pytest
```

---

## 9. Current Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI Entrypoint & Database Lifespan
│   ├── api/                 # API Router, Health & Readiness Endpoints
│   ├── core/                # Config, Logging, Exceptions
│   ├── db/                  # MongoDB, SQLite, Health, & Index Manager
│   │   ├── __init__.py
│   │   ├── mongodb.py       # AsyncMongoClient lifecycle & ping
│   │   ├── sqlite.py        # Async SQLite setup & system_metadata
│   │   ├── health.py        # Database health aggregator
│   │   └── indexes.py       # MongoDB Collection Index Definitions
│   ├── schemas/             # Pydantic Schemas & Domain Enums
│   │   ├── __init__.py
│   │   ├── common.py        # PyObjectId & UTC Datetime Helpers
│   │   ├── enums.py         # Controlled Domain Enums
│   │   ├── business.py      # Business Schema
│   │   ├── lead.py          # Lead Schema
│   │   ├── research.py      # Research Schema
│   │   ├── website_audit.py # Website Audit Schema
│   │   ├── outreach.py      # Outreach Schema
│   │   ├── conversation.py  # Conversation Schema
│   │   ├── campaign.py      # Campaign Schema
│   │   ├── agent_run.py     # Agent Execution History Schema
│   │   └── ai_generation.py # LLM Generation Artifact Schema
├── tests/                   # Pytest Suite (Health, DB, Schemas, Indexes)
├── data/                    # Local Storage Directory
│   └── apex_sales.sqlite3   # Auto-created SQLite DB
├── requirements.txt         # Dependencies
├── .env.example             # Environment Variable Template
└── README.md                # Documentation
```

---

## 10. LLM Infrastructure & OmniRoute Gateway (Phase 5)

The LLM infrastructure layer provides a clean, unified abstraction (`LLMService` & `OmniRouteClient`) for interacting with an OpenAI-compatible OmniRoute gateway.

### LLM Architecture Hierarchy
```
AI Agents (Future Phases)
    ↓
LLMService (Application Orchestration & Audit Logging)
    ↓
OmniRouteClient (HTTP Client, Retry, Timeout & Exception Translation)
    ↓
OmniRoute Gateway (OpenAI-compatible Endpoint: http://localhost:20128/v1)
    ↓
Target LLM Model
```

### Environment Variables
- `OMNIROUTE_BASE_URL`: Base URL for OmniRoute OpenAI-compatible gateway (default: `http://localhost:20128/v1`).
- `OMNIROUTE_API_KEY`: API Key for OmniRoute authentication (kept strictly in `.env`).
- `OMNIROUTE_DEFAULT_MODEL`: Default LLM model identifier (configured via environment).
- `OMNIROUTE_TIMEOUT_SECONDS`: Request timeout in seconds (default: `60`).
- `OMNIROUTE_MAX_RETRIES`: Maximum retry attempts for transient errors (default: `2`).

### Client Capabilities & Retry Rules
- **OpenAI Compatibility**: Standard `/v1/chat/completions` request/response format.
- **Controlled Exception Handling**: Maps HTTP and network failures into explicit exceptions: `LLMConfigurationError`, `LLMAuthenticationError`, `LLMTimeoutError`, `LLMConnectionError`, `LLMRateLimitError`, `LLMUpstreamError`.
- **Conservative Retries**: Automatically retries safe transient failures (timeouts, network errors, 5xx server errors). Does **NOT** retry 401 Authentication errors or invalid client payloads.
- **Token Usage Normalization**: Parses `prompt_tokens`, `completion_tokens`, `total_tokens` safely, defaulting missing values to `None`.
- **AI Generation Audit Logging**: Automatically reuses existing `ai_generations` database service to store invocation state, model, latency, and token counts.

### Security Rules
- API keys, Bearer tokens, and Authorization headers are **never** logged or included in exception messages.
- The `sanitize_error_message` utility redacts credentials automatically before logging or raising errors.

### Local OmniRoute Configuration
To use a local OmniRoute instance, set the following in your `backend/.env`:
```env
OMNIROUTE_BASE_URL=http://localhost:20128/v1
OMNIROUTE_API_KEY=your_actual_omniroute_key
OMNIROUTE_DEFAULT_MODEL=your_model_name
OMNIROUTE_TIMEOUT_SECONDS=60
OMNIROUTE_MAX_RETRIES=2
```

---

## 11. AI Lead Qualification & Pitch Generation (Phase 9–10)

Apex Sales AI features AI-driven lead qualification and evidence-grounded personalized pitch draft generation powered by OmniRoute and `LLMService`.

### Qualification Architecture
- **Context Builder (`LeadAIContextBuilder`)**: Constructs compact JSON summaries from verified business details, research, and website audits while filtering out raw HTML, script/style blocks, credentials, and internal database IDs.
- **Evidence-Grounded Qualification (`LeadQualificationService`)**: Evaluates leads against deterministic signals + AI reasoning without inventing business facts.
- **Scoring & Interpretation**:
  - `0–29`: LOW_OPPORTUNITY
  - `30–49`: POSSIBLE
  - `50–69`: GOOD
  - `70–84`: HIGH
  - `85–100`: VERY_HIGH
- **Structured Validation & Repair**: Validates JSON output against `QualificationLLMOutput`. Performs a single repair attempt if initial LLM JSON output is malformed.
- **Safeguards**: Blocks qualification for leads marked `DO_NOT_CONTACT` or `INVALID`. Updates `lead.qualification`, `lead.score`, `lead.service_opportunity`, and `lead.evidence` without overwriting manually entered lead data.

### Pitch Generation Architecture
- **Personalized Drafts (`PitchGenerationService`)**: Generates personalized outreach pitches grounded strictly in observed audit issues (e.g. missing mobile viewport, low score, weak CTA).
- **Supported Channels**:
  - `EMAIL`: Includes concise, non-spammy subject line and professional body.
  - `WHATSAPP`: Short, natural, conversational message with `subject=None`.
  - `MANUAL`: Structured editable draft.
- **Human Approval Guarantee**: All generated pitches are saved into the `outreach` collection strictly with status `OutreachStatus.DRAFT`. Pitch generation **NEVER** sends emails, WhatsApp messages, or external communications automatically.
- **Duplicate Prevention**: Reuses active draft records for the same lead and channel when `force_refresh=False`.

---

## 12. Implementation Boundaries & Limitations
- **Human Approval Only**: The system creates `Outreach` DRAFT records. Email and WhatsApp messages are **NEVER** automatically sent.
- **No Background Workers**: No Celery, Redis, background jobs, or scheduled follow-up loops.
- **No RAG / Vector DB**: Vector embeddings and RAG vector databases are not implemented.
- **No Scraping**: Web content is analyzed using non-LLM HTML extraction and lightweight HTTP fetchers.
- **No Uncontrolled AI Usage**: AI requests use compact prompts and single-attempt JSON repair to ensure low cost and token budget control.



---

## 12. Lead Discovery Engine (Phase 6)

The Lead Discovery Engine provides candidate ingestion, deterministic normalization, duplicate detection, and automated Business + Lead creation.

### Discovery Architecture
```
USER / API REQUEST (POST /api/v1/discovery/search)
     ↓
DiscoveryService
     ↓
BaseDiscoverySource (Adapter Interface) → ManualDiscoverySource
     ↓
CandidateNormalizer (Domain, Phone, Email, Name)
     ↓
CandidateDeduplicator (Batch & MongoDB Lookup)
     ↓
BusinessService / LeadService
     ↓
MongoDB (businesses & leads collections)
```

### Key Components (`app/discovery/`)
- **`interfaces.py`**: Defines `BaseDiscoverySource` abstract adapter interface.
- **`sources/manual.py`**: `ManualDiscoverySource` for deterministic, zero-cost, manual candidate input without external APIs.
- **`normalizer.py`**: `CandidateNormalizer` for deterministic domain, phone, email, URL, and name normalization without LLMs.
- **`deduplicator.py`**: `CandidateDeduplicator` for batch-level in-memory deduplication and MongoDB domain/phone/name matching.
- **`service.py`**: `DiscoveryService` orchestrating discovery execution, conservative business updates, and default `NEW` lead record creation.
- **`schemas.py` & `models.py`**: `DiscoverySearchRequest`, `DiscoveredCandidate`, `NormalizedCandidate`, and `DiscoverySearchResponse`.

### REST Endpoint
- `POST /api/v1/discovery/search`: Ingests candidate items, normalizes data, deduplicates candidates, and returns execution metrics (`run_id`, `requested`, `received`, `valid`, `duplicates`, `new_businesses`, `existing_businesses`, `new_leads`, `created_business_ids`, `created_lead_ids`).

### Phase 6 Implementation Limitations
- **External Discovery Providers**: Google Maps API, Google Search API, and paid lead databases are **not** implemented.
- **Deterministic Operation Only**: No LLMs, AI normalization, AI deduplication, or AI lead qualification.
- **No Web Scraping or Browser Automation**: No site scraping, CAPTCHA bypassing, or headless browsers.

---

## 13. Verification, Business Research & Website Audit Engine (Phase 7–8)

The Lead Intelligence engine combines business verification, deterministic research extraction, and lightweight website health auditing into a unified workflow.

### Intelligence Architecture
```
USER / API REQUEST (POST /api/v1/leads/{lead_id}/intelligence)
     ↓
LeadIntelligenceService
     ├── VerificationService (Safe HTTP check, phone/email presence, domain match)
     ├── ResearchService (Deterministic HTML title/meta/headings extraction & upsert)
     └── WebsiteAuditService (Deterministic 0-100 website audit scoring & issue logging)
     ↓
MongoDB (businesses, leads, research, website_audits, agent_runs)
```

### Key Components
- **`app/verification/`**:
  - `security.py`: Safe URL parsing and SSRF protections blocking private IPv4/IPv6 ranges, loopback (`127.0.0.1`, `localhost`), and internal network targets.
  - `sources/website.py`: `SafeWebsiteFetcher` defensive HTTP retriever capped at 500 KB response body, 5s timeout, and 3 redirects max.
  - `validators.py` & `service.py`: Computes deterministic `VerificationStatus` (`VERIFIED`, `PARTIALLY_VERIFIED`, `FAILED`, `UNVERIFIED`) and stores evidence.
- **`app/research/`**:
  - `extractor.py`: Extracts meta descriptions, headings (`h1`/`h2`), product/service indicators, and visible text snippets without LLMs.
  - `service.py`: `ResearchService` upserts structured records into the `research` MongoDB collection.
- **`app/auditing/`**:
  - `checks.py`: Lightweight deterministic audit checks (accessibility, HTTPS, response timing, meta tags, mobile viewport, contact info, CTA wording).
  - `service.py`: `WebsiteAuditService` calculates transparent `0.0 <= score <= 100.0` score and logs `AuditIssue` items into `website_audits` MongoDB collection.
- **`app/intelligence/`**:
  - `service.py`: `LeadIntelligenceService` orchestrates verification, research, and audit stages with failure isolation so partial website errors do not crash the pipeline.

### REST Endpoint
- `POST /api/v1/leads/{lead_id}/intelligence`: Runs lead verification, research, and website auditing for a given lead ID and returns a structured intelligence response.

### Security & Safety Rules
- **SSRF Protection**: Rejects `file://`, `ftp://`, `localhost`, `127.0.0.1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, and private/link-local DNS target IPs.
- **Request Boundaries**: Maximum 500 KB body size limit, 5-second HTTP timeout, maximum 3 redirects.
- **Deterministic Processing Only**: OmniRoute and AI models are **not** invoked in this phase.



