from fastapi import FastAPI, Depends
from threading import Thread

from app.database import Base, engine, SessionLocal
from app.models.document import Document

from app.routes.auth import router as auth_router
from app.routes.documents import router as document_router
from app.auth.jwt_handler import verify_token

from app.services.queue_bootstrap import rebuild_queue_from_db
from app.queue.fifo_queue import document_queue

from app.workers.document_worker import worker_loop  # NEW

from app.routes.stream import router as stream_router

app = FastAPI(title="Document Intelligence API")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(stream_router)     # ✅ register /documents/stream first
app.include_router(document_router)   # ✅ register /documents/{document_id} after

@app.on_event("startup")
def on_startup():
    # Rebuild queue (restart-safe)
    db = SessionLocal()
    try:
        requeued = rebuild_queue_from_db(db)
        print(f"[startup] Rebuilt queue. Requeued pending docs: {requeued}")
        print(f"[startup] Queue snapshot: {document_queue.snapshot()}")
    finally:
        db.close()

    # Start worker in background thread (non-blocking)
    t = Thread(target=worker_loop, args=(SessionLocal,), daemon=True)
    t.start()
    print("[startup] Worker thread started")


@app.get("/")
def root(payload: dict = Depends(verify_token)):
    return {
        "message": "Protected Route Access Granted",
        "user": payload.get("sub"),
        "queue_size": document_queue.size(),
    }