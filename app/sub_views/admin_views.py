from flask import render_template
from flask import g
# from guess_language import guess_language
from app import app
from app import db

from app.models import HttpRequestLog
from app.models import Users
from app.models import Series
from app.models import Translators

import sqlalchemy
from sqlalchemy.orm import joinedload

import datetime
import json

import app.api_handlers_admin as api_admin

@app.route('/admin/viewcounts/<int:days>')
@app.route('/admin/viewcounts/')
def renderAdminViewcount(days=1):
	if not g.user.is_admin():
		return render_template('not-implemented-yet.html')

	last_day = datetime.datetime.now() - datetime.timedelta(days=days)

	total_requests = HttpRequestLog                                 \
					.query                                          \
					.filter(HttpRequestLog.access_time >= last_day) \
					.count()

	clients        = HttpRequestLog                                                     \
					.query                                                              \
					.filter(HttpRequestLog.access_time >= last_day)                     \
					.distinct(HttpRequestLog.user_agent, HttpRequestLog.originating_ip) \
					.all()

	referred_by   = HttpRequestLog                                                                       \
					.query                                                                               \
					.filter(sqlalchemy.not_(HttpRequestLog.referer.like('https://www.wlnupdates.com%'))) \
					.filter(sqlalchemy.not_(HttpRequestLog.referer.like('http://10.1.1.8:8081%')))       \
					.filter(HttpRequestLog.access_time >= last_day)                                      \
					.distinct(HttpRequestLog.referer)                                                    \
					.all()

	users         = Users.query.count()

	# print(total_requests)
	# print(clients)
	# print(referred_by)

	return render_template('/admin/viewcount.html',
		total_requests = total_requests,
		clients        = clients,
		referred_by    = referred_by,
		users          = users,
		interval       = "Last {n} Day{p}".format(n=days if days > 1 else '', p='' if days == 1 else "s")
		)



@app.route('/admin/changes/')
def renderAdminChanges():
	if not g.user.is_authenticated():
		return render_template('not-implemented-yet.html')

	return render_template('not-implemented-yet.html')



@app.route('/admin/merge/series')
def renderAdminSeriesMerge():
	if not g.user.is_authenticated():
		return render_template('not-implemented-yet.html')

	try:
		with open("./seriesname-matchset.json", "r") as fp:
			matches = json.loads(fp.read())
	except Exception:
		return render_template('not-implemented-yet.html', message="Error loading merge JSON file?")

	no_merge = api_admin.get_config_json()["no-merge-series"]
	no_merge = [tuple(tmp) for tmp in no_merge]
	print("Loading series data")

	rowids = [tmp['id1'] for tmp in matches] + [tmp['id2'] for tmp in matches]

	print("Beginning series load.")


	db.session.commit()

	series = Series.query.filter(Series.id.in_(rowids))

	series = series.options(joinedload('author'))
	series = series.options(joinedload('alternatenames'))
	series = series.options(joinedload('illustrators'))

	rows = series.all()
	rows = {row.id : row for row in rows}

	print("Cross-correlating IDs.")

	tmp = {}
	for matchitem in matches:
		matchitem['r1'] = rows.get(matchitem['id1'], None)
		matchitem['r2'] = rows.get(matchitem['id2'], None)

		key = (matchitem['id1'], matchitem['id2']) if matchitem['id1'] <= matchitem['id2'] else (matchitem['id2'], matchitem['id1'])
		if key in tmp:
			continue
		if key in no_merge:
			continue

		tmp[key] = matchitem

	single_matches = list(tmp.values())

	single_matches.sort(key=lambda x: min(x['id1'], x['id2']))

	print("Series data loaded. Rendering")
	return render_template('/admin/series-merge.html', matches=single_matches)




@app.route('/admin/merge/groups')
def renderAdminGroupMerge():
	if not g.user.is_authenticated():
		return render_template('not-implemented-yet.html')

	try:
		with open("./translatorname-matchset.json", "r") as fp:
			matches = json.loads(fp.read())
	except Exception:
		return render_template('not-implemented-yet.html', message="Error loading merge JSON file?")

	no_merge = api_admin.get_config_json()["no-merge-groups"]
	no_merge = [tuple(tmp) for tmp in no_merge]
	print("Loading series data")

	rowids = [tmp['id1'] for tmp in matches] + [tmp['id2'] for tmp in matches]
	db.session.commit()

	print("Beginning series load.")

	translators = Translators.query.filter(Translators.id.in_(rowids))

	# translators = translators.options(joinedload('releases'))
	translators = translators.options(joinedload('alt_names'))
	rows = translators.all()
	rows = {row.id : row for row in rows}

	print("Cross-correlating IDs.")

	tmp = {}
	for matchitem in matches:
		matchitem['r1'] = rows.get(matchitem['id1'], None)
		matchitem['r2'] = rows.get(matchitem['id2'], None)

		# print("Matchitem:", matchitem)

		key = (matchitem['id1'], matchitem['id2']) if matchitem['id1'] <= matchitem['id2'] else (matchitem['id2'], matchitem['id1'])
		if key in tmp:
			continue
		if key in no_merge:
			continue

		tmp[key] = matchitem

	single_matches = list(tmp.values())

	single_matches.sort(key=lambda x: min(x['id1'], x['id2']))

	print("Series data loaded. Rendering")
	return render_template('/admin/group-merge.html', matches=single_matches)



@app.route('/admin/tools/')
def renderAdminTools():
	if not g.user.is_authenticated():
		return render_template('not-implemented-yet.html')

	return render_template('/admin/tools.html')


	# series       =       Series.query.filter(Series.id==sid).first()

	# if g.user.is_authenticated():
	# 	watch      =       Watches.query.filter(Watches.series_id==sid)     \
	# 	                                  .filter(Watches.user_id==g.user.id) \
	# 	                                  .scalar()
	# else:
	# 	watch = False

	# if series is None:
	# 	flash(gettext('Series %(sid)s not found.', sid=sid))
	# 	return redirect(url_for('index'))

	# releases = series.releases


	# series.covers.sort(key=get_cover_sorter())

	# return render_template('series-id.html',
	# 					series_id    = sid,
	# 					series       = series,
	# 					releases     = releases,
	# 					watch        = watch,
	# 					)
