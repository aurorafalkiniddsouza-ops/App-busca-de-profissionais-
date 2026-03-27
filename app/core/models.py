from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    searched_name: str
    council: str
    searched_state: Optional[str] = None
    found_name: Optional[str] = None
    registration_number: Optional[str] = None
    found_state: Optional[str] = None
    profession: Optional[str] = None
    status_text: Optional[str] = None
    final_status: str
    confidence_score: float = 0.0
    evidence_url: Optional[str] = None
    evidence_note: Optional[str] = None
    queried_at: datetime
    notes: Optional[str] = None
