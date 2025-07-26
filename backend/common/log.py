import logging

from common.tracing import Otel


def setup_logger():
    Otel.init()
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [%(levelname)s] tid=%(otelTraceID)s "
               "%(filename)s.%(funcName)s:%(lineno)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
