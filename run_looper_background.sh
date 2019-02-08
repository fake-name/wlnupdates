#!/usr/bin/env bash

source flask/bin/activate


while true;
do
    python run_background.py
    echo "Server 'python run_background.py' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done;
