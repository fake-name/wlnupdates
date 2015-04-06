

from settings import DATABASE_IP, DATABASE_DB_NAME, DATABASE_USER, DATABASE_PASS

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{passwd}@{host}:5432/{database}'.format(user=DATABASE_USER, passwd=DATABASE_PASS, host=DATABASE_IP, database=DATABASE_DB_NAME)
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
