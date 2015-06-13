
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
from app.models import Series
from app.models import Watches
import app.nameTools as nt
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
			AlternateNames.cleanname.op("%%")(searchterm)
		).limit(
			50
		)

	results = db.session.execute(query).fetchall()

	data = collections.OrderedDict()

	for result in results:
		dbid = result[0]
		if not dbid in data:
			data[dbid] = {}
			data[dbid]['row'] = Series.query.filter(Series.id==dbid).one()
			data[dbid]['watch'] = Watches.query.filter(Watches.series_id==dbid).scalar()
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
		flash(gettext('Bad search route!'))
		return redirect(url_for('index'))


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
