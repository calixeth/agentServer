from typing import Optional

from pydantic import BaseModel


class TwitterBO(BaseModel):
    id: str
    username: str
    data: dict
    avatar_url: str = ""
    avatar_base64: str = ""


class FileBO(BaseModel):
    url: str


class GenImgTaskBO(BaseModel):
    template_img_base64: str
    prompt: Optional[str] = ""
