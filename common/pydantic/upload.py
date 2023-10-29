from pydantic import BaseModel

class Upload(BaseModel):
    id: str
    youtube_id: str
