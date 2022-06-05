from functools import wraps

from flask import request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

from core.config import config


def configure_tracing(app):

    @app.before_request
    def before_request() -> None:
        request_id = request.headers.get('X-Request-Id')
        user_ip = request.headers.get('X-Real-IP')
        if not request_id:
            raise RuntimeError('request id is required')
        if not user_ip:
            raise RuntimeError('real ip is required')

    def configure_tracer() -> None:
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: "Auth-service"})))
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=config.jager_host,
                    agent_port=6831,
                )
            )
        )
        if config.test:
            trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    configure_tracer()
    FlaskInstrumentor().instrument_app(app)


def tracing(func):
    @wraps(func)
    def inner(*args, **kwargs):
        request_id = request.headers.get('X-Request-Id')
        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(func.__name__)
        result = func(*args, **kwargs)
        span.set_attribute('http.request_id', request_id)
        span.end()
        return result
    return inner
