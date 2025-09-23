from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class EmojiBase(BaseModel):
    emojiID: str
    imageURL: Optional[str] = None
    imageURLWithBackground: Optional[str] = None
    predictionID: Optional[str] = None
    prompt: str
    userID: str
    visibility: str = "Public"
    createdAt: int
    downloadCount: int = 0
    category: Optional[str] = None

class EmojiListResponse(BaseModel):
    emojis: List[EmojiBase]
    next_cursor: Optional[str] = None
    has_more: bool = False

class Pack(BaseModel):
    name: str
    url: str
    downloadCount: int
    emojiCount: int
    description: str
    createdAt: int
    scrapedAt: int
    userID: str

class PackListResponse(BaseModel):
    packs: List[Pack]
    next_cursor: Optional[str] = None
    has_more: bool = False

class PackMigrationData(BaseModel):
    id: int = Field(..., description="Original pack ID")
    name: str = Field(..., description="Pack name")
    url: str = Field(..., description="Pack URL")
    download_count: int = Field(..., description="Download count")
    emoji_count: int = Field(..., description="Emoji count")
    description: str = Field(..., description="Pack description")
    created_at: str = Field(..., description="Creation timestamp string")
    scraped_at: str = Field(..., description="Scraped timestamp string")
    user_id: int = Field(..., description="Original user ID")