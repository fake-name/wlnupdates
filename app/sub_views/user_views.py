
from flask import render_template, flash, redirect, url_for, g, request
from app import app
from app.models import Watches
from app.models import Series
from app.models import Releases
from sqlalchemy import desc
from app import db
from flask_babel import gettext
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import nullslast

from app.utilities import get_latest_release
from app.utilities import get_latest_releases


@app.route('/watches')
def renderUserWatches():
	if not g.user.is_authenticated():
		flash(gettext('You need to log in to create or view series watches.'))
		return redirect(url_for('index'))

	watches = Watches                                    \
				.query                                   \
				.options(joinedload(Watches.series_row)) \
				.filter(Watches.user_id == g.user.id)    \
				.all()


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

		if not watch.listname in data:
			data[watch.listname] = []
		data[watch.listname].append((series, prog, avail, watch.watch_as_name))

	for key in data.keys():
		data[key].sort(key=lambda x: (x[0].title.lower()))

	# data.sort(key=lambda x: (x[0].lower(), x[1].title.lower()))

	lists = list(data.keys())
	lists.sort(key=lambda x: (x.lower()))

	return render_template(
			'watched.html',
			watches = data,
			lists   = lists
		)


@app.route('/user-cp')
def renderUserCp():
	if not g.user.is_authenticated():
		flash(gettext('You need to log in to acces your user control-panel.'))
		return redirect(url_for('index'))

	return render_template('user_cp.html')
