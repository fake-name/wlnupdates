import os
from flask import Flask
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel, lazy_gettext
from flask_wtf.csrf import CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension
from config import basedir
import datetime
from babel.dates import format_datetime
from babel.dates import get_timezone
from flask_assets import Bundle
from flask_assets import Environment

import urllib.parse

class AnonUser():
	def is_authenticated(self):
		return False
	def is_active(self):
		return False
	def is_admin(self):
		return False
	def is_mod(self):
		return False
	def is_anonymous(self):
		return True
	def get_id(self):
		return None


app = Flask(__name__, static_folder='static', static_url_path='/static')

import sys
if "debug" in sys.argv:
	print("Flask running in debug mode!")
	app.debug = True
app.config.from_object('config.BaseConfig')
app.jinja_env.add_extension('jinja2.ext.do')
db = SQLAlchemy(app)
lm = LoginManager()
lm.anonymous_user = AnonUser
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = 'Please log in to access this page.'
mail = Mail(app)
babel = Babel(app)
csrf = CSRFProtect(app)

if "debug" in sys.argv:
	print("Installing debug toolbar!")
	toolbar = DebugToolbarExtension(app)

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



# ========================================================
# Forum
# ========================================================

assets = Environment(app)

jerberscript = Bundle(
		"js/jquery-latest.min.js",
		"js/bootstrap.min.js",
		"js/jquery.contextMenu.js",
		"js/jquery.datetimepicker.js",
		"js/editable.js",
		filters='jsmin',
		output='gen/jerberscript.js'
	)

assets.register('all_jerberscript', jerberscript)

darkside_css = Bundle(
	'css/bootstrap_dark.css',
	filters='cssmin',
	output='gen/darkside_css.css'
	)

lightside_css = Bundle(
	'css/bootstrap_light.css',
	filters='cssmin',
	output='gen/lightside_css.css'
	)

css_common = Bundle(
	'css/custom.css',
	'css/jquery.contextMenu.css',
	'css/jquery.datetimepicker.css',
	filters='cssmin',
	output='gen/stylin.css'
	)

assets.register('darkside_css',  darkside_css)
assets.register('lightside_css', lightside_css)
assets.register('most_css',      css_common)

import forum.forum.views as forum
app.register_blueprint(forum.bp, url_prefix='/forum')

# Admin
# from forum import admin
# admin.attach_admin(app)

from util import urlify
from flaskext.markdown import Markdown
Markdown(app, safe_mode='escape', extensions=[urlify.URLifyExtension()])

# ========================================================


from app import views, models

from . import context_processors



