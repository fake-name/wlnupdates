
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
from app.models import CommonTags
from app.models import Series
from app.models import Releases
from app.models import Watches
import app.nameTools as nt
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc

from app import db
from app import app
import collections
import json

def title_search(searchterm, page=1):
	searchtermclean = bleach.clean(searchterm, strip=True)
	searchterm = nt.prepFilenameForMatching(searchtermclean)

	if not searchterm:
		return render_template('not-implemented-yet.html', message='No search term entered (or search term collapsed down to nothing).')

	similarity = Function('similarity', AlternateNames.cleanname, (searchterm))
	query = select(
			[AlternateNames.series, AlternateNames.cleanname, AlternateNames.name, similarity],
			from_obj=[AlternateNames],
			order_by=desc(similarity)
		).where(
			or_(
				AlternateNames.cleanname.op("%%")(searchterm),
				AlternateNames.cleanname.like(searchterm + "%%")
				)
		).limit(
			50
		)

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



	# print(results)
	# print(data)


	return render_template('text-search.html',
					   results         = data,
					   name_key        = "tag",
					   page_url_prefix = 'tag-id',
					   searchTarget    = "Titles",
					   searchValue     = searchtermclean,
					   title           = 'Search for \'{name}\''.format(name=searchtermclean))






def execute_search():
	# Flatten the passed dicts.
	# This means that multiple identical parameters
	# /WILL/ clobber each other in a non-determinsic manner,
	# but that's not needed for search anyways, so I want
	# to disabiguate.
	search = {}
	search.update(dict(request.args.items()))
	search.update(dict(request.form.items()))

	if 'title' in search:
		return title_search(search['title'])
	else:
		return render_search_page(search)

def do_advanced_search(params):
	print("Params:")
	print(params)
	print()

	# Join on the aggregate functions for sub-chapters.
	rdte = func.max(Releases.published).label('reldate')
	rcnt = func.count(Series.releases).label('ccount')

	q = db.session.query(Series, rdte, rcnt).group_by(Series.id)

	q = q.join(Releases)
	q = q.filter(Releases.series == Series.id)

	if 'tag-category' in params:
		for text, mode in params['tag-category'].items():
			if mode == "included":
				q = q.filter(Series.tags.any(tag=str(text)))
			elif mode == 'excluded':
				q = q.filter(~Series.tags.any(tag=str(text)))
	if 'title-search-text' in params and params['title-search-text']:
		# TODO
		pass


	if 'chapter-limits' in params:
		if len(params['chapter-limits']) == 2:
			minc, maxc = params['chapter-limits']
			minc = int(minc)
			maxc = int(maxc)
			if minc > 0:
				q = q.having(rcnt >= minc)
			if maxc > 0:
				q = q.having(rcnt <= maxc)

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
			q = q.order_by(desc(rdte))
		elif params['sort-mode'] == "chapter-count":
			q = q.order_by(desc(rcnt))
		else: # params['sort-mode'] == "name"
			q = q.order_by(Series.title)
	else:
		q = q.order_by(Series.title)

	q = q.limit(100)
	res = q.all()

	if res:
		print("Results:")
		print(res[0])
		print(dir(res[0]))
	return res

def search_check_ok(params):
	if (
				'chapter-limits' in params
			and
				len(params['chapter-limits']) == 2
			and
				int(params['chapter-limits'][0]) >= 1
		):
		return True

	if (
				'tag-category' in params
			and
				len(params['tag-category']) >= 1
		):
		return True
	if (
				'series-type' in params
			and
				len(params['series-type']) >= 1
		):
		return True
	return False

@app.route('/ajax-search', methods=['POST'])
def ajax_search():
	print("Ajax search!")
	if search_check_ok(request.json):
		series = do_advanced_search(request.json)
		return render_template('ajax-search.html', series=series)
	else:
		return render_template('__block_blurb.html', message="You have to provide some search parameters!")

def render_search_page(search):
	if not search:

		print("Render search page call!")
		results = CommonTags.query                 \
			.filter(CommonTags.tag_instances > 25) \
			.order_by(CommonTags.tag)              \
			.all()

		return render_template('advanced-search.html',
			available_tags = results
			)
	elif 'json' in request.args:
		args = json.loads(request.args['json'])


		if search_check_ok(args):
			series = do_advanced_search(args)
			return render_template('advanced-search-results.html',
				series = series
				)
		else:
			return render_template('not-implemented-yet.html', message="You have to provide some search parameters!")

# @login_required
@app.route('/search', methods=['GET', 'POST'])
def search():
	return execute_search()
