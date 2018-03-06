
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from sqlalchemy.sql.expression import nullslast
from app.models import AlternateNames
from app.models import CommonTags
from app.models import CommonGenres
from app.models import Tags
from app.models import Genres
from app.models import Series
from app.models import Releases
from app.models import Watches
import app.nameTools as nt
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc, distinct

from app import app
from app import db
import collections
import json

def generate_similarity_query(searchterm, cols=None):

	searchtermclean = bleach.clean(searchterm, strip=True)
	searchtermprocessed = nt.prepFilenameForMatching(searchtermclean)

	similarity = Function('similarity', AlternateNames.cleanname, (searchtermprocessed))
	if cols is None:
		cols = [AlternateNames.series, AlternateNames.cleanname, AlternateNames.name, similarity]

	if not searchterm:
		return None, None

	query = select(
			cols,
			from_obj=[AlternateNames],
			order_by=desc(similarity)
		).where(
			or_(
				AlternateNames.cleanname.op("%%")(searchtermprocessed),
				AlternateNames.cleanname.like(searchtermprocessed + "%%")
				)
		).limit(
			50
		)
	return query, searchtermprocessed

def add_similarity_query(searchterm, query):

	searchtermclean = bleach.clean(searchterm, strip=True)
	searchtermprocessed = nt.prepFilenameForMatching(searchtermclean)

	similarity = Function('similarity', AlternateNames.cleanname, (searchtermprocessed))

	if not searchterm:
		return None, None

	query = query.filter(
		Series.id.in_(
			db.session.query(AlternateNames.series).filter(
				or_(
					AlternateNames.cleanname.op("%%")(searchtermprocessed),
					AlternateNames.cleanname.like(searchtermprocessed + "%%")
					)
				).order_by(
					desc(similarity)
				)
			)
		)

	return query

def title_search(searchterm):
	query, searchtermprocessed = generate_similarity_query(searchterm)
	results = db.session.execute(query).fetchall()

	data = collections.OrderedDict()

	uid = g.user.get_id()
	for result in results:
		dbid = result[0]
		if not dbid in data:
			data[dbid] = {}
			data[dbid]['row'] = Series.query.filter(Series.id==dbid).one()
			if uid:
				data[dbid]['watch'] = Watches            \
						.query                           \
						.filter(Watches.series_id==dbid) \
						.filter(Watches.user_id==uid)    \
						.scalar()
			else:
				data[dbid]['watch'] = []

			data[dbid]['results'] = []
		# We only care about relative ordering, and
		# since we're ordered when we iterate, if we
		# just append here, things will stay in the correct
		# order.
		data[dbid]['results'].append(result)

	return data, searchtermprocessed

def do_advanced_search(params, queried_columns=None):

	if queried_columns:
		print("Queried columns overridden: ", queried_columns)
		queried_columns = list(queried_columns)
	else:
		queried_columns = (Series.id, Series.title, Series.latest_published, Series.release_count)

	q = db.session.query(*queried_columns).group_by(Series.id)

	# q = q.join(Releases)
	# q = q.filter(Releases.series == Series.id)

	if 'tag-category' in params:
		q = q.join(Tags)
		for text, mode in params['tag-category'].items():
			if mode == "included":
				q = q.filter(Tags.tag == str(text))
			elif mode == 'excluded':
				q = q.filter(Tags.tag != str(text))

	if 'genre-category' in params:
		q = q.join(Genres)
		for text, mode in params['genre-category'].items():
			if mode == "included":
				q = q.filter(Genres.genre == str(text))
			elif mode == 'excluded':
				q = q.filter(Genres.genre != str(text))


	if 'title-search-text' in params and params['title-search-text']:
		searchterm = params['title-search-text']
		q = add_similarity_query(searchterm, q)


	if 'chapter-limits' in params:
		if len(params['chapter-limits']) == 2:
			minc, maxc = params['chapter-limits']
			minc = int(minc)
			maxc = int(maxc)
			params['chapter-limits'] = [minc, maxc]
			if minc > 0:
				q = q.having(Series.release_count >= minc)
			if maxc > 0:
				q = q.having(Series.release_count <= maxc)

	type_map = {
		'Translated'                : 'translated',
		'Original English Language' : 'oel',
	}

	if 'series-type' in params:
		ops = []
		for key, value in params['series-type'].items():
			if key in type_map:
				if value == 'included':
					ops.append((Series.tl_type == type_map[key]))
				elif value == 'excluded':
					ops.append((Series.tl_type != type_map[key]))
				else:
					print("wut?")
		if ops:
			q = q.filter(and_(*ops))

	if "sort-mode" in params:

		if params['sort-mode'] == "update":
			q = q.order_by(nullslast(desc(Series.latest_published)))
		elif params['sort-mode'] == "chapter-count":
			q = q.order_by(nullslast(desc(Series.release_count)))
		else: # params['sort-mode'] == "name"
			q = q.order_by(Series.title)
	else:
		q = q.order_by(Series.title)

	return q


def search_check_ok(params):
	if (
				'chapter-limits' in params
			and
			(
					len(params['chapter-limits']) != 2
				or
					int(params['chapter-limits'][0]) < 0
			)
		):
		print("chapter limits invalid", len(params['chapter-limits']) != 2, int(params['chapter-limits'][0]) < 0)
		return False

	have_filter = False
	# Require at least one filter parameter
	have_filter |= 'tag-category'      in params and len(params['tag-category'])      > 0
	have_filter |= 'genre-category'    in params and len(params['genre-category'])    > 0
	have_filter |= 'series-type'       in params and len(params['series-type'])       > 0
	have_filter |= 'title-search-text' in params and len(params['title-search-text'].strip()) >= 2

	return have_filter



@app.route('/ajax-search', methods=['POST'])
def ajax_search():
	print("Ajax search!")
	if search_check_ok(request.json):
		series_query = do_advanced_search(request.json)
		series_query = series_query.limit(100)
		series = series_query.all()

		return render_template('ajax-search.html', series=series)
	else:
		return render_template('__block_blurb.html', message="You have to provide some search parameters!")

def render_search_page(search):

	if 'json' in request.args:
		args = json.loads(request.args['json'])


		if search_check_ok(args):
			series = do_advanced_search(args)
			return render_template('advanced-search-results.html',
				series = series,
				search_params = args
				)
		else:
			return render_template('not-implemented-yet.html', message="You have to provide some search parameters!")
	else:
		return render_template('not-implemented-yet.html', message="This endpoint requires json post data!")


def get_tags():
	results = CommonTags.query                 \
		.order_by(CommonTags.tag)              \
		.all()
	return results

def get_genres():
	results = CommonGenres.query                 \
		.order_by(CommonGenres.genre)              \
		.all()
	return results


def execute_search():
	# Flatten the passed dicts.
	# This means that multiple identical parameters
	# /WILL/ clobber each other in a non-determinsic manner,
	# but that's not needed for search anyways, so I want
	# to disabiguate.
	searchd = {}
	searchd.update(dict(request.args.items()))
	searchd.update(dict(request.form.items()))

	common_searches = 25

	if 'title' in searchd:
		data, searchtermclean = title_search(searchd['title'])
		if not searchtermclean:
			return render_template('not-implemented-yet.html', message='No search term entered (or search term collapsed down to nothing).')

		return render_template('text-search.html',
						   results         = data,
						   name_key        = "tag",
						   page_url_prefix = 'tag-id',
						   searchTarget    = "Titles",
						   searchValue     = searchtermclean,
						   title           = 'Search for \'{name}\''.format(name=searchtermclean))

	elif 'json' in request.args:
		args = json.loads(request.args['json'])


		if search_check_ok(args):
			series_query = do_advanced_search(args)
			series_query = series_query.limit(100)
			series = series_query.all()

			return render_template('advanced-search-results.html',
				series = series,
				search_params = args
				)
		else:
			return render_template('not-implemented-yet.html', message="You have to provide some search parameters!")


	else:
		print("Render search page call!")
		tag_results = get_tags()
		genre_results = get_genres()

		common_tags, rare_tags = [], []
		for item in tag_results:
			if item.tag_instances >= 25:
				common_tags.append(item)
			else:
				rare_tags.append(item)

		common_genres, rare_genres = [], []
		for item in genre_results:
			if item.genre_instances >= 25:
				common_genres.append(item)
			else:
				rare_genres.append(item)

		return render_template('advanced-search.html',
			common_tags   = common_tags,
			rare_tags     = rare_tags,
			common_genres = common_genres,
			rare_genres   = rare_genres,
			common_thresh = common_searches
			)



# @login_required
@app.route('/search', methods=['GET', 'POST'])
def search():
	return execute_search()
