import datetime
from sqlalchemy import desc
from flask_babel import gettext
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import nullslast

from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask import request

from app.context_processors import staleness_factor
from app.models import Watches
from app.models import Series
from app.models import Releases
from app import app
from app import db

from app.utilities import get_latest_release
from app.utilities import get_latest_releases

def load_watches(active_filter_override=None):

	watches = Watches                                    \
				.query                                   \
				.options(joinedload(Watches.series_row)) \
				.filter(Watches.user_id == g.user.id)    \
				.all()

	active_filter = 'all'
	if 'active-filter' in request.args:
		active_filter = request.args['active-filter'] if request.args['active-filter'] in ['active', 'maybe-stalled', 'stalled', 'all'] else 'all'

	if active_filter_override:
		active_filter = active_filter_override if active_filter_override in ['active', 'maybe-stalled', 'stalled', 'all'] else 'all'

	data = {}

	ids = []
	for watch in [tmp for tmp in watches]:

		series = watch.series_row
		if not series:
			watches.remove(watch)
			db.session.delete(watch)
			db.session.commit()
		else:
			ids.append(series.id)

	latest = get_latest_releases(ids)

	for watch in watches:
		series = watch.series_row
		# latest = get_latest_release(series)

		# build easier-to-use dicts we can pass the template,
		# and calculate a aggregate progress number that works for
		# direct comparisons across chapter/volume releases
		avail = {}
		prog  = {}
		prog['vol']  = watch.volume   if watch and watch.volume    != None else -1
		prog['chp']  = watch.chapter  if watch and watch.chapter   != None else -1
		prog['frag'] = watch.fragment if watch and watch.fragment  != None else -1

		# avail['vol'] = latest.volume  if latest and latest.volume  != None else -1
		# avail['chp'] = latest.chapter if latest and latest.chapter != None else -1


		avail['date'] = latest[series.id][1]
		avail['vol']  = latest[series.id][0][0]
		avail['chp']  = latest[series.id][0][1]
		avail['frag'] = latest[series.id][0][2]

		prog['agg']  = 0
		if prog['vol'] > 0:
			prog['agg'] += prog['vol'] * 1e4
		if prog['chp'] > 0:
			prog['agg'] += prog['chp']
		if prog['frag'] > 0:
			prog['agg'] += prog['frag'] * 1e-4

		avail['agg'] = 0
		if avail['vol'] > 0:
			avail['agg'] += avail['vol'] * 1e4
		if avail['chp'] > 0:
			avail['agg'] += avail['chp']
		if avail['frag'] > 0:
			avail['agg'] += avail['frag'] * 1e-4


		data.setdefault(watch.listname, [])

		sf = staleness_factor(avail['date'])
		if active_filter == 'active' and sf in ["updating-current"]:
			data[watch.listname].append((series, prog, avail, watch.watch_as_name))
		elif active_filter == 'maybe-stalled' and sf in ["updating-current", "updating-stale"]:
			data[watch.listname].append((series, prog, avail, watch.watch_as_name))
		elif active_filter == 'stalled' and sf in ["updating-current", "updating-stale", "updating-stalled"]:
			data[watch.listname].append((series, prog, avail, watch.watch_as_name))
		elif active_filter == 'all':
			data[watch.listname].append((series, prog, avail, watch.watch_as_name))

		# else:  # This /shouldn't/ ever happen, but wth.
		# 	data[watch.listname].append((series, prog, avail, watch.watch_as_name))


	for key in data.keys():
		data[key].sort(key=lambda x: (x[0].title.lower()))

	lists = list(data.keys())
	lists.sort(key=lambda x: (x.lower()))

	return data, lists, active_filter

def recursively_convert_dt(in_val):
	if isinstance(in_val, dict):
		return {key : recursively_convert_dt(val) for key, val in in_val.items()}
	elif isinstance(in_val, datetime.datetime):
		return in_val.timestamp()
	elif isinstance(in_val, (list, tuple)):
		return [recursively_convert_dt(item) for item in in_val]

	return in_val

def serialize_series_object(series):
	return {
		"name"           : series.title,
		"id"             : series.id,
		"tl_type"        : series.tl_type,
		"rating"         : series.rating,
		"rating_count"   : series.rating_count,
		"extra_metadata" : series.extra_metadata,
	}


def serialize_watches(watches):

	data, lists, active_filter = watches
	clean_data = {}

	for listname, listitems in data.items():
		clean_data[listname] = [(serialize_series_object(series), prog, recursively_convert_dt(avail), watch_as_name) for series, prog, avail, watch_as_name in listitems]

	return clean_data, lists, active_filter


@app.route('/watches', methods=['GET'])
def renderUserWatches():
	if not g.user.is_authenticated():
		flash(gettext('You need to log in to create or view series watches.'))
		return redirect(url_for('index'))


	# data.sort(key=lambda x: (x[0].lower(), x[1].title.lower()))

	watches, lists, active_filter = load_watches()

	return render_template(
			'watched.html',
			watches = watches,
			lists   = lists,
			active_filter = active_filter,
		)


@app.route('/user-cp')
def renderUserCp():
	if not g.user.is_authenticated():
		flash(gettext('You need to log in to acces your user control-panel.'))
		return redirect(url_for('index'))

	return render_template('user_cp.html')
