

from settings import (DATABASE_IP, DATABASE_DB_NAME, DATABASE_USER, DATABASE_PASS, SECRET_KEY, WTF_CSRF_SECRET_KEY,
					MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, SECURITY_PASSWORD_SALT)
import os
import sys
if len(sys.argv) > 1 and "debug" in sys.argv:
	SQLALCHEMY_ECHO = True


basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):

	SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{passwd}@{host}:5432/{database}'.format(user=DATABASE_USER, passwd=DATABASE_PASS, host=DATABASE_IP, database=DATABASE_DB_NAME)
	SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

	CSRF_ENABLED = True
	WTF_CSRF_ENABLED = True

	COVER_DIR_BASE = os.path.join(basedir, "./covers/")


	# administrator list
	ADMINS = ['you@example.com']

	# slow database query threshold (in seconds)
	DATABASE_QUERY_TIMEOUT = 0.5

	SEND_FILE_MAX_AGE_DEFAULT = 60*60*12

	# pagination
	TAGS_PER_PAGE = 50
	GENRES_PER_PAGE = 50
	SERIES_PER_PAGE = 50

	POSTS_PER_PAGE = 50
	MAX_SEARCH_RESULTS = 50

	DATABASE_IP            = DATABASE_IP
	DATABASE_DB_NAME       = DATABASE_DB_NAME
	DATABASE_USER          = DATABASE_USER
	DATABASE_PASS          = DATABASE_PASS
	SECRET_KEY             = SECRET_KEY
	WTF_CSRF_SECRET_KEY    = WTF_CSRF_SECRET_KEY

	SECURITY_PASSWORD_SALT = SECURITY_PASSWORD_SALT

	# mail settings
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 465
	MAIL_USE_TLS = False
	MAIL_USE_SSL = True

	MAIL_USERNAME          = MAIL_USERNAME
	MAIL_PASSWORD          = MAIL_PASSWORD
	MAIL_DEFAULT_SENDER    = MAIL_DEFAULT_SENDER
