import os
from flask import Flask
from flask.json import JSONEncoder
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.mail import Mail
from flask.ext.babel import Babel, lazy_gettext
from flask_wtf.csrf import CsrfProtect
from config import basedir # , ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD

app = Flask(__name__)
app.config.from_object('config.BaseConfig')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = lazy_gettext('Please log in to access this page.')
oid = OpenID(app, os.path.join(basedir, 'tmp'))
mail = Mail(app)
babel = Babel(app)
CsrfProtect(app)

if not app.debug:
	import logging
	from logging.handlers import RotatingFileHandler
	file_handler = RotatingFileHandler('tmp/wlnupdates.log', 'a', 1 * 1024 * 1024, 10)
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(logging.Formatter(
		'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
	app.logger.addHandler(file_handler)
	app.logger.setLevel(logging.INFO)
	app.logger.info('wlnupdates startup')


from app import views, models
from .views import Users

idCache = {}

@app.context_processor
def utility_processor():
	def getUserId(idNo):
		if idNo in idCache:
			return idCache[idNo]
		user = Users.query.filter_by(id=idNo).one()
		idCache[user.id] = user.nickname

		# Truncate the cache if it's getting too large
		if len(idCache) > 500:
			idCache.popitem()

		return idCache[user.id]
	return dict(getUserId=getUserId)

def format_price(amount, currency=u'€'):
	return u'{0:.2f}{1}'.format(amount, currency)

