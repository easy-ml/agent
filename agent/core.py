import json
import logging
from json import JSONDecodeError

import pika

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, amqp: str, queue: str, handler):
        connection_params = pika.URLParameters(amqp)

        self._connection = pika.BlockingConnection(connection_params)

        self._input_queue = f'{queue}_input'
        self._output_queue = f'{queue}_output'

        self._input_channel = self._connection.channel()
        self._output_channel = self._connection.channel()

        self._input_channel.queue_declare(queue=self._input_queue, durable=True)
        logger.info('Declared input queue')
        self._output_channel.queue_declare(queue=self._output_queue, durable=True)
        logger.info('Declared output queue')

        self._input_channel.basic_consume(self._process_callback, queue=self._input_queue)

        self._publish_properties = pika.BasicProperties(delivery_mode=2)

        self._handler = handler

    def _prepare_callback(self, ch, method, properties, body):
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
            response['response'] = self._handler(payload)
        except Exception as e:
            logger.exception('Payload:\n %r', payload)
            response['error'] = str(e)

        self.send(json.dumps(response, ensure_ascii=False, sort_keys=True))

    def _process_callback(self, ch, method, properties, body):
        try:
            self._prepare_callback(ch, method, properties, body)
        except Exception:
            logger.exception('Unexpected behavior:\n %r', body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def send(self, body):
        self._output_channel.basic_publish(
            exchange='',
            routing_key=self._output_queue,
            body=body,
            properties=self._publish_properties,
        )
        logger.info('[x] Sent %s', body)

    def start(self):
        self._input_channel.start_consuming()
