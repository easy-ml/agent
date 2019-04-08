#!/usr/bin/env bash
set -e

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

if [[ ! -d "venv" ]]; then
  virtualenv venv
  source ./venv/bin/activate
  pip3 install -r ./processor/requirements.txt
fi;

source ./venv/bin/activate
python ./processor/__main__.py "$@"
