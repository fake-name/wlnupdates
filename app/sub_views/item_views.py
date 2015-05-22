from flask import render_template, flash, redirect, session, url_for, request, g, jsonify, send_file, abort
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app, db, lm, babel

from app.models import Users, Posts, Series, Tags, Genres, Author
from app.models import Illustrators, Translators, Releases, Covers, Watches, AlternateNames
from app.models import Feeds, Releases

from app.confirm import send_email

from app.apiview import handleApiPost, handleApiGet

from app.sub_views.search import execute_search

from app.historyController import renderHistory
import os.path
from sqlalchemy.sql.expression import func
from sqlalchemy import desc

import traceback



@app.route('/series-id/<sid>/')
def renderSeriesId(sid):
	series       =       Series.query.filter(Series.id==sid).first()


	if g.user.is_authenticated():
		watches      =       Watches.query.filter(Watches.series_id==sid)     \
		                                  .filter(Watches.user_id==g.user.id) \
		                                  .scalar()
	else:
		watches = False



	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	return render_template('series-id.html',
						series_id    = sid,
						series       = series,
						watches      = watches)


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


@app.route('/group-id/<sid>/<int:page>')
@app.route('/group-id/<sid>/')
def renderGroupId(sid, page=1):

	group = Translators.query.filter(Translators.id==sid).scalar()

	if group is None:
		flash(gettext('Group/Translator not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))


	items = Releases.query.filter(Releases.tlgroup==group.id).all()
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
						   searchTarget    = 'Translation Groups',
						   searchValue     = group.group_name
						   )

