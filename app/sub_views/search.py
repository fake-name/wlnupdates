
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





def render_search_page():
	print("Render search page call!")
	results = CommonTags.query                 \
		.filter(CommonTags.tag_instances > 25) \
		.order_by(CommonTags.tag)              \
		.all()

	return render_template('advanced-search.html',
		available_tags = results
		)

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
		return render_search_page()

def do_advanced_search(params):
	print("Params:")
	print(params)
	print()
	q = Series.query

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
			subq = Releases.query.filter(Releases.series == Series.id).count()
			if minc > 0:
				q = q.filter(subq >= minc)
			if maxc > 0:
				q = q.filter(subq <= maxc)

	type_map = {
		'Translated'                : 'oel',
		'Original English Language' : 'translated',
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

	if "sort-mode" in params and False:

		if params['sort-mode'] == "update":
			subq = Releases.query.filter(Releases.series == Series.id).max(Releases.published).one()
			q = q.order_by(desc(subq))
		elif params['sort-mode'] == "chapter-count":
			subq = func.count(Releases.query.filter(Releases.series == Series.id))
			q = q.order_by(desc(subq))

		else: # params['sort-mode'] == "name"
			q = q.order_by(Series.title)
	else: # params['sort-mode'] == "name"
		q = q.order_by(Series.title)

	res = q.all()

	return res


@app.route('/ajax-search', methods=['POST'])
def ajax_search():
	print("Ajax search!")
	series = do_advanced_search(request.json)
	return render_template('ajax-search.html', series=series)


# @login_required
@app.route('/search', methods=['GET', 'POST'])
def search():
	return execute_search()


	# return render_template('search_results.html',
	# 				   # sequence_item   = series_entries,
	# 				   # page            = page,
	# 				   name_key        = "title",
	# 				   page_url_prefix = 'series-id',
	# 				   searchTarget    = 'Tags',
	# 				   # searchValue     = tag.tag
	# 				   )
