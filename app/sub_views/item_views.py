
from jinja2.filters import do_urlencode
from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask_babel import gettext
import werkzeug.exceptions
# from guess_language import guess_language
from app import app
from app import db

from app.models import Series
from app.models import Tags
from app.models import Feeds
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Releases
from app.models import Publishers
from app.models import Watches

from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import datetime
from natsort import natsort_keygen

from slugify import slugify

from app.series_tools import get_rating

from app.sub_views import wiki_views

def getChapterSort(row):
	chp = row.chapter   if row.chapter else 0
	vol = row.volume    if row.volume  else 0
	frg = row.fragment  if row.fragment  else 0
	return (vol * 1e6) + chp + (frg * 1e-6)

def getDateSort(row):
	return row.published

def build_progress(watch):

	progress = {}
	progress['vol'] = 0
	progress['chp'] = 0
	progress['frg'] = 0

	if watch:
		raw_vol = watch.volume   if watch.volume   != None else 0
		raw_chp = watch.chapter  if watch.chapter  != None else 0
		raw_frg = watch.fragment if watch.fragment != None else 0
		progress['vol'] = float(raw_vol)
		progress['chp'] = float(raw_chp)
		progress['frg'] = float(raw_frg)


	progress['vol'] = max(progress['vol'], 0)
	progress['chp'] = max(progress['chp'], 0)
	progress['frg'] = max(progress['frg'], 0)
	return progress

def get_latest_release(releases):

	if not releases:
		return None

	releases = [(
			release.volume   if release.volume   is not None else -1,
			release.chapter  if release.chapter  is not None else -1,
			release.fragment if release.fragment is not None else -1,
			release.id,  # row id is guaranteed unique, and should prevent the sort from ever reaching the release item
			release
			) for release in releases if release.include]
	releases.sort()

	if not releases:
		return None
	if not releases[-1]:
		return None

	latest = releases[-1][-1]


	return latest

def get_most_recent_release(releases):
	max_release = datetime.datetime.min
	for release in [item for item in releases if item.include]:
		if max_release < release.published:
			max_release = release.published
	return max_release

def format_latest_release(release):
	if release == None:
		return "none"
	vol  = release.volume
	chp  = release.chapter
	frag = release.fragment

	if vol == None:
		vol = -1

	ret = ''
	if vol > 0:
		ret += "vol. {}".format(vol)
	if chp:
		if len(ret) > 1:
			ret += ", "
		ret += "ch. {}".format(chp)
	if frag:
		ret += " pt. {}".format(frag)
	return ret

def get_cover_sorter():
	# Munge up the covers so they sort properly
	sorter = natsort_keygen(key=lambda x: str(x.description).replace('〈', '').replace('〉', ''))
	return sorter

def get_similar_by_tags(sid, taglist):
	'''
	Example query:
		SELECT p.*
		    FROM series p
		WHERE p.id IN (
		    SELECT
		        tg.series, COUNT(DISTINCT tg.tag)
		    FROM tags tg
		    WHERE tg.tag IN (
		        'world-travel',
		        'rape',
		        'popular-male-lead',
		        'politics-involving-royalty',
		        'parallel-dimension',
		        'otaku',
		        'older-female-younger-male',
		        'military',
		        'magic')
		    GROUP BY tg.series
		    ORDER BY
		        COUNT(DISTINCT tg.tag) DESC
		    LIMIT 10
		);
	'''

	count_metric = func.count(func.distinct(Tags.tag))
	query = select(
			[Series.title, Series.id],
			from_obj=[Series]
			).where(
				Series.id.in_(
					select(
						[Tags.series],
						from_obj=[Tags],
						order_by=desc(count_metric)
					).group_by(
						Tags.series
					).where(
						and_(
							Tags.tag.in_([tag.tag for tag in taglist[:100]]),
							Tags.series != sid
							)
					).limit(
						6
					)
				)
			)


	results = db.session.execute(query).fetchall()
	return results



def load_series_data(sid):
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
	series = series.options(joinedload('tags'))
	# series = series.options(joinedload('releases.translators'))

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
		return None

	releases = series.releases
	if series.sort_mode == 'chronological_order':
		releases.sort(reverse=True, key=getDateSort)
	else:
		releases.sort(reverse=True, key=getChapterSort)


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

	if series.tags:
		similar_series = get_similar_by_tags(sid, series.tags)
	else:
		similar_series = []


	return series, releases, watch, watchlists, progress, latest, latest_dict, most_recent, latest_str, rating, total_watches, similar_series

def get_author(sid):
	author = Author.query.filter(Author.id==sid).first()
	if not author:
		return None, None

	items = Author.query.filter(Author.name==author.name).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	return author, series
def get_artist(sid):
	artist = Illustrators.query.filter(Illustrators.id==sid).first()
	if not artist:
		return None, None


	items = Illustrators.query.filter(Illustrators.name==artist.name).all()
	ids = []
	for item in items:
		ids.append(item.series)


	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)

	return artist, series




def get_tag_id(sid, page=1):

	tag = Tags.query.filter(Tags.id==sid).first()

	if tag is None:
		return None, None


	items = Tags.query.filter(Tags.tag==tag.tag).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)
	return tag, series

def get_publisher_id(sid, page=1):

	pub = Publishers.query.filter(Publishers.id==sid).first()

	if pub is None:
		return None, None


	items = Publishers.query.filter(Publishers.name==pub.name).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)
	return pub, series

def get_genre_id(sid, page=1):

	genre = Genres.query.filter(Genres.id==sid).first()
	if genre is None:
		return None, None

	items = Genres.query.filter(Genres.genre==genre.genre).all()
	ids = []
	for item in items:
		ids.append(item.series)

	series = Series.query.filter(Series.id.in_(ids)).order_by(Series.title)
	return genre, series

@app.route('/series-id/<sid>/')
def renderSeriesIdWithoutSlug(sid):

	series       =       Series.query
	series = series.filter(Series.id==sid)
	series = series.first()
	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	return redirect(url_for("renderSeriesId", sid=sid, slug=slugify(series.title, to_lower=True)))



@app.route('/series-id-unread/<sid>/')
def renderLatestUnreadForSeriesId(sid):

	series       = Series.query
	series       = series.options(joinedload('releases'))
	series       = series.filter(Series.id==sid)
	series       = series.first()

	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	if not g.user.is_authenticated():
		flash(gettext('You need to be logged in so the system can track your latest read chapter in order for '
					+ 'unread shortcut links to be functional.'))
		return redirect(url_for("renderSeriesId", sid=sid, slug=slugify(series.title, to_lower=True)))


	watch      =       Watches.query.filter(Watches.series_id==sid)     \
	                                  .filter(Watches.user_id==g.user.id) \
	                                  .scalar()

	if not watch:
		flash(gettext('You need to be watching a series in so the system can track your latest read chapter to '
					+ 'make unread shortcut links functional.'))
		return redirect(url_for("renderSeriesId", sid=sid, slug=slugify(series.title, to_lower=True)))

	if series.sort_mode == "chronological_order":
		# In chronological order mode, we just sort by date only
		# TODO: Push sorting down to the DB query
		releases = [
		                (
		                    tmp.published,
		                    idx,
		                    tmp
		                 )
		             for
		                 idx, tmp
		             in
		                 enumerate(series.releases, 1)
		             if
		                 tmp.include
		            ]
		releases.sort()

		# Renumber with the correct sequential numbering.
		releases = [(tmp[0], idx, tmp[2]) for idx, tmp in enumerate(releases, 1)]

	else:   # only parsed_title_order at the moment.
		# we insert a incrementing count to prevent the possiblity of trying to order by
		# a Release item, since they're explicitly not orderable. Since `idx` will never be
		# the same, we can gaurantee we'll never hit the last item in the list
		releases = [
		                (
		                    tmp.volume   if tmp.volume   else 0,
		                    tmp.chapter  if tmp.chapter  else 0,
		                    tmp.fragment if tmp.fragment else 0,
		                    tmp.published,
		                    idx,
		                    tmp
		                 )
		             for
		                 idx, tmp
		             in
		                 enumerate(series.releases, 1)
		             if
		                 tmp.include
		            ]

		releases.sort()

	# Watch read-to value
	wv, wc, wf = watch.volume if watch.volume else 0, watch.chapter if watch.chapter else 0, watch.fragment if watch.fragment else 0
	# Handle special-case negagtive read values used to mask off values
	wv, wc, wf = max(0, wv), max(0, wc), max(0, wf)

	# print("Read progress:", (wv, wc, wf))
	# for release in releases:
	# 	print(release)

	for item in releases:
		rel = item[-1]
		idx = item[-2]

		# Release value
		rv, rc, rf = rel.volume   if rel.volume   else 0, rel.chapter   if rel.chapter   else 0, rel.fragment   if rel.fragment   else 0


		# # Clobber the chapter value in chrono mode.
		# if series.sort_mode == "chronological_order":
		# 	rc = idx

		# print("Item:", item)
		if (rv >= wv and rc >= wc and rf > wf) or (rv >= wv and rc > wc) or (rv > wv):
			if g.user.id == 2:
				return redirect('http://10.1.1.60:5001/view?url=%s' % do_urlencode(rel.srcurl))

			return redirect(rel.srcurl)



	flash(gettext('Could not determine what chapter to redirect you too. Sorry about that!'))

	return redirect(url_for("renderSeriesId", sid=sid, slug=slugify(series.title, to_lower=True)))



@app.route('/series-id/<sid>/<slug>')
def renderSeriesId(sid, slug):

	data = load_series_data(sid)
	if data is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	series, releases, watch, watchlists, progress, latest, latest_dict, most_recent, latest_str, rating, total_watches, similar_series = data

	# Check we're at the right slug url
	if slug != slugify(series.title, to_lower=True):
		return redirect(url_for("renderSeriesId", sid=sid, slug=slugify(series.title, to_lower=True)))

	if series.orig_status and "&lt;br&gt;" in series.orig_status:
		series.orig_status = series.orig_status.replace("&lt;br&gt;", ", ")
		db.session.commit()

	return render_template('series-id.html',
						series_id      = sid,
						series         = series,
						releases       = releases,
						watch          = watch,
						watchlists     = watchlists,
						progress       = progress,
						latest         = latest,
						latest_dict    = latest_dict,
						most_recent    = most_recent,
						latest_str     = latest_str,
						series_rating  = rating,
						total_watches  = total_watches,
						similar_series = similar_series,
						)


@app.route('/author-id/<sid>/<int:page>')
@app.route('/author-id/<sid>/')
def renderAuthorId(sid, page=1):
	author, series = get_author(sid)
	# print("Author search result: ", author)

	if author is None:
		flash(gettext('Author not found? This is probably a error!'))
		return redirect(url_for('renderAuthorTable'))

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

	artist, series = get_artist(sid)
	# print("Artist search result: ", artist)

	if artist is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderArtistTable'))

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

	tag, series = get_tag_id(sid)

	if tag is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))

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

	pub, series = get_publisher_id(sid)

	if pub is None:
		flash(gettext('Tag not found? This is probably a error!'))
		return redirect(url_for('renderTagTable'))

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

	genre, series = get_genre_id(sid)

	if genre is None:
		flash(gettext('Genre not found? This is probably a error!'))
		return redirect(url_for('renderGenreTable'))


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



# @app.route('/feeds/source/<source>/<page>')
# @app.route('/feeds/source/<source>/<int:page>')
# @app.route('/feeds/source/<source>/')
# def renderFeedsSourceTable(source, page=1):
# 	feeds = Feeds.query                   \
# 		.filter(Feeds.srcname == source)  \
# 		.order_by(desc(Feeds.published))


# 	feeds = feeds.options(joinedload('tags'))
# 	feeds = feeds.options(joinedload('authors'))

# 	if feeds is None:
# 		flash(gettext('No feeds? Something is /probably/ broken!.'))
# 		return redirect(url_for('renderFeedsTable'))

# 	feed_entries = feeds.paginate(page, app.config['SERIES_PER_PAGE'])

# 	return render_template('feeds.html',
# 						   subheader = "Source = '%s'" % source,
# 						   sequence_item   = feed_entries,
# 						   page            = page,
# 						   chunk           = True
# 						   )


def get_group_id(sid, page):

	group = Translators.query.filter(Translators.id==sid).scalar()
	if group is None:
		return None, None, None, None, None


	names = [tmp.name for tmp in group.alt_names]

	feeds = Feeds.query.options(joinedload('tags')) \
		.filter(Feeds.srcname.in_(names))            \
		.order_by(desc(Feeds.published))

	items_raw = Releases.query.filter(Releases.tlgroup==group.id).order_by(desc(Releases.published))


	subq = Releases.query.with_entities(Releases.series.distinct()).filter(Releases.tlgroup==group.id)

	seriesq = Series.query.filter(Series.id.in_(subq)).order_by(Series.title)

	series = seriesq.all()

	return group, names, feeds, items_raw, series

@app.route('/group-id/<sid>/<int:page>')
@app.route('/group-id/<sid>/')
def renderGroupId(sid, page=1):

	group, names, feeds, items_raw, series = get_group_id(sid, page)


	if group is None:
		flash(gettext('Group/Translator not found? This is probably a error!'))
		return redirect(url_for('renderGroupsTable'))

	try:
		feed_entries = feeds.paginate(page, app.config['SERIES_PER_PAGE'])
	except werkzeug.exceptions.NotFound:
		feed_entries = None
	try:
		items = items_raw.paginate(page, app.config['SERIES_PER_PAGE'])
	except werkzeug.exceptions.NotFound:
		items = None


	return render_template('group.html',
						   series                 = series,
						   releases_sequence_item = items,
						   feed_sequence_item     = feed_entries,
						   group                  = group,
						   wiki                   = wiki_views.render_wiki("Group", group.name)
						   )

