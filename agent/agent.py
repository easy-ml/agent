import io
import json
import logging
import os
import shutil
import subprocess
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


class RequestFolder(object):
    def __init__(self, request_id):
        self._request_id = request_id
        self._path = os.path.join(HOME, request_id)

    def _clear(self):
        shutil.rmtree(self._path, ignore_errors=True)
        logger.info('Removed folder: %s', self._path)

    def __enter__(self):
        self._clear()
        os.mkdir(self._path)  # aware of umask
        os.chmod(self._path, 0o777)
        logger.info('Created folder: %s', self._path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clear()

    @property
    def path(self):
        return self._path


def callback(core: CoreService):
    def cb(request_id, payload):
        logger.info(f'[x] Received %r' % payload)

        with RequestFolder(request_id) as folder:
            response = {'thumbnail': None}

            image_id = payload['image']
            image_path = os.path.join(folder.path, image_id)
            with open(image_path, 'wb') as image:
                image.write(core.storage_get(image_id).content)
            logger.info('Image loaded: %s', image_path)

            meta_path = os.path.join(folder.path, 'meta.json')
            meta_json = {'image': image_id}
            with open(meta_path, 'w') as meta:
                json.dump(meta_json, meta)
            logger.info('Meta created: %s', meta_path)

            logger.info('Running subprocess in folder: %s', folder.path)
            process = subprocess.Popen(f'su -c "bash run.sh {folder.path}" - {USER}', shell=True)
            process.wait()

            zip_path = os.path.join(folder.path, 'output.zip')
            thumbnail_path = os.path.join(folder.path, 'thumbnail.png')
            output_info_path = os.path.join(folder.path, 'output.json')

            with open(output_info_path, 'r') as output_info_file:
                response['meta'] = json.load(output_info_file)

            uploaded = core.storage_upload(zip_path, request_id).json()
            response['content'] = uploaded.get('filename', None)

            if os.path.isfile(thumbnail_path):
                uploaded = core.storage_upload(thumbnail_path, request_id).json()
                response['thumbnail'] = uploaded.get('filename', None)

        return response

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
