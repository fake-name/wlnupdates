#!/usr/bin/env bash

. ./flask/bin/activate


while true;
do
    python run.py
    echo "Server 'python run.py all' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done;
