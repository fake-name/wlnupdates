#! /bin/bash

# Reinitialize the database for the app.
set -e

python migrator.py destroy

rm -rf ./migrations
python db_migrate.py db init
cp ./script.py.mako ./migrations/
python db_migrate.py db migrate
python db_migrate.py db upgrade
python db_migrate.py install_triggers
python db_migrate.py install_tgm_idx

python migrator.py
