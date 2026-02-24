LLM Document Intelligence (FastAPI)
A production-style Document Intelligence pipeline built with FastAPI, featuring authentication, FIFO background processing, persistent lifecycle tracking, OpenAI integration, and real-time streaming via Server-Sent Events (SSE).
🚀 Core Features
JWT Authentication (1-hour expiry)
Upload single or multiple PDF/TXT files (max 10MB per file)
FIFO background processing (no Redis / Celery)
Persistent status lifecycle tracking with timestamps
Text extraction (TXT + PDF via pypdf)
OpenAI integration using gpt-4.1
Retry-once logic for LLM failures
Real-time global SSE streaming (/documents/stream)
Full document retrieval endpoints
Delete endpoint
Restart-safe queue recovery
🏗 Architecture Overview
The system follows a lightweight, self-contained backend architecture:
Client → Auth → Upload → FIFO Queue → Background Worker →
Text Extraction → OpenAI Analysis → Persistence → SSE Broadcast
Key Design Decisions
In-memory FIFO queue (collections.deque) for strict processing order.
Worker thread started during FastAPI startup lifecycle.
SQLite for persistence (no external DB as per requirement).
JSON column for status history preservation.
Broadcaster pattern for SSE client management.
Retry-once logic for OpenAI calls to handle transient failures.
Queue rebuild on startup by scanning DB for pending documents.
🔁 Document Lifecycle
Each document transitions through:
Copy code

pending → processing → analyzing → completed
Or:
Copy code

pending → processing → failed
All status changes:
Include timestamps
Are persisted in SQLite
Survive server restarts
Are streamed in real-time via SSE
🧠 Queue Design
Implemented using deque
Thread-safe locking to prevent race conditions
Duplicate prevention
Background worker continuously polls queue
On restart, the system re-queues any document still marked as pending
This ensures:
Strict FIFO order
No job loss on restart
No double-processing
📡 Streaming Design (SSE)
Endpoint: GET /documents/stream
Authenticated via JWT
Uses Server-Sent Events (text/event-stream)
Publishes:
document_id
status
timestamp
filename
analysis_result (on completion)
error_message (on failure)
Handles client disconnection gracefully
Supports multiple concurrent listeners
🛠 Tech Stack
FastAPI
SQLAlchemy + SQLite
OpenAI Python SDK
pypdf
Threading
SSE (Server-Sent Events)
📁 Project Structure
Copy code

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
Bash
Copy code
python -m venv venv
Windows (Git Bash):
Bash
Copy code
source venv/Scripts/activate
macOS/Linux:
Bash
Copy code
source venv/bin/activate
2️⃣ Install dependencies
Bash
Copy code
pip install -r requirements.txt
3️⃣ Environment Variables
Create .env file:
Copy code

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4.1
JWT_SECRET=your_secret_key
JWT_EXPIRY_MINUTES=60
4️⃣ Run Server
Bash
Copy code
uvicorn app.main:app --reload
Access:
API: http://127.0.0.1:8000�
Swagger: http://127.0.0.1:8000/docs�
🧪 Testing Flow
1️⃣ Login
Copy code

POST /auth/login
{
  "username": "admin",
  "password": "password123"
}
2️⃣ Upload Document
Copy code

POST /documents/upload
Use Authorization: Bearer <token>
3️⃣ Stream Status
Bash
Copy code
curl -N -H "Authorization: Bearer <token>" \
http://127.0.0.1:8000/documents/stream
4️⃣ Retrieve Document
Copy code

GET /documents/{id}
Returns:
extracted_text
analysis_result
full status history
error (if any)
🔐 Security Considerations
JWT expires in 60 minutes
OpenAI API key loaded from environment
No secrets committed
File size limit enforced (10MB)
Allowed extensions enforced (.pdf, .txt)
Worker failure isolation
⚖ Trade-offs & Design Choices
SQLite chosen per requirement (no external DB)
Thread-based worker used instead of Celery for lightweight design
SSE chosen over WebSockets for simplicity and HTTP-native streaming
In-memory queue acceptable due to restart-safe DB recovery
For production:
Replace SQLite with PostgreSQL
Use Redis/Celery for distributed processing
Add structured logging
Add rate limiting
Containerize with Docker
Add integration tests
⏱ Time Breakdown
Project setup + schema + auth: 1.5h
Upload + validation + disk storage: 1h
FIFO queue + worker implementation: 1.5h
Text extraction logic: 0.5h
OpenAI integration + validation + retry: 1h
SSE streaming + broadcaster: 1h
Persistence + endpoints + delete: 1h
Documentation + testing: 0.5h
Total: ~8 hours
