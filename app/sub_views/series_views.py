from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext
from app import app
from app.models import Series



def getSeries(page, letter=None, type=None):
	series = Series.query
	if letter:
		series = series.filter(Series.title.like("{}%".format(letter)))
	if type:
		series = series.filter(Series.tl_type==type)
	series = series.order_by(Series.title)

	series = series.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return series

@app.route('/series/<letter>/<int:page>')
@app.route('/series/<page>')
@app.route('/series/<int:page>')
@app.route('/series/')
def renderSeriesTable(letter=None, page=1):
	series = getSeries(letter=letter, page=page)
	return render_template('series-list.html',
						   series_entries   = series,
						   page            = page,
						   name_key        = "title",
						   letter          = letter,
						   path_name       = "series",
						   )



@app.route('/translated-series/<letter>/<int:page>')
@app.route('/translated-series/<page>')
@app.route('/translated-series/<int:page>')
@app.route('/translated-series/')
def renderTranslatedSeriesTable(letter=None, page=1):
	series = getSeries(letter=letter, type='translated', page=page)
	return render_template('series-list.html',
						   series_entries   = series,
						   page            = page,
						   name_key        = "title",
						   path_name       = "translated-series",
						   letter          = letter,
						   title_prefix    = "Translated ",
						   )



@app.route('/oel-series/<letter>/<int:page>')
@app.route('/oel-series/<page>')
@app.route('/oel-series/<int:page>')
@app.route('/oel-series/')
def renderOelSeriesTable(letter=None, page=1):
	series = getSeries(letter=letter, type='oel', page=page)
	return render_template('series-list.html',
						   series_entries   = series,
						   page            = page,
						   name_key        = "title",
						   path_name       = "oel-series",
						   letter          = letter,
						   title_prefix    = "OEL ",
						   )

