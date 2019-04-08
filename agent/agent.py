import io
import logging
import os
import shutil
import sys
import zipfile

import click
import requests

from agent.core import Core
from agent.service import CoreService

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s:\n%(message)s\n')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

USER = 'appuser'
HOME = f'/home/{USER}/'


def prepare_app(app):
    logger.info('Preparing application')
    response = requests.get(app)
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    path = next((name for name in archive.namelist() if name.endswith('__main__.py')), None)
    if path is None:
        raise ValueError('__main__.py file has to be presented in app')
    top_folder = os.path.split(path)[0]
    archive.extractall(HOME)
    shutil.move(os.path.join(HOME, top_folder), os.path.join(HOME, 'processor'))
    logger.info('Application prepared')


def callback(core: CoreService):
    def cb(body):
        logger.info(f'[x] Received %r' % body)
        # core.get(body['image'])
        # su -c "bash run.sh {folder}" - appuser
        return None

    return cb


@click.command()
@click.option('-m', '--amqp', envvar='AGENT_AMQP', required=True)
@click.option('-q', '--queue', envvar='AGENT_QUEUE', required=True)
@click.option('-a', '--app', envvar='AGENT_APP', required=True)
@click.option('-t', '--token', envvar='AGENT_TOKEN', required=True)
@click.option('-s', '--server', envvar='SERVER', required=True)
def run(amqp, queue, app, token, server):
    """
    Run agent with following parameters
    :param amqp: Advanced Message Queuing Protocol URI
    :param queue: RabbitMQ Queue
    :param app: Application URL
    :param token: Access token
    :param server: Server URL
    """
    logger.info(f'''Loading agent with following parameters:
    AMQP: {amqp}
    QUEUE: {queue}
    APP: {app}''')

    prepare_app(app)
    core_service = CoreService(server, token)

    core = Core(amqp, queue, callback(core_service))
    core.start()
    return 0


if __name__ == '__main__':
    sys.exit(run())
