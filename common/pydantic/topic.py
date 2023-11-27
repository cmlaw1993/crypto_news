from pydantic import BaseModel
from typing import Optional
from typing import List

class Topic(BaseModel):
    id: str
    content: str
    sources: Optional[List[str]] = None
    source_content: Optional[List[str]] = None
    priority: int
    priority_score: int
    reason: str
    datetime: str
    date: str
    time: str
