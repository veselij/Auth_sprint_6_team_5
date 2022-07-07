import logging
from logging import config as logging_config

from flask import has_request_context, request
from gunicorn import glogging

from core.config import config


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.request_id = request.headers.get("X-Request-Id")
        else:
            msg = record.getMessage()
            if not "request_id" in msg:
                return False
            record.request_id = msg.split("request_id")[-1].strip()
        return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "custom_filter": {
            "()": RequestIdFilter,
        },
    },
    "handlers": {
        "logstash": {
            "level": "INFO",
            "class": "logstash.LogstashHandler",
            "filters": ["custom_filter"],
            "host": config.logstash_host,
            "port": config.logstash_port,
            "version": 1,
            "message_type": "logstash",
            "fqdn": False,
            "tags": ["auth"],
        },
    },
    "loggers": {
        "gunicorn.error": {
            "propagate": True,
        },
        "gunicorn.access": {
            "propagate": True,
        },
    },
    "root": {"level": "INFO", "handlers": ["logstash"]},
}


class UniformLogger(glogging.Logger):
    def setup(self, cfg):
        logging_config.dictConfig(LOGGING)
