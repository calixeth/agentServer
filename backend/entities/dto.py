from pydantic import BaseModel, Field


class GenCoverImgReq(BaseModel):
    x_link: str = Field(description="x link")
    img_url: str = Field(default="", description="img file url")


class GenCoverImgResp(BaseModel):
    task_id: str = Field(description="task id")
    img_url: str = Field(description="img file url")
