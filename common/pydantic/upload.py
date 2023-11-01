from pydantic import BaseModel
from typing import Optional
from typing import List


class Chapter(BaseModel):
    ts: int
    title: str


class Upload(BaseModel):
    id: str
    clip: str
    thumbnail: Optional[str] = None
    chapters: List[Chapter]
    youtube_id: Optional[str] = None
