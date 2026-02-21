# LLM Document Intelligence (FastAPI)

A lightweight Document Intelligence pipeline:
- JWT auth (1-hour expiry)
- Upload PDF/TXT documents
- FIFO queue + background worker (no Celery/Redis)
- Text extraction (TXT + PDF)
- OpenAI analysis with retry-once
- Persistent status history (survives restart)
- Global SSE stream for document status updates

---

## Features

- **Auth**: `POST /auth/login` returns JWT (expires in 60 mins)
- **Upload**: `POST /documents/upload` supports single or multiple files
- **FIFO processing**: documents processed in strict upload order
- **Lifecycle tracking**: `pending → processing → analyzing → completed` (or `failed`)
- **Status history persisted** with timestamps
- **SSE stream**: `GET /documents/stream` emits updates for all documents
- **Retrieval**:
  - `GET /documents`
  - `GET /documents/{id}`
  - `GET /documents/{id}/status`

---

## Tech Stack

- FastAPI
- SQLAlchemy + SQLite
- pypdf (PDF text extraction)
- OpenAI Python SDK
- Server-Sent Events (SSE)

---

## Setup (Windows / macOS / Linux)

### 1) Create venv + install deps
```bash
python -m venv venv
# Windows Git Bash:
source venv/Scripts/activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

OPENAI_API_KEY=YOUR_OPENAI_API_KEY

OPENAI_MODEL=gpt-4.1