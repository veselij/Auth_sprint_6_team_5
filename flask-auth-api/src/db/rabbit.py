from contextlib import contextmanager

import pika

from core.config import config


class PikaClient:
    @contextmanager
    def rabbit_connection(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config.rabbit_host),
        )
        channel = connection.channel()
        channel.queue_declare(config.rabbit_queue, durable=True)
        try:
            yield channel
        finally:
            channel.close()
            connection.close()
