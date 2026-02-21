LLM Document Intelligence (FastAPI)

A lightweight Document Intelligence pipeline featuring authentication, document processing, lifecycle tracking, and real-time streaming.

🚀 Features

JWT authentication (1-hour expiry)

Upload PDF/TXT documents (single or multiple)

FIFO background processing (no Celery/Redis)

Text extraction (TXT + PDF via pypdf)

OpenAI analysis with retry-once logic

Persistent status history (survives restart)

Global Server-Sent Events (SSE) stream

Document delete endpoint

Strict lifecycle tracking:

pending → processing → analyzing → completed

or

pending → processing → failed
🧱 Tech Stack

FastAPI

SQLAlchemy + SQLite

OpenAI Python SDK

pypdf

SSE (Server-Sent Events)

📁 Project Structure
app/
  auth/
  config.py
  database.py
  main.py
  models/
  queue/
  routes/
  services/
  streaming/
  workers/
⚙️ Setup
1️⃣ Create virtual environment
python -m venv venv

Windows (Git Bash):

source venv/Scripts/activate

macOS/Linux:

source venv/bin/activate
2️⃣ Install dependencies
pip install -r requirements.txt
3️⃣ Configure Environment Variables

Create a .env file:

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4.1
JWT_SECRET=your_secret_key
JWT_EXPIRY_MINUTES=60
4️⃣ Run the server
uvicorn app.main:app --reload

Server runs at:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs
🧪 How To Test
1️⃣ Login
POST /auth/login
{
  "username": "admin",
  "password": "password123"
}

Copy the returned JWT.

2️⃣ Upload Document
POST /documents/upload

Use Authorization: Bearer <token>

3️⃣ Stream Status Updates
curl -N -H "Authorization: Bearer <token>" \
http://127.0.0.1:8000/documents/stream

You will see:

processing
analyzing
completed
4️⃣ Retrieve Document
GET /documents/{id}

Returns:

Extracted text

Analysis result

Full status history

Error (if any)

🔐 Security Notes

JWT expires in 60 minutes

OpenAI key must not be committed

SSE is authenticated

File size limit: 10MB

Allowed types: PDF, TXT

🧠 Design Notes

FIFO queue ensures strict processing order

Background worker runs inside FastAPI lifecycle

Status history stored in JSON column

Events published to global broadcaster

LLM retry logic prevents transient failures

🏁 Production Considerations

For production usage:

Replace SQLite with PostgreSQL

Use Redis/Celery for distributed queue

Add structured logging

Add rate limiting

Containerize with Docker

## ⏱ Time Breakdown (Approx.)
- Project setup + schema + auth: Xh
- Upload + validation + disk storage: Xh
- FIFO queue + worker: Xh
- Text extraction: Xh
- LLM analysis + retry: Xh
- SSE streaming: Xh
- Persistence + endpoints + delete: Xh
- README + testing: Xh