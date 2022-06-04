from functools import wraps

from flask import request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter


def configure_tracing(app):

    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-Id')
        user_ip = request.headers.get('X-Real-IP')
        if not request_id:
            raise RuntimeError('request id is required')
        if not user_ip:
            raise RuntimeError('real ip is required')

    def configure_tracer() -> None:
        trace.set_tracer_provider(TracerProvider())
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name='localhost',
                    agent_port=6831,
                )
            )
        )
        # Чтобы видеть трейсы в консоли
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    configure_tracer()
    FlaskInstrumentor().instrument_app(app)


def tracing(func):
    @wraps(func)
    def inner(*args, **kwargs):
        request_id = request.headers.get('X-Request-Id')
        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(func.__name__)
        func(*args, **kwargs)
        span.set_attribute('http.request_id', request_id)
        span.end()
        return
    return inner
