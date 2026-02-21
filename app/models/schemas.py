from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class StatusEvent(BaseModel):
    status: str
    timestamp: str


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    current_status: str


class DocumentDetail(BaseModel):
    document_id: str
    filename: str
    current_status: str
    status_history: List[StatusEvent]
    extracted_text: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DocumentStatusOnly(BaseModel):
    document_id: str
    current_status: str