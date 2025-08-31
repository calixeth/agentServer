import json
import logging
import traceback

from common.tracing import Otel


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
        handlers=[handler]
    )
