from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app
from app.models import Releases
from app.models import Series
from sqlalchemy import desc


def get_releases(srctype=None):
	releases = Releases.query
	if srctype:
		releases = releases.filter(Releases.series_row.has(tl_type = srctype))
	releases = releases.order_by(desc(Releases.published))

	return releases



@app.route('/releases/<page>')
@app.route('/releases/<int:page>')
@app.route('/releases/')
def renderReleasesTable(page=1):

	releases = get_releases()

	if releases is None:
		flash(gettext('No releases? Something is /probably/ broken!.'))
		return redirect(url_for('renderReleasesTable'))

	releases_entries = releases.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('releases.html',
						   sequence_item   = releases_entries,
						   page            = page,
						   tl_type         = ''
						   )




@app.route('/translated-releases/<page>')
@app.route('/translated-releases/<int:page>')
@app.route('/translated-releases/')
def renderTranslatedReleasesTable(page=1):

	releases = get_releases(srctype='translated')

	if releases is None:
		flash(gettext('No releases? Something is /probably/ broken!.'))
		return redirect(url_for('renderReleasesTable'))

	releases_entries = releases.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('releases.html',
						   sequence_item   = releases_entries,
						   page            = page,
						   tl_type         = 'Translated '
						   )



@app.route('/oel-releases/<page>')
@app.route('/oel-releases/<int:page>')
@app.route('/oel-releases/')
def renderOelReleasesTable(page=1):

	releases = get_releases(srctype='oel')

	if releases is None:
		flash(gettext('No releases? Something is /probably/ broken!.'))
		return redirect(url_for('renderReleasesTable'))

	releases_entries = releases.paginate(page, app.config['SERIES_PER_PAGE'], False)

	return render_template('releases.html',
						   sequence_item   = releases_entries,
						   page            = page,
						   tl_type         = 'OEL '
						   )

