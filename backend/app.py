import logging
import os

import uvicorn
from agents import set_default_openai_key
from fastapi import FastAPI

from config import SETTINGS
from routes import api_router, voice_router

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [%(levelname)s] "
           "%(filename)s.%(funcName)s:%(lineno)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Server starting...")
app = FastAPI()
app.include_router(api_router.router)
app.include_router(voice_router.router)

logger.info("Application initialization complete")

if __name__ == '__main__':
    set_default_openai_key(SETTINGS.OPENAI_API_KEY)
    os.environ["OPENAI_API_KEY"] = SETTINGS.OPENAI_API_KEY

    uvicorn.run(app, host=SETTINGS.HOST, port=SETTINGS.PORT, workers=SETTINGS.WORKERS)
