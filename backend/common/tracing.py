import logging
from typing import Optional

from opentelemetry import baggage
from opentelemetry import trace
from opentelemetry.baggage import get_baggage
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import get_current, attach
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import get_current_span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from config import SETTINGS

logger = logging.getLogger(__name__)


class Otel(object):
    """"""
    _executed = False
    _trace_provider = None
    _settings = None

    @staticmethod
    def init():
        if Otel._executed:
            return

        Otel._executed = True

        Otel._init_propagator()

        resource = Otel._init_resource()

        Otel._init_trace(resource)

    @staticmethod
    def get_tid() -> str:
        ret = ""
        try:
            current_span = get_current_span()
            tid = current_span.get_span_context().trace_id if current_span.get_span_context().is_valid else ''
            if tid:
                ret = format(tid, '032x')
        except Exception:
            pass
        return ret

    @staticmethod
    def get_sid() -> str:
        ret = ""
        try:
            current_span = get_current_span()
            sid = current_span.get_span_context().span_id if current_span.get_span_context().is_valid else ''
            if sid:
                ret = format(sid, '016x')
        except Exception:
            pass
        return ret

    @staticmethod
    def get_baggage(key: str) -> Optional[object]:
        if not key:
            return None
        current_context = get_current()
        return get_baggage(key, context=current_context)

    @staticmethod
    def add_baggage(name: str, value: object):
        current_context = get_current()
        attach(baggage.set_baggage(name, value, current_context))

    @staticmethod
    def _init_trace(resource):
        trace_provider = TracerProvider(resource=resource)
        Otel._trace_provider = trace_provider
        trace.set_tracer_provider(trace_provider)

        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument()

    @staticmethod
    def _init_propagator():
        propagator = CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
        set_global_textmap(propagator)

    @staticmethod
    def _init_resource():
        resource = Resource(attributes={
            SERVICE_NAME: SETTINGS.APP_NAME,
        })
        return resource
