from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext
from datetime import datetime
from guess_language import guess_language
from app import app, db, lm, oid, babel
from .forms import LoginForm, EditForm, PostForm, SearchForm
from .models import User, Post, Series
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, DATABASE_QUERY_TIMEOUT

from sqlalchemy.sql.expression import func

@lm.user_loader
def load_user(id):
	return User.query.get(int(id))


@babel.localeselector
def get_locale():
	return 'en'


@app.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()
	g.locale = get_locale()


@app.after_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= DATABASE_QUERY_TIMEOUT:
			app.logger.warning(
				"SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
				(query.statement, query.parameters, query.duration,
				 query.context))
	return response


@app.errorhandler(404)
def not_found_error(dummy_error):
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(dummy_error):
	db.session.rollback()
	return render_template('500.html'), 500


def get_random_books():
	items = Series.query.order_by(func.random()).limit(4)
	print(list(items))
	return items

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
# @login_required
def index(page=1):
	# form = PostForm()
	# if form.validate_on_submit():
	# 	language = guess_language(form.post.data)
	# 	if language == 'UNKNOWN' or len(language) > 5:
	# 		language = ''
	# 	post = Post(body=form.post.data, timestamp=datetime.utcnow(),
	# 				author=g.user, language=language)
	# 	db.session.add(post)
	# 	db.session.commit()
	# 	flash(gettext('Your post is now live!'))
	# 	return redirect(url_for('index'))
	# posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
	return render_template('index.html',
						   title='Home',
						   random_series=get_random_books(),
						   posts=[])


@oid.after_login
def after_login(resp):
	if resp.email is None or resp.email == "":
		flash(gettext('Invalid login. Please try again.'))
		return redirect(url_for('login'))
	user = User.query.filter_by(email=resp.email).first()
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		nickname = User.make_valid_nickname(nickname)
		nickname = User.make_unique_nickname(nickname)
		user = User(nickname=nickname, email=resp.email)
		db.session.add(user)
		db.session.commit()
		# make the user follow him/herself
		db.session.add(user.follow(user))
		db.session.commit()
	remember_me = False
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None)
	login_user(user, remember=remember_me)
	return redirect(request.args.get('next') or url_for('index'))


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
# @login_required
def user(nickname, page=1):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash(gettext('User %(nickname)s not found.', nickname=nickname))
		return redirect(url_for('index'))
	posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
	return render_template('user.html',
						   user=user,
						   posts=posts)

@app.route('/series/id/<sid>')
def renderSeriesId(sid):
	series = Series.query.filter_by(id=sid).first()
	print(dir(series))
	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	return render_template('series.html',
						   series=series)


@app.route('/series/<letter>/<int:page>')
@app.route('/series/<page>')
@app.route('/series/<int:page>')
@app.route('/series/')
def renderSeriesTable(letter=None, page=1):

	return render_template('allseries.html',
							page=page,
							letter=letter)


@app.route('/edit', methods=['GET', 'POST'])
# @login_required
def edit():
	form = EditForm(g.user.nickname)
	if form.validate_on_submit():
		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash(gettext('Your changes have been saved.'))
		return redirect(url_for('edit'))
	elif request.method != "POST":
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
	return render_template('edit.html', form=form)



@app.route('/search', methods=['POST'])
# @login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/search_results/<query>')
# @login_required
def search_results(query):
	results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
	return render_template('search_results.html',
						   query=query,
						   results=results)

