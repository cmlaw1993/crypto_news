from pydantic import BaseModel
from typing import Optional
from typing import List
from typing import Dict
from enum import Enum


class Effects(str, Enum):

    ZoomInCenter = 'ZoomInCenter'
    ZoomInUp = 'ZoomInUp'
    ZoomInUpRight = 'ZoomInUpRight'
    ZoomInRight = 'ZoomInRight'
    ZoomInDownRight = 'ZoomInDownRight'
    ZoomInDown = 'ZoomInDown'
    ZoomInDownLeft = 'ZoomInDownLeft'
    ZoomInLeft = 'ZoomInLeft'
    ZoomInUpLeft = 'ZoomInUpLeft'

    ZoomOutCenter = 'ZoomOutCenter'
    ZoomOutUp = 'ZoomOutUp'
    ZoomOutUpRight = 'ZoomOutUpRight'
    ZoomOutRight = 'ZoomOutRight'
    ZoomOutDownRight = 'ZoomOutDownRight'
    ZoomOutDown = 'ZoomOutDown'
    ZoomOutDownLeft = 'ZoomOutDownLeft'
    ZoomOutLeft = 'ZoomOutLeft'
    ZoomOutUpLeft = 'ZoomOutUpLeft'


class Media(BaseModel):
    id: str
    keyword: str
    source: str
    author: str
    credit: str
    license: str
    effects: str


class Digest(BaseModel):
    id: str
    main_topic: str
    title: str
    oneliner: str
    content: List[str]
    media: Optional[Dict[int, Media]] = None
    clip: Optional[str] = None
    sources: str
    articles: List[str]
    priority: int
    priority_score: int
    datetime: str
    date: str
    time: str
    reason: Optional[str] = None
