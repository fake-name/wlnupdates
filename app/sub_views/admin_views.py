from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app

from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Releases
from app.models import HttpRequestLog
from app.models import Watches

from sqlalchemy import desc
from natsort import natsort_keygen

import datetime

@app.route('/admin/viewcounts/')
def renderAdminViewcount():
	if not g.user.is_admin():
		return render_template('not-implemented-yet.html')

	last_day = datetime.datetime.now() - datetime.timedelta(days=1)

	total_requests = HttpRequestLog                                 \
					.query                                          \
					.filter(HttpRequestLog.access_time >= last_day) \
					.count()

	clients        = HttpRequestLog                                                     \
					.query                                                              \
					.filter(HttpRequestLog.access_time >= last_day)                     \
					.distinct(HttpRequestLog.user_agent, HttpRequestLog.originating_ip) \
					.all()

	print(total_requests)
	print(clients)

	return render_template('/admin/viewcount.html',
		total_requests = total_requests,
		clients        = clients,
		interval       = "Last Day"
		)

@app.route('/admin/changes/')
def renderAdminChanges():
	if not g.user.is_authenticated():
		return render_template('not-implemented-yet.html')



	series       =       Series.query.filter(Series.id==sid).first()

	if g.user.is_authenticated():
		watch      =       Watches.query.filter(Watches.series_id==sid)     \
		                                  .filter(Watches.user_id==g.user.id) \
		                                  .scalar()
	else:
		watch = False

	if series is None:
		flash(gettext('Series %(sid)s not found.', sid=sid))
		return redirect(url_for('index'))

	releases = series.releases


	series.covers.sort(key=get_cover_sorter())

	return render_template('series-id.html',
						series_id    = sid,
						series       = series,
						releases     = releases,
						watch        = watch,
						)
