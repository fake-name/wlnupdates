
from flask import render_template, flash, redirect, url_for, g, request

from app import app
from app.models import Watches, Series

from app import db

@app.route('/watches')
def renderUserLists():
	print(g.user)
	print(g.user.id)

	query = db.session.query(Series) \
		.filter(Watches.user_id == g.user.id) \
		.filter(Watches.series_id == Series.id)
	watched = query.all()
	for series in watched:
		print(series)

	watches = Watches.query.filter(Watches.user_id == g.user.id).all()
	print("watches: ", watches)
	return render_template(
			'watched.html',
			watches = watched
		)
