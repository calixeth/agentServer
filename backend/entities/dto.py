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


class Cover(SubTask):
    input: GenCoverImgReq
    output: str | None = Field(description="cover img url", default=None)


class AIGCTaskQuery(BaseModel):
    task_id: str = Field(description="task_id")


class AIGCTask(BaseModel):
    task_id: str = Field(description="task_id")
    tenant_id: str = Field(description="tenant_id")
    cover: Cover | None = Field(description="cover", default=None)
    created_at: datetime.datetime = Field(description="created_at")


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
