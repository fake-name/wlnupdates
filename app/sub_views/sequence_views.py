from flask import render_template
from flask import flash
from flask import redirect
from flask import session
from flask import url_for
from flask import request
from flask import g
from flask import jsonify
from flask import send_file
from flask import abort
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app
from app import db
from app import babel

from app.models import Users
from app.models import News_Posts
from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Releases
from app.models import Covers
from app.models import Watches
from app.models import AlternateNames
from app.models import Feeds
from app.models import Releases

from app.confirm import send_email

from app.apiview import handleApiPost
from app.apiview import  handleApiGet

from app.sub_views.search import execute_search

from app.historyController import renderHistory
import os.path
from sqlalchemy.sql.expression import func
from sqlalchemy import desc

from sqlalchemy.orm import joinedload
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


	feeds = feeds.options(joinedload('tags'))
	feeds = feeds.options(joinedload('authors'))



	if feeds is None:
		flash(gettext('No feeds? Something is /probably/ broken!.'))
		return redirect(url_for('renderFeedsTable'))

	feed_entries = feeds.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('feeds.html',
						   sequence_item   = feed_entries,
						   page            = page
						   )