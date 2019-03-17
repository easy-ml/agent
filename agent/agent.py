import logging

import click

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.option('-m', '--amqp', envvar='AGENT_AMQP', required=True)
@click.option('-q', '--queue', envvar='AGENT_QUEUE', required=True)
@click.option('-a', '--app', envvar='AGENT_APP', required=True)
def run(amqp, queue, app):
    logger.info(f'''
Loading agent with following parameters:
    AMQP: {amqp}
    QUEUE: {queue}
    APP: {app}''')


if __name__ == '__main__':
    run()
