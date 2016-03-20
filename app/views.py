from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import request
from flask import g
from flask import send_file
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import BadSignature
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext
from datetime import datetime
# from guess_language import guess_language
from app import app
from app import db
from app import lm
from app import babel
from .forms import  LoginForm, SearchForm, SignupForm
from .models import Users
from .models import News_Posts
from .models import Series
from .models import Releases
from .models import Covers
from .models import Feeds
from .models import HttpRequestLog

from .confirm import send_email



import os.path
from sqlalchemy.sql.expression import func
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

# These imports /look/ unused, but they cause the installation
# of most of the site routes.
from .sub_views import item_views
from .sub_views import stub_views
from .sub_views import user_views
from .sub_views import admin_views
from .sub_views import add
from .sub_views import sequence_views
from .sub_views import release_views
from .sub_views import series_views
from .sub_views import history_view
from .sub_views import cover_edit_view
from .sub_views import news_view
from .sub_views import popular_views
from .sub_views.search import execute_search

from .apiview import handleApiPost
from .apiview import handleApiGet


import traceback

@lm.user_loader
def load_user(id):
	return Users.query.get(int(id))


@babel.localeselector
def get_locale():
	return 'en'


@app.before_request
def before_request():
	req = HttpRequestLog(
		path           = request.path,
		user_agent     = request.headers.get('User-Agent'),
		referer        = request.headers.get('Referer'),
		forwarded_for  = request.headers.get('X-Originating-IP'),
		originating_ip = request.headers.get('X-Forwarded-For'),
		)
	db.session.add(req)

	g.user = current_user
	g.search_form = SearchForm()
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)

	db.session.commit()
	g.locale = get_locale()



@app.after_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= app.config['DATABASE_QUERY_TIMEOUT']:
			app.logger.warning(
				"SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
				(query.statement, query.parameters, query.duration,
				 query.context))
	return response


@app.errorhandler(404)
def not_found_error(dummy_error):
	print("404. Wat?")
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(dummy_error):
	db.session.rollback()
	print("Internal Error!")
	print(dummy_error)
	print(traceback.format_exc())
	# print("500 error!")
	return render_template('500.html'), 500



def get_random_books():
	items = Series.query.order_by(func.random()).limit(5)
	return items


def get_news():
	# User ID 2 is the admin acct, as created by the db migrator script
	# Probably shouldn't be hardcoded, works for the moment.
	newsPost = News_Posts.query.filter(News_Posts.user_id == 2).order_by(desc(News_Posts.timestamp)).limit(1).one()
	return newsPost

def get_raw_feeds(limit=20):
	raw_feeds = Feeds.query              \
		.options(joinedload('tags'))     \
		.options(joinedload('authors'))  \
		.order_by(desc(Feeds.published)) \
		.limit(20)                       \
		.all()
	if raw_feeds:
		tmp = raw_feeds[0]

	return raw_feeds

def get_release_feeds(srctype=None):
	q = Releases.query
	if srctype:
		q = q.filter(Releases.series_row.has(tl_type = srctype))

	q = q.order_by(desc(Releases.published))
	q = q.options(joinedload('series_row'))
	q = q.options(joinedload('translators'))
	q = q.limit(20)

	return q.all()


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
# @login_required
def index(page=1):
	return render_template('index.html',
						   title               = 'Home',
						   random_series       = get_random_books(),
						   news                = get_news(),
						   raw_feeds           = get_raw_feeds(),
						   oel_release_items   = get_release_feeds(srctype='oel'),
						   trans_release_items = get_release_feeds(srctype='translated'),
						   )


@app.route('/user/<nickname>/<int:page>')
@app.route('/user/<nickname>')
# @login_required
def user(nickname, page=1):
	user = Users.query.filter_by(nickname=nickname).first()
	if user is None:
		flash(gettext('User %(nickname)s not found.', nickname=nickname))
		return redirect(url_for('index'))
	posts = user.news_posts.paginate(page, app.config['POSTS_PER_PAGE'], False)
	return render_template('user.html',
						   user=user,
						   posts=posts)



@app.route('/cover-img/<cid>')
def renderCoverImage(cid):
	# TODO: Add a "not found" image
	cover = Covers.query.filter(Covers.id==cid).first()
	if not cover:
		flash(gettext('Cover not found in database! Wat?'))
		return redirect(url_for('index'))

	covpath = os.path.join(app.config['COVER_DIR_BASE'], cover.fspath)
	if not os.path.exists(covpath):
		print("Cover not found! '%s'" % covpath)
		flash(gettext('Cover file is missing!'))
		return redirect(url_for('index'))

	return send_file(
		covpath,
		conditional=True
		)


@app.route('/favicon.ico')
def sendFavIcon():
	return send_file(
		"./static/favicon.ico",
		conditional=True
		)




# @app.route('/edit', methods=['GET', 'POST'])
# @login_required
# def edit():
# 	form = EditForm(g.user.nickname)
# 	if form.validate_on_submit():
# 		g.user.nickname = form.nickname.data
# 		g.user.about_me = form.about_me.data
# 		db.session.add(g.user)
# 		db.session.commit()
# 		flash(gettext('Your changes have been saved.'))
# 		return redirect(url_for('edit'))
# 	elif request.method != "POST":
# 		form.nickname.data = g.user.nickname
# 		form.about_me.data = g.user.about_me
# 	return render_template('edit.html', form=form)





#################################################################################################################################
#################################################################################################################################
#################################################################################################################################
#################################################################################################################################

@app.route('/logout', methods=['GET', 'POST'])
def logout():
	logout_user()
	flash(gettext('You have been logged out.'))
	return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if g.user is not None and g.user.is_authenticated():
		flash(gettext('You are already logged in.'))
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(nickname=form.username.data).first()
		if user.verified:
			login_user(user, remember=bool(form.remember_me.data))
			flash(gettext('You have logged in successfully.'))
			return redirect(url_for('index'))
		else:
			flash(gettext('Please confirm your account first.'))
			return redirect(url_for('index'))


	return render_template('login.html',
						   title='Sign In',
						   form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))
	form = SignupForm()
	if form.validate_on_submit():
		user = Users(
			nickname  = form.username.data,
			password  = form.password.data,
			email     = form.email.data,
			verified  = 0
		)
		print("User:", user)
		db.session.add(user)
		db.session.commit()
		send_email(form.email.data,
				"Please confirm your account for WLNUpdates.com",
				render_template('mail.html',
								confirm_url=get_activation_link(user))
				)

		print("Sent")

		return render_template('confirm.html')


		# session['remember_me'] = form.remember_me.data
	return render_template('signup.html',
						   title='Sign In',
						   form=form)



def get_serializer():
	return URLSafeTimedSerializer(app.config['SECRET_KEY'])


def get_activation_link(user):
	s = get_serializer()
	payload = s.dumps(user.id, salt=app.config['SECURITY_PASSWORD_SALT'])
	return url_for('activate_user', payload=payload, _external=True)

@app.route('/users/activate/<payload>')
def activate_user(payload, expiration=60*60*24):
	s = get_serializer()
	try:
		user_id = s.loads(payload, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
		user = Users.query.get(int(user_id))
		if user.verified:
			flash(gettext('Your account has already been activated. Stop that.'))
		else:
			user.verified = 1
			db.session.commit()
			flash(gettext('Your account has been activated. Please log in.'))
		return index(1)

	except BadSignature:
		return render_template('not-implemented-yet.html', message='Invalid activation link.')
