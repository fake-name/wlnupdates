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
			.order_by(Author.name) \
			.distinct(Author.name)
	if series is None:
		flash(gettext('No series items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('renderAuthorTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   path_name       = "authors",
						   name_key        = "name",
						   page_url_prefix = 'author-id',
						   title           = 'Authors',
						   # add_new         = 'author',
						   # add_new_text    = 'Add a Author',
						   )


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
		return redirect(url_for('renderArtistTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   path_name       = "artists",
						   name_key        = "name",
						   page_url_prefix = 'artist-id',
						   title           = 'Artists',
						   # add_new         = 'artist',
						   # add_new_text    = 'Add a Artist',

						   )



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
		flash(gettext('No tag items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('renderTagTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   path_name       = 'tags',
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
		flash(gettext('No genre items with a prefix of {prefix} found.'.format(prefix=letter)))
		return redirect(url_for('renderGenreTable'))
	series_entries = series.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('sequence.html',
						   sequence_item   = series_entries,
						   page            = page,
						   letter          = letter,
						   path_name       = "genres",
						   name_key        = "genre",
						   page_url_prefix = 'genre-id',
						   title           = 'Genres')



@app.route('/releases/<page>')
@app.route('/releases/<int:page>')
@app.route('/releases/')
def renderReleasesTable(page=1):

	releases = Releases.query       \
		.order_by(desc(Releases.published))

	if releases is None:
		flash(gettext('No releases? Something is /probably/ broken!.'))
		return redirect(url_for('renderReleasesTable'))

	releases_entries = releases.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('releases.html',
						   sequence_item   = releases_entries,
						   page            = page)



@app.route('/groups/<page>')
@app.route('/groups/<int:page>')
@app.route('/groups/')
def renderGroupsTable(page=1):

	groups = Translators.query       \
		.order_by(Translators.name)

	if groups is None:
		flash(gettext('No Translators? Something is /probably/ broken!.'))
		return redirect(url_for('renderGroupsTable'))

	groups_entries = groups.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('groups.html',
						   sequence_item   = groups_entries,
						   page            = page,
						   add_new         = 'group',
						   add_new_text    = 'Add a Group',
						   )


@app.route('/feeds/<page>')
@app.route('/feeds/<int:page>')
@app.route('/feeds/')
def renderFeedsTable(page=1):

	feeds = Feeds.query       \
		.order_by(desc(Feeds.published))

	if feeds is None:
		flash(gettext('No feeds? Something is /probably/ broken!.'))
		return redirect(url_for('renderFeedsTable'))

	feed_entries = feeds.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('feeds.html',
						   sequence_item   = feed_entries,
						   page            = page
						   )