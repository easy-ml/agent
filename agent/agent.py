import logging
import sys

import click
from core import Core

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s:\n%(message)s\n')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def callback(body):
    logger.info(f'[x] Received %r' % body)
    return None


@click.command()
@click.option('-m', '--amqp', envvar='AGENT_AMQP', required=True)
@click.option('-q', '--queue', envvar='AGENT_QUEUE', required=True)
@click.option('-a', '--app', envvar='AGENT_APP', required=True)
def run(amqp, queue, app):
    logger.info(f'''Loading agent with following parameters:
    AMQP: {amqp}
    QUEUE: {queue}
    APP: {app}''')

    core = Core(amqp, queue, callback)
    core.start()

    return 0


if __name__ == '__main__':
    sys.exit(run())
