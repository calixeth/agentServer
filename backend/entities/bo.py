from enum import StrEnum
from typing import Optional

from openai import BaseModel
from pydantic import BaseModel, Field

from entities.enums import ChainType


class Country(StrEnum):
    USA = 'USA'
    UK = 'UK'
    JP = 'JP'
    KR = 'KR'
    CN = 'CN'


class Language(StrEnum):
    ENGLISH = "English"
    CHINESE = "Chinese"
    JAPANESE = "Japanese"


class TwitterBO(BaseModel):
    id: str
    username: str
    data: dict
    avatar_url: str = ""
    avatar_url_400x400: str = ""
    avatar_base64: str = ""
    description: str = ""
    country: Country = None


class TwitterDTO(BaseModel):
    name: str = Field(default="", description="Display name of the user")
    screen_name: str = Field(default="", description="Unique Twitter handle (username)")
    profile_banner_url: str = Field(default="", description="URL of the profile banner image")
    profile_image_url_https: str = Field(default="", description="URL of the profile image in HTTPS")
    followers_count: int = Field(default=0, description="Number of followers")
    friends_count: int = Field(default=0, description="Number of accounts the user is following")
    description: str = Field(default="", description="Description of the user")
    timeline: dict = Field(default_factory=dict, description="timeline posts")


class FileBO(BaseModel):
    url: str


class GenImgTaskBO(BaseModel):
    template_img_base64: str
    prompt: Optional[str] = ""


class RefreshTokenRequest(BaseModel):
    """Request for refreshing access token"""
    refresh_token: str


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email for login")
    password: str


class WalletLoginRequest(BaseModel):
    """Request for wallet login/registration"""
    wallet_address: str
    signature: Optional[str] = None
    chain_type: Optional[ChainType] = Field(ChainType.ETHEREUM, description="Blockchain type for wallet authentication")


class TwitterTTSRequestBO(BaseModel):
    """Business object for Twitter TTS request"""
    twitter_url: str = Field(description="Twitter/X post URL")
    task_type: str = Field(default="tts", description="Task type (tts, voice_clone, music_gen)")
    voice: str | None = Field(default=None, description="TTS voice to use")
    model: str | None = Field(default=None, description="TTS model to use")
    response_format: str | None = Field(default=None, description="Audio format")
    speed: float | None = Field(default=None, description="Speech speed")
    tenant_id: str = Field(description="Tenant ID")
    voice_id: Optional[str] = Field(description="Voice ID")
    audio_url: Optional[str] = Field(description="Audio URL")
    username: Optional[str] = Field(default=None, description="Username for the TTS task")
    style: Optional[str] = Field(default=None, description="Music style for music generation tasks")
    digital_human_id: Optional[str] = Field(default=None, description="Digital human ID")


class TwitterTTSResp(BaseModel):
    audio_url: str
    tweet_id: str = ""
    tweet_content: str = ""
    tweet_created_at: str = ""
    tweet_username: str = ""
