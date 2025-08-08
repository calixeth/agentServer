from typing import Optional

from pydantic import BaseModel, Field

from entities.enums import ChainType


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



