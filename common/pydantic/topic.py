from pydantic import BaseModel

class Topic(BaseModel):
    id: str
    content: str
    source: str
    source_content: str
    datetime: str
    date: str
    time: str
