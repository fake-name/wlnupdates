from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask import request
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app

from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Releases
from app.models import Publishers
from app.models import Watches

from sqlalchemy import desc
from natsort import natsort_keygen
from sqlalchemy.orm import joinedload
import datetime

from app.series_tools import get_rating

from app.sub_views import wiki_views

def getSort(row):
	chp = row.chapter if row.chapter else 0
	vol = row.volume  if row.volume  else 0
	return vol * 1e6 + chp

def build_progress(watch):

	progress = {}
	progress['vol'] = 0
	progress['chp'] = 0
	progress['frg'] = 0

	if watch:
		raw_vol = watch.volume  if watch.volume  != None else 0
		raw_chp = watch.chapter if watch.chapter != None else 0
		progress['vol'] = raw_vol
		progress['chp'] = int(raw_chp)
		progress['frg'] = int(raw_chp * 100) % 100


	progress['vol'] = max(progress['vol'], 0)
	progress['chp'] = max(progress['chp'], 0)
	progress['frg'] = max(progress['frg'], 0)

	return progress

def get_latest_release(releases):
	max_vol = 0
	max_chp = 0
	max_release = None
	for release in [item for item in releases if item.include]:

		if release.volume and release.volume > max_vol:
			max_vol = release.volume
			max_chp = release.chapter
			max_release = release
		elif release.volume and release.chapter and release.volume >= max_vol and release.chapter >= max_chp:
			max_vol = release.volume
			max_chp = release.chapter
			max_release = release

		elif not release.volume and not max_vol and release.chapter and release.chapter >= max_chp:
			max_chp = release.chapter
			max_release = release
	return max_release

def get_most_recent_release(releases):
	max_release = datetime.datetime.min
	for release in [item for item in releases if item.include]:
		if max_release < release.published:
			max_release = release.published
	return max_release

def format_latest_release(release):
	if release == None:
		return "none"
	vol = release.volume
	chp = release.chapter

	if vol == None:
		vol = -1

	ret = ''
	if vol > 0:
		ret += "vol. {}".format(vol)
	if chp:
		if len(ret) > 1:
			ret += ", "
		ret += "ch. {}".format(chp)
	return ret

def get_cover_sorter():
	# Munge up the covers so they sort properly
	sorter = natsort_keygen(key=lambda x: str(x.description).replace('〈', '').replace('〉', ''))
	return sorter


@app.route('/series-id/<sid>/')
def renderSeriesId(sid):
	series       =       Series.query

	# Adding these additional joinedload values, while they /should/
	# help, since the relevant content is then loaded during rendering
	# if they're not already loaded, somehow manages to COMPLETELY
	# tank the query performance.
	# series = series.options(joinedload('tags'))
	# series = series.options(joinedload('genres'))
	# series = series.options(joinedload('covers'))

	series = series.options(joinedload('author'))
	series = series.options(joinedload('alternatenames'))
	series = series.options(joinedload('illustrators'))
	series = series.options(joinedload('releases.translators'))

	series = series.filter(Series.id==sid)

	series = series.first()

	if g.user.is_authenticated():
		watch      =       Watches.query.filter(Watches.series_id==sid)     \
		                                  .filter(Watches.user_id==g.user.id) \
		                                  .scalar()

		# This is *relatively* optimized, since the query
		# planner is smart enough to apply the filter before the distinct.
		# May become a performance issue if the watches table gets large
		# enough, but I think the performance ceiling will actually
		# be the number of watches a user has, rather then the
		# overall table size.
		watchlists = Watches                                 \
					.query                                   \
					.filter(Watches.user_id == g.user.id)    \
					.distinct(Watches.listname)              \
					.all()
		watchlists = [watchitem.listname for watchitem in watchlists]
		# print(watchlists)
	else:
		watch = False
		watchlists = False



	total_watches =       Watches.query.filter(Watches.series_id==sid).count()

	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	releases = series.releases
	releases.sort(reverse=True, key=getSort)


	latest      = get_latest_release(releases)
	latest_dict = build_progress(latest)
	most_recent = get_most_recent_release(releases)
	latest_str  = format_latest_release(latest)

	if watch:
		progress    = build_progress(watch)
	else:
		progress    = latest_dict

	series.covers.sort(key=get_cover_sorter())

	rating = get_rating(sid)





	return render_template('series-id.html',
						series_id     = sid,
						series        = series,
						releases      = releases,
						watch         = watch,
						watchlists    = watchlists,
						progress      = progress,
						latest        = latest,
						latest_dict   = latest_dict,
						most_recent   = most_recent,
						latest_str    = latest_str,
						series_rating = rating,
						total_watches = total_watches,
						)


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
						   searchValue     = author.name,
						   wiki            = wiki_views.render_wiki("Author", author.name)
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
						   searchValue     = artist.name,
						   wiki            = wiki_views.render_wiki("Artist", artist.name)
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
						   searchValue     = tag.tag,
						   wiki            = wiki_views.render_wiki("Tag", tag.tag)
						   )

@app.route('/publisher-id/<sid>/<int:page>')
@app.route('/publisher-id/<sid>/')
def renderPublisherId(sid, page=1):

	pub = Publishers.query.filter(Publishers.id==sid).first()

	if pub is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))

	# Look up the ascii value of the tag, and then find
	# all the links containing it.
	# Table is CITEXT, so we don't care about case.

	# this should REALLY have another indirection table.

	items = Publishers.query.filter(Publishers.name==pub.name).all()
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
						   searchTarget    = 'Publishers',
						   searchValue     = pub.name,
						   wiki            = wiki_views.render_wiki("Publisher", pub.name)
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
						   searchValue     = genre.genre,
						   wiki            = wiki_views.render_wiki("Genre", genre.genre)
						   )


@app.route('/group-id/<sid>/')
def renderGroupId(sid):

	group = Translators.query.filter(Translators.id==sid).scalar()

	if group is None:
		flash(gettext('Group/Translator not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))


	items = Releases.query.filter(Releases.tlgroup==group.id).order_by(desc(Releases.published)).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title).all()

	return render_template('group.html',
						   series   = series,
						   releases = items,
						   group    = group
						   )

