from pydantic import BaseModel
from typing import Optional
from typing import List
from typing import Dict


class Media(BaseModel):
    id: str
    keyword: str
    source: str
    author: str
    credit: str
    license: str


class Digest(BaseModel):
    id: str
    main_topic: str
    title: str
    oneliner: str
    content: List[str]
    media: Optional[Dict[int, Media]] = None
    clip: Optional[str] = None
    sources: List[str]
    source_content: List[str]
    articles: List[str]
    priority: int
    priority_score: int
    datetime: str
    date: str
    time: str
    reason: Optional[str] = None
