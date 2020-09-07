#!/usr/bin/env bash


while true;
do
    python3 run_background.py
    echo "Server 'python run_background.py' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done;
