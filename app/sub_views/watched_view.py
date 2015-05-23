
from flask import render_template, flash, redirect, url_for, g, request

from app import app
from app.models import Watches, Series, Releases
from sqlalchemy import desc
from app import db
from sqlalchemy.orm import joinedload
def get_latest_release(series):
	latest = Releases                               \
				.query                              \
				.filter(Releases.series==series.id) \
				.order_by(desc(Releases.volume))    \
				.order_by(desc(Releases.chapter))   \
				.limit(1)                           \
				.scalar()
	return latest

@app.route('/watches')
def renderUserLists():

	watches = Watches                                       \
				.query                                      \
				.options(joinedload(Watches.series_row))    \
				.filter(Watches.user_id == g.user.id).all()


	data = []
	for watch in watches:
		series = watch.series_row
		latest = get_latest_release(series)

		avail = {}
		prog  = {}
		prog['vol']  = watch.volume   if watch and watch.volume    != None else -1
		prog['chp']  = watch.chapter  if watch and watch.chapter   != None else -1
		avail['vol'] = latest.volume  if latest and latest.volume  != None else -1
		avail['chp'] = latest.chapter if latest and latest.chapter != None else -1


		prog['agg']  = 0
		if prog['vol'] > 0:
			prog['agg'] += prog['vol'] * 1e4
		if prog['chp'] > 0:
			prog['agg'] += prog['chp']

		avail['agg'] = 0
		if avail['vol'] > 0:
			avail['agg'] += avail['vol'] * 1e4
		if avail['chp'] > 0:
			avail['agg'] += avail['chp']

		# print(prog)
		if latest:
			print(avail)
			print(latest.volume, latest.chapter)
		data.append((series, prog, avail))

	return render_template(
			'watched.html',
			watches = data
		)
