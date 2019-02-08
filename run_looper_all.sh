#!/usr/bin/env bash

source flask/bin/activate


while true;
do
    python3 run.py all
    echo "Server 'python3 run.py all' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done;
