#! /bin/bash

set -e

rm -rf migrations/

python db_migrate.py db init
cp ./script.py.mako ./migrations/
python db_migrate.py db migrate
python db_migrate.py db upgrade
