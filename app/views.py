from flask import render_template, flash, redirect, session, url_for, request, g, jsonify, send_file, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext
from datetime import datetime
# from guess_language import guess_language
from app import app, db, lm, oid, babel
from .forms import LoginForm, EditForm, PostForm, SearchForm, SignupForm
from .models import Users, Post, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers

from .confirm import send_email

from .apiview import handleApiPost, handleApiGet


from .historyController import renderHistory
import os.path
from sqlalchemy.sql.expression import func

@lm.user_loader
def load_user(id):
	return Users.query.get(int(id))


@babel.localeselector
def get_locale():
	return 'en'


@app.before_request
def before_request():
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
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(dummy_error):
	db.session.rollback()
	# print("500 error!")
	return render_template('500.html'), 500


def get_random_books():
	items = Series.query.order_by(func.random()).limit(4)
	# print(list(items))
	return items

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
# @login_required
def index(page=1):
	return render_template('index.html',
						   title='Home',
						   random_series=get_random_books(),
						   posts=[])


@app.route('/user/<nickname>/<int:page>')
@app.route('/user/<nickname>')
# @login_required
def user(nickname, page=1):
	user = Users.query.filter_by(nickname=nickname).first()
	if user is None:
		flash(gettext('User %(nickname)s not found.', nickname=nickname))
		return redirect(url_for('index'))
	posts = user.posts.paginate(page, app.config['POSTS_PER_PAGE'], False)
	return render_template('user.html',
						   user=user,
						   posts=posts)

@app.route('/series-id/<sid>/')
def renderSeriesId(sid):
	series       =       Series.query.filter(Series.id==sid).first()
	tags         =         Tags.query.filter(Tags.series==sid).all()
	genres       =       Genres.query.filter(Genres.series==sid).all()
	author       =       Author.query.filter(Author.series==sid).all()
	illustrators = Illustrators.query.filter(Illustrators.series==sid).all()
	releases     =     Releases.query.filter(Releases.series==sid).all()
	covers       =       Covers.query.filter(Covers.series==sid).all()


	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	return render_template('series-id.html',
						series_id       = sid,
						series       = series,
						tags         = tags,
						genres       = genres,
						author       = author,
						illustrators = illustrators,
						covers       = covers,
						releases     = releases)


@app.route('/author-id/<sid>/<int:page>')
@app.route('/author-id/<sid>/')
def renderAuthorId(sid, page=1):
	author = Author.query.filter(Author.id==sid).first()
	# print("Author search result: ", author)

	if author is None:
		flash(gettext('Author not found? This is probably a error!'))
		return redirect(url_for('renderAuthorTable'))

	items = Author.query.filter(Author.name==author.name).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('search_results.html',
						   sequence_item   = series_entries,
						   page            = page,
						   name_key        = "title",
						   page_url_prefix = 'series-id',
						   searchTarget    = 'Authors',
						   searchValue     = author.name
						   )

@app.route('/artist-id/<sid>/<int:page>')
@app.route('/artist-id/<sid>/')
def renderArtistId(sid, page=1):
	artist = Illustrators.query.filter(Illustrators.id==sid).first()
	# print("Artist search result: ", artist)

	if artist is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderArtistTable'))

	items = Illustrators.query.filter(Illustrators.name==artist.name).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('search_results.html',
						   sequence_item   = series_entries,
						   page            = page,
						   name_key        = "title",
						   page_url_prefix = 'series-id',
						   searchTarget    = 'Artists',
						   searchValue     = artist.name
						   )


@app.route('/tag-id/<sid>/<int:page>')
@app.route('/tag-id/<sid>/')
def renderTagId(sid, page=1):

	tag = Tags.query.filter(Tags.id==sid).first()

	if tag is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))

	# Look up the ascii value of the tag, and then find
	# all the links containing it.
	# Table is CITEXT, so we don't care about case.

	# this should REALLY have another indirection table.

	items = Tags.query.filter(Tags.tag==tag.tag).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return render_template('search_results.html',
						   sequence_item   = series_entries,
						   page            = page,
						   name_key        = "title",
						   page_url_prefix = 'series-id',
						   searchTarget    = 'Tags',
						   searchValue     = tag.tag
						   )


@app.route('/genre-id/<sid>/<int:page>')
@app.route('/genre-id/<sid>/')
def renderGenreId(sid, page=1):

	genre = Genres.query.filter(Genres.id==sid).first()

	if genre is None:
		flash(gettext('Genre not found? This is probably a error!'))
		return redirect(url_for('renderGenreTable'))

	# Look up the ascii value of the tag, and then find
	# all the links containing it.
	# Table is CITEXT, so we don't care about case.

	# this should REALLY have another indirection table.

	items = Genres.query.filter(Genres.genre==genre.genre).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return render_template('search_results.html',
						   sequence_item   = series_entries,
						   page            = page,
						   name_key        = "title",
						   page_url_prefix = 'series-id',
						   searchTarget    = 'Genres',
						   searchValue     = genre.genre
						   )

@app.route('/cover-img/<cid>')
def renderCoverImage(cid):
	cover = Covers.query.filter(Covers.id==cid).first()
	if not cover:
		flash(gettext('Cover not found!'))
		return redirect(url_for('index'))

	covpath = os.path.join(app.config['COVER_DIR_BASE'], cover.fspath)
	if not os.path.exists(covpath):
		flash(gettext('Cover file is missing!'))
		return redirect(url_for('index'))

	return send_file(covpath)



@app.route('/series/<letter>/<int:page>')
@app.route('/series/<page>')
@app.route('/series/<int:page>')
@app.route('/series/')
def renderSeriesTable(letter=None, page=1):
	if letter:
		series = Series.query                                \
			.filter(Series.title.like("{}%".format(letter))) \
			.order_by(Series.title)
	else:
		series = Series.query       \
			.order_by(Series.title)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('renderSeriesTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   name_key        = "title",
						   letter          = letter,
						   page_url_prefix = 'series-id',
						   title           = 'Book Titles')



@app.route('/authors/<letter>/<int:page>')
@app.route('/authors/<page>')
@app.route('/authors/<int:page>')
@app.route('/authors/')
def renderAuthorTable(letter=None, page=1):

	if letter:
		series = Author.query                                 \
			.filter(Author.name.like("{}%".format(letter))) \
			.order_by(Author.name)                          \
			.distinct(Author.name)
	else:
		series = Author.query       \
			.order_by(Author.name)\
			.distinct(Author.name)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('renderAuthorTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   name_key        = "author",
						   page_url_prefix = 'author-id',
						   title           = 'Authors')


@app.route('/artists/<letter>/<int:page>')
@app.route('/artists/<page>')
@app.route('/artists/<int:page>')
@app.route('/artists/')
def renderArtistTable(letter=None, page=1):

	if letter:
		series = Illustrators.query                                 \
			.filter(Illustrators.name.like("{}%".format(letter))) \
			.order_by(Illustrators.name)                          \
			.distinct(Illustrators.name)
	else:
		series = Illustrators.query       \
			.order_by(Illustrators.name)\
			.distinct(Illustrators.name)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('series'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   name_key        = "name",
						   page_url_prefix = 'artist-id',
						   title           = 'Artists')



@app.route('/tags/<letter>/<int:page>')
@app.route('/tags/<page>')
@app.route('/tags/<int:page>')
@app.route('/tags/')
def renderTagTable(letter=None, page=1):

	if letter:
		series = Tags.query                                 \
			.filter(Tags.tag.like("{}%".format(letter))) \
			.order_by(Tags.tag)                          \
			.distinct(Tags.tag)
	else:
		series = Tags.query       \
			.order_by(Tags.tag)\
			.distinct(Tags.tag)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('series'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   name_key        = "tag",
						   page_url_prefix = 'tag-id',
						   title           = 'Tags')


@app.route('/genres/<letter>/<int:page>')
@app.route('/genres/<page>')
@app.route('/genres/<int:page>')
@app.route('/genres/')
def renderGenreTable(letter=None, page=1):

	if letter:
		series = Genres.query                                \
			.filter(Genres.genre.like("{}%".format(letter))) \
			.order_by(Genres.genre)                          \
			.distinct(Genres.genre)
	else:
		series = Genres.query       \
			.order_by(Genres.genre) \
			.distinct(Genres.genre)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('series'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   name_key        = "genre",
						   page_url_prefix = 'genre-id',
						   title           = 'Genres')


@app.route('/history/<topic>/<int:srcId>')
def history_route(topic, srcId):
	return renderHistory(topic, srcId)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
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
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/about')
def about_site():
	return render_template('about.html')

@app.route('/user-cp')
def renderUserCp():
	return render_template('not-implemented-yet.html')

@app.route('/custom-lists')
def renderUserLists():
	return render_template('not-implemented-yet.html')

@app.route('/groups')
def renderGroups():
	return render_template('not-implemented-yet.html')

@app.route('/releases')
def renderReleases():
	return render_template('not-implemented-yet.html')


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
