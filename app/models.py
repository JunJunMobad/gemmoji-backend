from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class EmojiBase(BaseModel):
    emojiID: str = Field(..., description="Unique emoji identifier")
    imageURL: Optional[str] = Field(None, description="URL to the emoji image")
    imageURLWithBackground: Optional[str] = Field(None, description="URL to emoji image with background")
    predictionID: str = Field(..., description="Prediction ID")
    prompt: str = Field(..., description="Emoji prompt text")
    userID: str = Field(..., description="User ID who owns this emoji")
    visibility: str = Field("Public", description="Emoji visibility (Public/Private)")
    createdAt: int = Field(..., description="Creation timestamp in milliseconds")

class EmojiListResponse(BaseModel):
    emojis: List[EmojiBase]
    next_cursor: Optional[int] = Field(None, description="Cursor for next page (createdAt timestamp)")
    has_more: bool = Field(False, description="Whether there are more results available")

class Pack(BaseModel):
    name: str = Field(..., description="Pack name")
    url: str = Field(..., description="Pack URL")
    downloadCount: int = Field(..., description="Download count")
    emojiCount: int = Field(..., description="Emoji count")
    description: str = Field(..., description="Pack description")
    createdAt: int = Field(..., description="Creation timestamp in milliseconds")
    scrapedAt: int = Field(..., description="Scraped timestamp in milliseconds")
    userID: str = Field(..., description="User ID")

class PackListResponse(BaseModel):
    packs: List[Pack]
    next_cursor: Optional[int] = Field(None, description="Cursor for next page (createdAt timestamp)")
    has_more: bool = Field(False, description="Whether there are more results available")

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