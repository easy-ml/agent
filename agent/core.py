import json
import logging
from json import JSONDecodeError

import pika

from agent.service import CoreService

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, amqp: str, queue: str, handler, core_service: CoreService):
        self._connection_params = pika.URLParameters(amqp)
        self._queue = queue
        self._handler = handler
        self._core_service = core_service

        self._connect()

    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=self._queue, durable=True)
        self._channel.basic_consume(queue=self._queue, on_message_callback=self._process_callback)

    def _prepare_callback(self, channel, method, properties, body):
        try:
            data = json.loads(body.decode('utf-8'))
            request_id = data['request_id']
            payload = data['payload']
        except JSONDecodeError:
            logging.warning('Invalid format of request:\n%r', body)
            return
        except KeyError:
            logging.warning('Invalid format of request:\n%r', body)
            return

        response = {'request_id': request_id, 'request': data}

        try:
            response['response'] = self._handler(request_id, payload)
        except Exception as e:
            logger.exception('Payload:\n %r', payload)
            response['error'] = str(e)

        self.send(response)

    def _process_callback(self, ch, method, properties, body):
        try:
            self._prepare_callback(ch, method, properties, body)
        except Exception:
            logger.exception('Unexpected behavior:\n %r', body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def send(self, data):
        response = data.get('error', data.get('response'))
        self._core_service.update_request(data['request_id'], response or {'error': None})
        logger.info('[x] Sent %r', response)

    def start(self):
        self._channel.start_consuming()
