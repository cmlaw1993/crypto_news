from pydantic import BaseModel
from typing import Optional
from typing import List

class Article(BaseModel):
    id: str
    title: str
    content: Optional[str]
    api: str
    api_type: str
    source: str
    author: str
    description: Optional[str] = None
    category: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    country: Optional[List[str]] = None
    language: Optional[str] = None
    news_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    datetime: str
    date: str
    time: str
