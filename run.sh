#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 --reload main:app