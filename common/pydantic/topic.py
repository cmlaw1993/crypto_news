from pydantic import BaseModel

class Topic(BaseModel):
    id: str
    content: str
    source: str
    source_content: str
    priority: int
    priority_score: int
    datetime: str
    date: str
    time: str
