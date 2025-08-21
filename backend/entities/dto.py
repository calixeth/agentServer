import datetime
import uuid
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field

from common.error import raise_error
from entities.bo import Country


class TaskStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class Gender(StrEnum):
    MALE = "0"
    FEMALE = "1"


class SubTask(BaseModel):
    sub_task_id: str = Field(description="sub_task_id")
    status: TaskStatus = Field(description="status", default=TaskStatus.IN_PROGRESS)
    created_at: datetime.datetime = Field(description="created_at")
    done_at: datetime.datetime | None = Field(description="done_at", default=None)
    history: list[dict[str, Any]] = Field(description="history", default_factory=list)

    def regenerate(self) -> None:
        if self.status == TaskStatus.DONE:
            current_dict = self.model_dump()
            current_dict.pop("history", None)
            self.history.insert(0, current_dict)

        self.status = TaskStatus.IN_PROGRESS
        self.created_at = datetime.datetime.now()
        self.done_at = None
        self.sub_task_id = str(uuid.uuid4())


class GenCoverImgReq(BaseModel):
    task_id: str = Field(description="task_id")
    x_link: str = Field(description="x link")
    img_url: str = Field(default="", description="manually specify cover img")


class AIGCTaskID(BaseModel):
    """
    task_id
    """
    task_id: str = Field(description="task_id", default=None)


class AIGCPublishReq(BaseModel):
    """
    """
    task_id: str = Field(description="task_id")
    gender: Gender = Field(description="gender")
    description: str = Field(description="description", default="")
    mp3_url: str = Field(description="mp3 url", default="")
    x_tts_urls: list[str] = Field(description="x tts url", default_factory=list)


class ID(BaseModel):
    """
    id
    """
    id: str = Field(description="id", default=None)


class Username(BaseModel):
    """
    username
    """
    username: str = Field(description="username", default=None)


class GenCoverResp(BaseModel):
    first_frame_img_url: str = Field(description="first_frame_url")
    cover_img_url: str = Field(description="cover_url")


class Cover(SubTask):
    input: GenCoverImgReq
    output: GenCoverResp | None = Field(description="cover", default=None)


class VideoKeyType(StrEnum):
    TURN = "turn"
    SAYING = "saying"
    GOGO = "gogo"
    DANCE = "dance"
    ANGRY = "angry"
    DEFAULT = "default"
    THINK = "think"


class GenVideoReq(BaseModel):
    task_id: str = Field(description="task_id")
    key: VideoKeyType = Field(description="Unique key")
    # scenario: str = Field(description="Scenario Description")


class GenVideoResp(BaseModel):
    out_id: str = Field(description="out_id")
    view_url: str = Field(description="view url")
    download_url: str = Field(description="download url")


class Video(SubTask):
    input: GenVideoReq
    output: GenVideoResp | None = Field(description="video url", default=None)


class AIGCTask(BaseModel):
    task_id: str = Field(description="task_id")
    tenant_id: str = Field(description="tenant_id")
    created_at: datetime.datetime = Field(description="created_at")
    cover: Cover | None = Field(description="cover", default=None)
    videos: list[Video] = Field(description="videos", default_factory=list)

    def check_cover(self):
        if not self.cover or not self.cover.output or not self.cover.input.x_link:
            raise_error("cover img not found")


class TwitterTTSRequest(BaseModel):
    """Request model for creating Twitter TTS task"""
    twitter_url: str = Field(description="Twitter/X post URL")
    voice: Optional[str] = Field(default=None, description="TTS voice to use")
    model: Optional[str] = Field(default=None, description="TTS model to use")
    response_format: Optional[str] = Field(default=None, description="Audio format")
    speed: Optional[float] = Field(default=None, description="Speech speed")
    voice_id: Optional[str] = Field(default=None, description="Optional voice ID for TTS")
    audio_url: Optional[str] = Field(default=None, description="Optional audio URL for TTS")
    username: Optional[str] = Field(default=None, description="Username for the TTS task")


class TwitterTTSResponse(BaseModel):
    """Response for Twitter TTS task"""
    task_id: str = Field(description="Generated task ID")
    status: TaskStatus = Field(description="Task status")
    message: str = Field(description="Response message")


class TwitterTTSTask(BaseModel):
    """Twitter TTS task model"""
    task_id: str = Field(description="Unique task ID")
    tenant_id: str = Field(description="Tenant ID")
    twitter_url: str = Field(description="Twitter/X post URL")
    tweet_id: str = Field(description="Extracted tweet ID")
    voice: Optional[str] = Field(description="TTS voice")
    model: Optional[str] = Field(description="TTS model")
    response_format: Optional[str] = Field(description="Audio format")
    speed: Optional[float] = Field(description="Speech speed")
    status: TaskStatus = Field(description="Task status")
    created_at: datetime.datetime = Field(description="Task creation time")
    updated_at: datetime.datetime = Field(description="Last update time")
    title: str | None = Field(description="TTS title", default=None)
    tweet_content: str | None = Field(description="Extracted tweet content", default=None)
    voice_id: Optional[str] = Field(default=None, description="Optional voice ID for TTS")
    audio_url_input: Optional[str] = Field(default=None, description="Optional audio URL for TTS")
    audio_url: str | None = Field(description="Generated audio file URL", default=None)
    error_message: str | None = Field(description="Error message if failed", default=None)
    processing_started_at: datetime.datetime | None = Field(description="Processing start time", default=None)
    completed_at: datetime.datetime | None = Field(description="Completion time", default=None)
    username: Optional[str] = Field(default=None, description="Username for the TTS task")


class TwitterTTSTaskListResponse(BaseModel):
    """Response for Twitter TTS task list"""
    tasks: list[TwitterTTSTask] = Field(description="List of tasks")
    total: int = Field(description="Total number of tasks")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Page size")


class TwitterTTSTaskQuery(BaseModel):
    """Query parameters for Twitter TTS tasks"""
    tenant_id: str = Field(description="Tenant ID")
    page: int = Field(default=1, description="Page number")
    page_size: int = Field(default=20, description="Page size")
    status: TaskStatus | None = Field(default=None, description="Filter by status")


class PredefinedVoice(BaseModel):
    """Predefined voice model"""
    voice_id: str = Field(description="Unique voice identifier")
    name: str = Field(description="Voice display name")
    audio_url: Optional[str] = Field(default=None, description="Sample audio URL for preview")
    description: Optional[str] = Field(default=None, description="Voice description")
    category: Optional[str] = Field(default=None, description="Voice category")
    is_active: bool = Field(default=True, description="Whether the voice is available")
    created_at: datetime.datetime = Field(description="Creation time")
    updated_at: Optional[datetime.datetime] = Field(default=None, description="Last update time")


class PredefinedVoiceListResponse(BaseModel):
    """Response for predefined voice list"""
    voices: list[PredefinedVoice] = Field(description="List of predefined voices")
    total: int = Field(description="Total number of voices")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    access_token_expires_in: int  # in seconds
    refresh_token_expires_in: int  # in seconds


class NonceResponse(BaseModel):
    """Response containing nonce for wallet signature"""
    nonce: str
    message: str


class WalletLoginResponse(BaseModel):
    """Response for successful wallet login"""
    access_token: str
    refresh_token: str
    user: dict
    is_new_user: bool
    access_token_expires_in: int  # in seconds
    refresh_token_expires_in: int  # in seconds


class TokenResponse(BaseModel):
    """Response containing new access token"""
    access_token: str
    refresh_token: str
    access_token_expires_in: int  # in seconds
    refresh_token_expires_in: int  # in seconds
    user: dict


class DigitalVideo(BaseModel):
    key: str = Field(description="key")
    view_url: str = Field(description="video url")


class DigitalHuman(BaseModel):
    id: str = Field(description="Digital human ID")
    from_task_id: str = Field(description="from_task_id")
    from_tenant_id: str = Field(description="from_tenant_id")
    created_at: datetime.datetime = Field(description="created_at")
    updated_at: datetime.datetime = Field(description="updated_at")
    username: str = Field(description="username")
    cover_img: str = Field(description="cover_img")
    videos: list[DigitalVideo] = Field(description="videos", default_factory=list)
    gender: Gender = Field(description="gender")
    description: str = Field(description="description", default="")
    mp3_url: str = Field(description="mp3 url", default="")
    x_tts_urls: list[str] = Field(description="x tts url", default_factory=list)
    country: Country = Field(description="country")
