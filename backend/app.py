import logging
import os

import uvicorn
from agents import set_default_openai_key
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from common.log import setup_logger
from common.tracing import Otel
from config import SETTINGS
from routes import api_router, voice_router

Otel.init()
setup_logger()

logger = logging.getLogger(__name__)
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
app.include_router(api_router.router)
app.include_router(voice_router.router)

if __name__ == '__main__':
    set_default_openai_key(SETTINGS.OPENAI_API_KEY)
    os.environ["OPENAI_API_KEY"] = SETTINGS.OPENAI_API_KEY

    uvicorn.run(app, host=SETTINGS.HOST, port=SETTINGS.PORT, workers=SETTINGS.WORKERS, log_config="log_config.yaml")
