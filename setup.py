from distutils.core import setup

from setuptools import find_packages

setup(
    name='agent',
    version='0.1',
    packages=find_packages(exclude=('tests',)),
    entry_points={
        'console_scripts': ['run-agent=agent.agent:run'],
    },
)
