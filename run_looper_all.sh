#!/usr/bin/env bash

. ./flask/bin/activate


while true;
do
    python3 run.py all
    echo "Server 'python3 run.py all' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done;
