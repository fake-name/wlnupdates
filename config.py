

from settings import DATABASE_IP, DATABASE_DB_NAME, DATABASE_USER, DATABASE_PASS, SECRET_KEY

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{passwd}@{host}:5432/{database}'.format(user=DATABASE_USER, passwd=DATABASE_PASS, host=DATABASE_IP, database=DATABASE_DB_NAME)
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

import sys
if len(sys.argv) > 1 and "debug" in sys.argv:
	SQLALCHEMY_ECHO = True

CSRF_ENABLED = True

COVER_DIR_BASE = os.path.join(basedir, "./covers/")

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

# administrator list
ADMINS = ['you@example.com']

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

# pagination
TAGS_PER_PAGE = 50
GENRES_PER_PAGE = 50
SERIES_PER_PAGE = 50

POSTS_PER_PAGE = 50
MAX_SEARCH_RESULTS = 50
