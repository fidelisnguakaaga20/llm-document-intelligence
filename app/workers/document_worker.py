import time
from datetime import datetime
from sqlalchemy.orm import Session
import os
import asyncio

from app.streaming.broadcaster import broadcaster
from app.queue.fifo_queue import document_queue
from app.models.document import Document
from app.services.text_extractor import extract_text
from app.services.llm_analyzer import analyze_with_retry

UPLOAD_DIR = "uploads"


def append_status(document: Document, new_status: str):
    history = document.status_history or []
    history.append({"status": new_status, "timestamp": datetime.utcnow().isoformat()})
    document.status_history = history
    document.current_status = new_status


def _safe_publish(event: dict):
    """
    Worker runs in a background thread.
    - If there's no running event loop: asyncio.run(...)
    - If there IS a running loop: schedule task on it
    """
    try:
        loop = asyncio.get_running_loop()
        # if we got a loop, schedule publish
        loop.create_task(broadcaster.publish(event))
    except RuntimeError:
        # no running loop
        asyncio.run(broadcaster.publish(event))


def publish_status_event(doc: Document):
    event = {
        "document_id": doc.id,
        "status": doc.current_status,
        "timestamp": datetime.utcnow().isoformat(),
        "filename": doc.filename,
    }

    if doc.current_status == "completed":
        event["analysis_result"] = doc.analysis_result

    if doc.current_status == "failed":
        event["error_message"] = doc.error_message

    _safe_publish(event)


def mark_failed(db: Session, doc: Document, error_message: str):
    doc.error_message = error_message
    append_status(doc, "failed")
    db.commit()
    publish_status_event(doc)
    print(f"[worker] failed: {doc.id} reason={error_message}")


def worker_loop(db_factory, poll_interval: float = 0.5):
    print("[worker] started")

    while True:
        doc_id = document_queue.dequeue()

        if not doc_id:
            time.sleep(poll_interval)
            continue

        db: Session = db_factory()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()

            if not doc:
                print(f"[worker] doc not found, skipping: {doc_id}")
                continue

            if doc.current_status != "pending":
                print(
                    f"[worker] doc not pending, skipping: {doc_id} status={doc.current_status}"
                )
                continue

            # 1) pending -> processing
            append_status(doc, "processing")
            db.commit()
            publish_status_event(doc)
            print(f"[worker] set processing: {doc.id}")

            # 2) Extract text
            file_path = os.path.join(UPLOAD_DIR, doc.id, doc.filename)
            ok, text_or_error = extract_text(file_path)
            if not ok:
                mark_failed(db, doc, text_or_error)
                continue

            doc.extracted_text = text_or_error
            db.commit()
            print(f"[worker] extracted text stored: {doc.id} chars={len(text_or_error)}")

            # 3) processing -> analyzing
            append_status(doc, "analyzing")
            db.commit()
            publish_status_event(doc)
            print(f"[worker] set analyzing: {doc.id}")

            # 4) LLM analysis with retry once
            ok2, result_or_error = analyze_with_retry(doc.extracted_text)
            if not ok2:
                mark_failed(db, doc, str(result_or_error))
                continue

            doc.analysis_result = result_or_error

            # 5) analyzing -> completed
            append_status(doc, "completed")
            db.commit()
            publish_status_event(doc)
            print(f"[worker] completed: {doc.id}")

        except Exception as e:
            db.rollback()
            print(f"[worker] unexpected error processing {doc_id}: {e}")
        finally:
            db.close()