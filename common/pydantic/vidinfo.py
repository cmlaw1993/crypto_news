from pydantic import BaseModel
from typing import Optional
from typing import List


class Chapter(BaseModel):
    ts: int
    title: str
    digest: str


class VidInfo(BaseModel):
    id: str
    clip: str
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    chapters: List[Chapter]
    youtube_id: Optional[str] = None
