from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext
# from guess_language import guess_language
from app import app
from app.models import Releases
from app.models import Series
from sqlalchemy import desc
from sqlalchemy.orm import joinedload


def get_releases(page, srctype=None):
	releases = Releases.query
	if srctype:
		releases = releases.filter(Releases.series_row.has(tl_type = srctype))
	releases = releases.order_by(desc(Releases.published))

	# Join on the series entry. Cuts the total page-rendering queries in half.
	releases = releases.options(joinedload('series_row'))
	releases = releases.options(joinedload('translators'))
	releases = releases.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return releases



@app.route('/releases/<page>')
@app.route('/releases/<int:page>')
@app.route('/releases/')
def renderReleasesTable(page=1):

	if page > 50:
		flash('Historical pages limited to 50 for performance reasons!')
		page = 1

	releases = get_releases(page=page)

	return render_template('releases.html',
						   sequence_item   = releases,
						   page            = page,
						   tl_type         = ''
						   )




@app.route('/translated-releases/<page>')
@app.route('/translated-releases/<int:page>')
@app.route('/translated-releases/')
def renderTranslatedReleasesTable(page=1):

	if page > 50:
		flash('Historical pages limited to 50 for performance reasons!')
		page = 1

	releases = get_releases(page=page, srctype='translated')

	return render_template('releases.html',
						   sequence_item   = releases,
						   page            = page,
						   tl_type         = 'Translated '
						   )



@app.route('/oel-releases/<page>')
@app.route('/oel-releases/<int:page>')
@app.route('/oel-releases/')
def renderOelReleasesTable(page=1):

	if page > 50:
		flash('Historical pages limited to 50 for performance reasons!')
		page = 1

	releases = get_releases(page=page, srctype='oel')

	return render_template('releases.html',
						   sequence_item   = releases,
						   page            = page,
						   tl_type         = 'OEL ',
						   show_group      = False
						   )
