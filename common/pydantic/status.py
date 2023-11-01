from pydantic import BaseModel
from typing import Dict, List

class StatusData(BaseModel):
    enable: bool
    weekend: bool
    append_output: bool
    input: List

class Status(BaseModel):
    download_news: StatusData
    news_to_vectordb: StatusData
    get_main_topics: StatusData
    construct_digest: StatusData
    rank_digest: StatusData
    select_digest: StatusData
    download_media: StatusData
    create_thumbnail: StatusData
    generate_clip: StatusData
    combine_clips: StatusData
    upload_clip: StatusData
    upload_thumbnail: StatusData
