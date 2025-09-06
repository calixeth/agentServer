import asyncio
import datetime
import json
import logging
import traceback

from common.tracing import Otel
from infra.db import logs_col


class MongoHandler(logging.Handler):

    def emit(self, record: logging.LogRecord):
        try:
            tid = getattr(record, "otelTraceID", None) or Otel.get_tid()
            if not tid or tid == '0':
                return
            message = record.getMessage()
            if not message.startswith("M "):
                return
            log_entry = {
                "ts": datetime.datetime.now(),
                "level": record.levelname,
                "tid": tid,
                "func": f"{record.filename}.{record.funcName}.{record.lineno}",
                "message": record.getMessage(),
            }

            if record.exc_info:
                log_entry["exc_info"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )
            elif record.stack_info:
                log_entry["stack_info"] = record.stack_info

            asyncio.create_task(logs_col.insert_one(log_entry))
        except Exception:
            pass


class JsonSingleLineFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "tid": getattr(record, "otelTraceID", None),
            "func": f"{record.filename}.{record.funcName}.{record.lineno}",
            "message": record.getMessage().replace("\n", " "),
        }

        if record.exc_info:
            log_record["exc_info"] = (
                "".join(traceback.format_exception(*record.exc_info))
                .replace("\n", " | ")
            )

        return json.dumps(log_record, ensure_ascii=False)


def setup_logger():
    Otel.init()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonSingleLineFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            handler,
            MongoHandler(),
        ]
    )
