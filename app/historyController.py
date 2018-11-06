from flask import render_template
from .models import SeriesChanges
from .models import TagsChanges
from .models import GenresChanges
from .models import AuthorChanges
from .models import IllustratorsChanges
from .models import AlternateNamesChanges
from .models import PublishersChanges
from .models import AlternateTranslatorNamesChanges




dispatch_table = {
	'description'    : SeriesChanges,
	'demographic'    : SeriesChanges,
	'type'           : SeriesChanges,
	'origin_loc'     : SeriesChanges,
	'orig_lang'      : SeriesChanges,
	'tl_type'        : SeriesChanges,
	'orig_status'    : SeriesChanges,
	'region'         : SeriesChanges,
	'license_en'     : SeriesChanges,
	'pub_date'       : SeriesChanges,
	'website'        : SeriesChanges,
	'author'         : AuthorChanges,
	'illustrators'   : IllustratorsChanges,
	'tag'            : TagsChanges,
	'genre'          : GenresChanges,
	'altnames'       : AlternateNamesChanges,
	'publisher'      : PublishersChanges,
	'group-altnames' : AlternateTranslatorNamesChanges,
}

def rowToDict(row):
	return {x.name: getattr(row, x.name) for x in row.__table__.columns}

maskedRows = ['id', 'operation', 'srccol', 'changeuser', 'changetime']


def generateSeriesHistArray(inRows):
	inRows = [rowToDict(row) for row in inRows]
	inRows.sort(key = lambda x: x['id'])

	# Generate the list of rows we actually want to process by extracting out
	# the keys in the passed row, and masking out the ones we specifically don't want.
	if inRows:
		processKeys = [key for key in inRows[0].keys() if key not in maskedRows]
		processKeys.sort()
	else:
		processKeys = []

	# Prime the loop by building an empty dict to compare against
	previous = {key: None for key in processKeys}


	ret = []
	for row in inRows:
		rowUpdate = []
		for key in processKeys:
			if (row[key] != previous[key]) and (row[key] or previous[key]):
				item = {
					'changetime' : row['changetime'],
					'changeuser' : row['changeuser'],
					'operation'  : row['operation'],
					'item'       : key,
					'value'      : row[key]
					}
				previous[key] = row[key]
				# print(item)
				rowUpdate.append(item)

		if rowUpdate:
			ret.append(rowUpdate)

	return ret


def renderHistory(histType, contentId):
	# print("histType", histType)
	if histType not in dispatch_table:
		return render_template('not-implemented-yet.html', message='Error! Invalid history type.')

	table = dispatch_table[histType]

	if table == SeriesChanges:
		conditional = (table.srccol==contentId)
	elif table == AlternateTranslatorNamesChanges:
		conditional = (table.group==contentId)
	else:
		conditional = (table.series==contentId)


	data = table                                   \
			.query                                 \
			.filter(conditional)                   \
			.order_by(table.changetime).all()

	# print("History data:", data)

	seriesHist    = None
	authorHist    = None
	illustHist    = None
	tagHist       = None
	genreHist     = None
	nameHist      = None
	pubHist       = None
	groupAltNames = None

	if table == SeriesChanges:
		seriesHist = generateSeriesHistArray(data)
	if table == AuthorChanges:
		authorHist = data
	if table == IllustratorsChanges:
		illustHist = data
	if table == TagsChanges:
		tagHist = data
	if table == GenresChanges:
		genreHist = data
	if table == AlternateNamesChanges:
		nameHist = data
	if table == AlternateTranslatorNamesChanges:
		groupAltNames = data
	if table == PublishersChanges:
		pubHist = data

	return render_template('history.html',
			seriesHist    = seriesHist,
			authorHist    = authorHist,
			illustHist    = illustHist,
			tagHist       = tagHist,
			genreHist     = genreHist,
			nameHist      = nameHist,
			pubHist       = pubHist,
			groupAltNames = groupAltNames,
			)
