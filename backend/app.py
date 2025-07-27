import logging
import os

import fastapi
import uvicorn
from agents import set_default_openai_key
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from common.log import setup_logger
from common.response import RestResponse
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


@app.exception_handler(Exception)
async def default_exception_handler(request: fastapi.Request, exc: Exception):
    """"""
    logger.error("Exception handler", exc_info=True)
    return ORJSONResponse(
        RestResponse(code=500, msg=str(exc)).model_dump(),
        status_code=200
    )


if __name__ == '__main__':
    set_default_openai_key(SETTINGS.OPENAI_API_KEY)
    os.environ["OPENAI_API_KEY"] = SETTINGS.OPENAI_API_KEY

    uvicorn.run(app, host=SETTINGS.HOST, port=SETTINGS.PORT, workers=SETTINGS.WORKERS, log_config="log_config.yaml")
