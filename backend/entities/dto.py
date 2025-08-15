import datetime
import uuid
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


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


class AIGCTaskQuery(BaseModel):
    """
    task_id or x_username
    """
    task_id: str = Field(description="task_id", default=None)
    x_username: str = Field(description="x_username", default=None)


class Cover(SubTask):
    input: GenCoverImgReq
    output: str | None = Field(description="cover img url", default=None)


class VideoKeyType(StrEnum):
    TURN = "turn"
    SAYING = "saying"
    GOGO = "gogo"
    DANCE = "dance"
    ANGRY = "angry"
    DEFAULT = "default"


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


class TwitterTTSRequest(BaseModel):
    """Request for Twitter TTS task"""
    twitter_url: str = Field(description="Twitter/X post URL")
    voice: str = Field(default="alloy", description="TTS voice to use")
    model: str = Field(default="tts-1", description="TTS model to use")
    response_format: str = Field(default="mp3", description="Audio format")
    speed: float = Field(default=1.0, description="Speech speed")


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
    voice: str = Field(description="TTS voice")
    model: str = Field(description="TTS model")
    response_format: str = Field(description="Audio format")
    speed: float = Field(description="Speech speed")
    status: TaskStatus = Field(description="Task status")
    created_at: datetime.datetime = Field(description="Task creation time")
    updated_at: datetime.datetime = Field(description="Last update time")
    title: str | None = Field(description="TTS title", default=None)
    tweet_content: str | None = Field(description="Extracted tweet content", default=None)
    audio_url: str | None = Field(description="Generated audio file URL", default=None)
    error_message: str | None = Field(description="Error message if failed", default=None)
    processing_started_at: datetime.datetime | None = Field(description="Processing start time", default=None)
    completed_at: datetime.datetime | None = Field(description="Completion time", default=None)


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
