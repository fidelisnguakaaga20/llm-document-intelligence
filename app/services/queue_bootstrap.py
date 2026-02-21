from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.models.document import Document
from app.queue.fifo_queue import document_queue


def rebuild_queue_from_db(db: Session) -> int:
    """
    On server startup, re-enqueue documents that are still pending.
    This makes the system survive restart even though the queue is in-memory.
    """
    pending_docs = (
        db.query(Document)
        .filter(Document.current_status == "pending")
        .order_by(asc(Document.created_at))
        .all()
    )

    count = 0
    for doc in pending_docs:
        added = document_queue.enqueue(doc.id)
        if added:
            count += 1

    return count