from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ['.env', '../.env', '../../.env', '../../../.env']
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 1
    OPENAI_API_KEY: str = "<KEY>"
    PROMPT_KEY_ELEMENTS_APPEND: str = ""
    APP_NAME: str = "AgentServer"
    MONGO_STR: str = ""
    MONGO_DB: str = "agent-server"
    TWITTER241 = ""
    TWITTER241_HOST = ""
    TWITTER241_KEY = ""
    TZ_API_KEY = ""
    TZ_URL = ""
    AWS_ACCESS_KEY = ""
    AWS_SECRET_KEY = ""


SETTINGS = Settings()
