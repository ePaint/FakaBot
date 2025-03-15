from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Video(BaseModel):
    id: Optional[str] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None

    @property
    def url(self) -> str:
        return f'https://www.youtube.com/watch?v={self.id}'

    @property
    def duration_label(self) -> str:
        return f'{self.duration // 60}:{self.duration % 60:02}'

    @property
    def label(self) -> str:
        return f'{self.title} ({self.duration_label})'

    @property
    def cache_path(self) -> Path:
        return Path(f'youtube_api/cache/downloads/{self.id}.mp3')
