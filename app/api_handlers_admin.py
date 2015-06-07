
from app import db
from app import app
from app.models import AlternateNames
from app.models import AlternateNamesChanges
from app.models import AlternateTranslatorNames
from app.models import Author
from app.models import AuthorChanges
from app.models import Genres
from app.models import GenresChanges
from app.models import Illustrators
from app.models import IllustratorsChanges
from app.models import Series
from app.models import SeriesChanges
from app.models import Tags
from app.models import TagsChanges
from app.models import Translators

from app.models import Covers
from app.models import CoversChanges

from app.models import Releases
from app.models import ReleasesChanges
from app.models import Watches

from flask import flash
from flask.ext.babel import gettext
from flask.ext.login import current_user

from flask.ext.login import current_user
import app.series_tools
from app.api_common import getResponse




def mergeSeriesItems(data):
	if not current_user.has_mod:
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'merge-id'
	assert 'item-id' in data
	assert 'merge_id' in data

	m1, m2 = int(data['item-id']), int(data['merge_id'])
	merge_from = max(m1, m2)
	merge_to   = min(m1, m2)

	itm_from = Series.query.filter(Series.id==merge_from).one()
	itm_to = Series.query.filter(Series.id==merge_to).one()

	alts   = []
	author = []
	illust = []
	tags   = []
	genres = []

	alts.append(itm_from.title)
	for altname in AlternateNames.query.filter(AlternateNames.series==itm_from.id).all():
		alts.append(altname.name)

	for val in Author.query.filter(Author.series==itm_from.id).all():
		author.append(val.name)

	for val in Illustrators.query.filter(Illustrators.series==itm_from.id).all():
		illust.append(val.name)

	for val in Tags.query.filter(Tags.series==itm_from.id).all():
		tags.append(val.tag)

	for val in Genres.query.filter(Genres.series==itm_from.id).all():
		genres.append(val.genre)


	# !Ordering here matters!
	# Change-tables have to go second.
	delete_from = [
			AlternateNames,
			AlternateNamesChanges,
			Author,
			AuthorChanges,
			Illustrators,
			IllustratorsChanges,
			Tags,
			TagsChanges,
			Genres,
			GenresChanges,
		]

	for clearTable in delete_from:
		clearTable.query.filter(clearTable.series==itm_from.id).delete()

	app.series_tools.updateAltNames  ( itm_to, alts,            deleteother=False )
	app.series_tools.setAuthorIllust ( itm_to, author = author, deleteother=False )
	app.series_tools.setAuthorIllust ( itm_to, illust = illust, deleteother=False )
	app.series_tools.updateTags      ( itm_to, tags   = tags,   deleteother=False )
	app.series_tools.updateGenres    ( itm_to, genres = genres, deleteother=False )

	# For each user watch, if the user is already watching the merge-to item,
	# just delete it. If not, update the user-id
	for watch in Watches.query.filter(Watches.series_id==itm_from.id).all():
		if not Watches                              \
				.query                                  \
				.filter(Watches.series_id==itm_to.id)   \
				.filter(Watches.user_id==watch.user_id) \
				.scalar():

			watch.series_id = itm_to.id

		else:
			db.session.delete(watch)

	if itm_from.description and not itm_to.description:
		itm_to.description = itm_from.description

	if itm_from.description and not itm_to.description:
		itm_to.description = itm_from.description
	if itm_from.type and not itm_to.type:
		itm_to.type = itm_from.type
	if itm_from.origin_loc and not itm_to.origin_loc:
		itm_to.origin_loc = itm_from.origin_loc
	if itm_from.demographic and not itm_to.demographic:
		itm_to.demographic = itm_from.demographic
	if itm_from.orig_lang and not itm_to.orig_lang:
		itm_to.orig_lang = itm_from.orig_lang
	if not itm_to.volume or (itm_from.volume and itm_from.volume > itm_to.volume):
		itm_to.volume = itm_from.volume
	if not itm_to.chapter or (itm_from.chapter and itm_from.chapter > itm_to.chapter):
		itm_to.chapter = itm_from.chapter
	if itm_from.region and not itm_to.region:
		itm_to.region = itm_from.region
	if not itm_to.tot_chapter or (itm_from.tot_chapter and itm_from.tot_chapter > itm_to.tot_chapter):
		itm_to.tot_chapter = itm_from.tot_chapter
	if not itm_to.tot_volume or (itm_from.tot_volume and itm_from.tot_volume > itm_to.tot_volume):
		itm_to.tot_volume = itm_from.tot_volume
	if itm_from.license_en and not itm_to.license_en:
		itm_to.license_en = itm_from.license_en
	if itm_from.orig_status and not itm_to.orig_status:
		itm_to.orig_status = itm_from.orig_status

	db.session.flush()
	Covers.query.filter(Covers.series==itm_from.id).update({'series': itm_to.id})
	CoversChanges.query.filter(CoversChanges.series==itm_from.id).update({'series': itm_to.id})

	# Move releases over
	Releases.query.filter(Releases.series==itm_from.id).update({'series': itm_to.id})
	ReleasesChanges.query.filter(ReleasesChanges.series==itm_from.id).update({'series': itm_to.id})

	sid = itm_from.id
	Series.query.filter(Series.id==sid).delete(synchronize_session="fetch")
	SeriesChanges.query.filter(SeriesChanges.id==sid).delete(synchronize_session="fetch")

	db.session.commit()

	return getResponse("Success", False)

def getReleaseFromId(inId):
	ret = Releases.query.filter(Releases.id==inId).one()
	return ret

def toggle_counted(data):
	release = getReleaseFromId(data['id'])
	release.include = not release.include
	db.session.commit()

	flash(gettext('Release %(id)s count-state toggled. New state: %(state)s', id=release.id, state="counted" if release.include else "uncounted"))
	return getResponse("Item count-state toggled!", error=False)

def delete(data):
	release = getReleaseFromId(data['id'])
	db.session.delete(release)
	db.session.commit()
	flash(gettext('Release deleted.'))
	return getResponse("Release deleted.", error=False)


RELEASE_OPS = {
	'toggle-counted' : toggle_counted,
	'delete'         : delete,
}

BOOL_LUT = {
	"True"  : True,
	"False" : False,
}


def alterReleaseItem(data):

	if not current_user.has_mod:
		return getResponse(error=True, message="You have to have moderator privileges to do that!")
	assert 'op' in data
	assert 'mode' in data
	assert 'count' in data
	assert 'id' in data

	assert data['mode'] == "release-ctrl"

	try:
		data['id'] = int(data['id'])
	except ValueError:
		raise AssertionError("Failure converting item ID to integer!")
	assert data['count'] in BOOL_LUT
	data['count'] = BOOL_LUT[data['count']]

	assert data['op'] in RELEASE_OPS

	return RELEASE_OPS[data['op']](data)

