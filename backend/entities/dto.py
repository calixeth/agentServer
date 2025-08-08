from pydantic import BaseModel, Field


class GenCoverImgReq(BaseModel):
    x_link: str = Field(description="x link")
    img_url: str = Field(default="", description="img file url")


class GenCoverImgResp(BaseModel):
    task_id: str = Field(description="task id")
    img_url: str = Field(description="img file url")


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
