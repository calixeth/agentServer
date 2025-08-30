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


class TaskType(StrEnum):
    """Task type for Twitter TTS tasks"""
    TTS = "tts"  # Text-to-Speech (default)
    VOICE_CLONE = "voice_clone"  # Voice cloning
    MUSIC_GEN = "music_gen"  # Music generation


class MusicStyle(StrEnum):
    """Music style for music generation tasks"""
    POP = "pop"  # Pop music
    ROCK = "rock"  # Rock music
    JAZZ = "jazz"  # Jazz music
    CLASSICAL = "classical"  # Classical music
    ELECTRONIC = "electronic"  # Electronic music
    FOLK = "folk"  # Folk music
    BLUES = "blues"  # Blues music
    COUNTRY = "country"  # Country music
    HIP_HOP = "hip_hop"  # Hip hop music
    AMBIENT = "ambient"  # Ambient music
    CUSTOM = "custom"  # Custom style


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
    voice_id: str = Field(description="voice_id", default="Abbess")


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
    first_frame_img_url: str = Field(description="first_frame_url", default="")
    cover_img_url: str = Field(description="cover_url", default="")
    dance_first_frame_img_url: str = Field(description="dance_first_frame_img_url", default="")
    sing_first_frame_img_url: str = Field(description="sing_first_frame_img_url", default="")
    figure_first_frame_img_url: str = Field(description="figure_first_frame_img_url", default="")


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
    SING = "sing"
    SPEECH = "speech"
    FIGURE = "figure"


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
    task_type: Optional[TaskType] = Field(default=TaskType.TTS, description="Task type (tts, voice_clone, music_gen)")
    voice: Optional[str] = Field(default=None, description="TTS voice to use")
    model: Optional[str] = Field(default=None, description="TTS model to use")
    response_format: Optional[str] = Field(default=None, description="Audio format")
    speed: Optional[float] = Field(default=None, description="Speech speed")
    voice_id: Optional[str] = Field(default=None, description="Optional voice ID for TTS")
    audio_url: Optional[str] = Field(default=None, description="Optional audio URL for TTS")
    username: Optional[str] = Field(default=None, description="Username for the TTS task")
    style: Optional[str] = Field(default=None,
                                 description="Music style for music generation tasks (pop, rock, jazz, classical, electronic, folk, blues, country, hip_hop, ambient, custom)")


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
    task_type: TaskType = Field(default=TaskType.TTS, description="Task type (tts, voice_clone, music_gen)")
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
    style: Optional[str] = Field(default=None, description="Music style for music generation tasks")


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
    dance_image: str = Field(description="dance image", default=None)
    sing_image: str = Field(description="sing_image", default=None)
    figure_image: str = Field(description="figure image", default=None)


# New DTOs for lyrics and music generation APIs
class GenerateLyricsRequest(BaseModel):
    """Request for generating lyrics from Twitter URL"""
    twitter_url: str = Field(description="Twitter/X post URL")


class GenerateLyricsResponse(BaseModel):
    """Response for lyrics generation"""
    lyrics: str = Field(description="Generated lyrics text")
    title: str = Field(description="Extracted title from lyrics", default="")
    twitter_url: str = Field(description="Original Twitter URL")
    generated_at: str = Field(description="Generation timestamp")


class GenerateMusicRequest(BaseModel):
    """Request for generating music from lyrics"""
    lyrics: str = Field(description="Lyrics text to generate music from")
    style: str = Field(
        description="Music style (pop, rock, jazz, classical, electronic, folk, blues, country, hip_hop, ambient, custom)")
    reference_audio_url: str = Field(description="Audio url")
    voice: str = Field(description="TTS voice to use", default="alloy")
    model: str = Field(description="TTS model to use", default="tts-1")
    response_format: str = Field(description="Audio format", default="mp3")
    speed: float = Field(description="Speech speed", default=1.0, ge=0.25, le=4.0)


class GenerateMusicResponse(BaseModel):
    """Response for music generation"""
    audio_url: str = Field(description="Generated music audio URL")
    lyrics: str = Field(description="Original lyrics used")
    style: str = Field(description="Music style used")
    voice: str = Field(description="TTS voice used")
    model: str = Field(description="TTS model used")
    response_format: str = Field(description="Audio format")
    speed: float = Field(description="Speech speed used")
    generated_at: str = Field(description="Generation timestamp")
