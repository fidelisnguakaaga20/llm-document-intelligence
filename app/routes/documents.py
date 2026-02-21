import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.jwt_handler import verify_token
from app.database import SessionLocal
from app.models.document import Document
from app.models.schemas import DocumentDetail, DocumentListItem, DocumentStatusOnly
from app.queue.fifo_queue import document_queue

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {".pdf", ".txt"}

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _append_status(document: Document, new_status: str):
    history = document.status_history or []
    history.append({"status": new_status, "timestamp": datetime.utcnow().isoformat()})
    document.status_history = history
    document.current_status = new_status


@router.post("/upload")
def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    uploaded = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Allowed: pdf, txt",
            )

        # Read bytes
        content = file.file.read()
        size = len(content)
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file.filename}. Max 10MB per file.",
            )

        document_id = str(uuid.uuid4())
        doc_dir = os.path.join(UPLOAD_DIR, document_id)
        os.makedirs(doc_dir, exist_ok=True)

        save_path = os.path.join(doc_dir, file.filename)
        with open(save_path, "wb") as f:
            f.write(content)

        doc = Document(
            id=document_id,
            filename=file.filename,
            current_status="pending",
            status_history=[],
            extracted_text=None,
            analysis_result=None,
            error_message=None,
        )

        # Add "pending" once
        _append_status(doc, "pending")

        db.add(doc)
        db.commit()

        # FIFO enqueue
        document_queue.enqueue(document_id)

        uploaded.append(
            {
                "document_id": document_id,
                "filename": file.filename,
                "status": doc.current_status,
            }
        )

    return {"uploaded_documents": uploaded}


@router.get("", response_model=List[DocumentListItem])
def list_documents(
    status: Optional[str] = Query(default=None, description="Filter by current_status"),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    q = db.query(Document).order_by(Document.created_at.desc())

    if status:
        q = q.filter(Document.current_status == status)

    docs = q.all()
    return [
        DocumentListItem(
            document_id=d.id,
            filename=d.filename,
            current_status=d.current_status,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document_detail(
    document_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDetail(
        document_id=d.id,
        filename=d.filename,
        current_status=d.current_status,
        status_history=d.status_history or [],
        extracted_text=d.extracted_text,
        analysis_result=d.analysis_result,
        error_message=d.error_message,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusOnly)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentStatusOnly(document_id=d.id, current_status=d.current_status)


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token),
):
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    # optional safeguard: don't delete in-flight docs
    if d.current_status in ("pending", "processing", "analyzing"):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete document while processing",
        )

    db.delete(d)
    db.commit()

    folder = os.path.join(UPLOAD_DIR, document_id)
    if os.path.exists(folder):
        shutil.rmtree(folder, ignore_errors=True)

    return {"message": "Deleted", "document_id": document_id}