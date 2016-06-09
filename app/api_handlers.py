
from app import db
import app
from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Covers
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Watches
from flask import g
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
import markdown
import bleach
import os.path
import os
import hashlib
from data_uri import DataURI
from flask_login import current_user
import datetime
import dateutil.parser
import app.nameTools as nt
import datetime
from app.api_common import getResponse
import app.series_tools

VALID_KEYS = {
	'description-container'  : 'description',
	'title-container'        : 'title',
	'demographic-container'  : 'demographic',
	'type-container'         : 'type',
	'origin_loc-container'   : 'origin_loc',
	'orig_lang-container'    : 'orig_lang',
	'author-container'       : 'author',
	'illustrators-container' : 'illustrators',
	'tag-container'          : 'tag',
	'genre-container'        : 'genre',
	'altnames-container'     : 'alternate-names',
	'region-container'       : 'region',
	'license_en-container'   : 'license_en',
	'orig_status-container'  : 'orig_status',
	'tl_type-container'      : 'tl_type',
	'website-container'      : 'website',
	'publisher-container'    : 'publisher',
	'pub_date-container'     : 'first_publish_date',
	'watch-container'        : None,

	}

# {
# 	'mode': 'manga-update',
# 	'item-id': '532',
# 	'entries':
# 		[
# 			{
# 				'type': 'combobox',
# 				'key': 'watch-container',
# 				'value': 'no-list'
# 			},
# 			{
# 				'type': 'multiitem',
# 				'key': 'publisher-container',
# 				'value': 'Test'
# 			}
# 		]
# }



VALID_LICENSE_STATES = {
	"unknown" : None,
	"True"    : True,
	"False"   : False,
}


def getCurrentUserId():
	'''
	if current_user == None, we're not executing within the normal flask runtime,
	which means we can probably assume that the caller is the system update
	service.
	'''
	if current_user != None:
		return current_user.id
	else:
		return app.app.config['SYSTEM_USERID']

def validateMangaData(data):
	# print("Manga Data:", data)
	assert "entries" in data
	assert "item-id" in data

	try:
		itemId = int(data['item-id'])
	except ValueError:
		raise AssertionError

	assert itemId >= 0
	update = {
				'id'       : itemId,
				'entries' : []
			}

	for item in data['entries']:
		val = {}
		assert 'value' in item
		assert 'type' in item
		assert 'key' in item

		itemType = item['type']
		assert itemType in ['singleitem', 'multiitem', 'combobox', 'datebox']

		if itemType == 'singleitem' or itemType == 'combobox':
			val['data'] = item['value'].strip()
		elif itemType == 'datebox':
			try:
				val['data'] = dateutil.parser.parse(item['value'])
			except ValueError:
				raise AssertionError("Date updates must be a ISO 8601 string!")
		elif itemType == 'multiitem':
			tmp         = [entry.strip() for entry in item['value'].strip().split("\n")]
			val['data'] = [entry for entry in tmp if entry]
		else:
			raise AssertionError("Invalid item type!")

		if item['key'] not in VALID_KEYS:
			raise AssertionError("Invalid source key: '%s'!" % item['key'])

		# Skip entries where the target is None
		if VALID_KEYS[item['key']]:
			val['type'] = VALID_KEYS[item['key']]
			update['entries'].append(val)

	# Ok, the JSON is valid, and we've more or less sanitized it.
	# Return the processed output.
	return update

def updateTitle(series, newTitle):

	newTitle = bleach.clean(newTitle.strip())

	conflict_series = Series.query.filter(Series.title==newTitle).scalar()

	if conflict_series and conflict_series.id != series.id:
		return getResponse("A series with that name already exists! Please choose another name", error=True)


	oldTitle = series.title
	series.title = newTitle

	ret = app.series_tools.updateAltNames(series, [newTitle, oldTitle], deleteother=False)
	if ret:
		return ret

	return None


def processMangaUpdateJson(data):
	validated = validateMangaData(data)

	sid = validated['id']
	series = Series.query.filter(Series.id==sid).one()
	print(validated)

	for entry in validated['entries']:
		# print(entry)

		if entry['type'] == 'title':
			if not current_user.is_mod():
				return getResponse(error=True, message="You have to have moderator privileges to do that!")

			ret = updateTitle(series, bleach.clean(entry['data'], strip=True))
			if ret:
				return ret

		elif entry['type'] == 'description':
			processedData = markdown.markdown(bleach.clean(entry['data'], strip=True))
			if series.description == processedData:
				# print("No change?")
				pass
			else:
				series.description = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()


		elif entry['type'] == 'demographic':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				# print("No change?")
				pass
			else:
				series.demographic = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'orig_status':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.orig_status == processedData:
				# print("No change?")
				pass
			else:
				series.orig_status = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'region':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				# print("No change?")
				pass
			else:
				series.region = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'tl_type':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.tl_type == processedData:
				# print("No change?")
				pass
			else:
				series.tl_type = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'license_en':
			lic_state = entry['data']

			if lic_state not in VALID_LICENSE_STATES:
				raise ValueError("Invalid license data!")
			else:
				lic_state = VALID_LICENSE_STATES[lic_state]

			series.license_en = lic_state
			series.changeuser = getCurrentUserId()
			series.changetime = datetime.datetime.now()


			# if series.demographic == processedData:
			# 	# print("No change?")
			# 	pass
			# else:
			# 	series.region = processedData
			# 	series.changeuser = getCurrentUserId()
			# 	series.changetime = datetime.datetime.now()

		elif entry['type'] == 'type':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.type == processedData:
				# print("No change?")
				pass
			else:
				series.type = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'origin_loc':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.origin_loc == processedData:
				# print("No change?")
				pass
			else:
				series.origin_loc = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'orig_lang':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.orig_lang == processedData:
				# print("No change?")
				pass
			else:
				series.orig_lang = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'website':
			processedData = bleach.clean(entry['data'], strip=True, tags=[])
			if series.website == processedData:
				# print("No change?")
				pass
			else:
				series.website    = processedData
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'first_publish_date':
			pub_date = entry['data']
			if series.pub_date == pub_date:
				# print("No change?")
				pass
			else:
				series.pub_date   = pub_date
				print("Publish date: ", series.pub_date)
				series.changeuser = getCurrentUserId()
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'author':

			ret = app.series_tools.setAuthorIllust(series, author=entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'illustrators':
			ret = app.series_tools.setAuthorIllust(series, illust=entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'publisher':
			ret = app.series_tools.updatePublishers(series, publishers=entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'tag':
			ret = app.series_tools.updateTags(series, entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'genre':
			ret = app.series_tools.updateGenres(series, entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'alternate-names':
			ret = app.series_tools.updateAltNames(series, entry['data'])
			if ret:
				return ret
		else:
			raise AssertionError("Unknown modifification type!")

	db.session.commit()
	ret = {
			"error"   : False,
			"message" : "Wat?!"
	}
	return ret

# {'watch': True, 'mode': 'set-watch', 'item-id': '1857', 'list': 'watched'}

################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################


def validateWatchedData(data):
	assert "watch" in data
	assert "list" in data
	assert "item-id" in data

	update = {}
	try:
		update['watch'] = bool(data['watch'])
	except ValueError:
		raise AssertionError

	try:
		update['item-id'] = int(data['item-id'])
	except ValueError:
		raise AssertionError


	try:
		# Clean all html.
		update['listName'] = bleach.clean(str(data['list']), tags=[], strip=True)
	except ValueError:
		raise AssertionError
	if len(update['listName']) > 256:
		raise AssertionError

	# Special case handle the special list name that removes the item from the list.
	# Set the watch to none, so the corresponsing list gets deleted.
	# Yes, this is a hack, and I'm ignoring the "watch" boolean field in the
	# API params, but... eh. It's easier to fix here then in the javascript.
	if update['listName'] == '-0-0-0-0-0-0-0-no-list-0-0-0-0-0-0-0-0-':
		# print("List deletion token!")
		update['watch'] = False
		# print("Doing watch:", update['watch'])

	# print("update['listName'] == '-0-0-0-0-0-0-0-no-list-0-0-0-0-0-0-0-0-': ", update['listName'] == '-0-0-0-0-0-0-0-no-list-0-0-0-0-0-0-0-0-')

	# Ok, the JSON is valid, and we've more or less sanitized it.
	# Return the processed output.
	return update


def setSeriesWatchJson(data):
	cleaned = validateWatchedData(data)
	print("[setSeriesWatchJson] data -> ", data)
	watch_row = Watches.query.filter(
			(Watches.user_id==getCurrentUserId()) &
			(Watches.series_id==cleaned['item-id'])
		).scalar()

	# There are 5 possible permutations here:
	# Want to watch item, item not in any extant list:
	# 	- Add item to list
	# Want to watch item, item in extant list:
	# 	- Update item
	# Want to stop watching item, item in a list:
	# 	- Delete item
	# Want to stop watching item, item not in list
	# 	- Do nothing (how did that happen?)
	# Want to watch item, item already watched and in correct list
	# 	- Do nothing (how did that happen?)

	if not watch_row and cleaned['watch']:
		# Want to watch item, item not in any extant list:

		newWatch = Watches(
			user_id   = getCurrentUserId(),
			series_id = cleaned['item-id'],
			listname  = cleaned['listName'],
		)

		db.session.add(newWatch)
		db.session.commit()
		watch_str = "Yes"

	elif watch_row and cleaned['watch'] and cleaned['listName'] != watch_row.listname:
		# Want to watch item, item in extant list:
		watch_row.listname = cleaned['listName']
		db.session.commit()
		watch_str = "Yes"

	elif watch_row and not cleaned['watch']:
		# Want to stop watching item, item in a list:
		db.session.delete(watch_row)
		db.session.commit()
		watch_str = "No"

	else:
		# Want to stop watching item, item not in list
		# Want to watch item, item already watched and in correct list
		watch_str = "Wat?"



	ret = {
			"error"     : False,
			"message"   : "Watch Updated",
			'watch_str' : watch_str

	}
	return ret


################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################


VALID_GROUP_KEYS = {
	'altnames-container'     : 'alternate-names',
	}

def validateGroupData(data):
	print("Group Data:", data)
	assert "entries" in data
	assert "item-id" in data

	try:
		itemId = int(data['item-id'])
	except ValueError:
		raise AssertionError

	assert itemId >= 0
	update = {
				'id'       : itemId,
				'entries' : []
			}

	for item in data['entries']:
		val = {}
		assert 'value' in item
		assert 'type' in item
		assert 'key' in item

		itemType = item['type']
		assert itemType in ['singleitem', 'multiitem', 'combobox']

		if itemType == 'singleitem' or itemType == 'combobox':
			val['data'] = item['value'].strip()
		elif itemType == 'multiitem':
			tmp         = [entry.strip() for entry in item['value'].strip().split("\n")]
			val['data'] = [entry for entry in tmp if entry]
		else:
			raise AssertionError("Invalid item type!")

		if item['key'] not in VALID_GROUP_KEYS:
			raise AssertionError("Invalid source key: '%s'!" % item['key'])
		else:
			val['type'] = VALID_GROUP_KEYS[item['key']]

		update['entries'].append(val)

	# Ok, the JSON is valid, and we've more or less sanitized it.
	# Return the processed output.
	return update



def updateGroupAltNames(group, altnames, delete=True):
	print("Alt names:", altnames)
	altnames = [name.strip() for name in altnames]
	cleaned = {}
	for name in altnames:
		if name.lower().strip():
			cleaned[name.lower().strip()] = name

	havenames = AlternateTranslatorNames.query.filter(AlternateTranslatorNames.group==group.id).order_by(AlternateTranslatorNames.name).all()
	havenames = {name.name.lower().strip() : name for name in havenames}

	for name in cleaned.keys():
		if name in havenames:
			havenames.pop(name)
		else:
			newname = AlternateTranslatorNames(
					name       = cleaned[name],
					cleanname  = nt.prepFilenameForMatching(cleaned[name]),
					group      = group.id,
					changetime = datetime.datetime.now(),
					changeuser = getCurrentUserId()
				)
			db.session.add(newname)

	if delete:
		for key, value in havenames.items():
			db.session.delete(value)

	db.session.commit()



def processGroupUpdateJson(data):
	validated = validateGroupData(data)

	sid = validated['id']
	group = Translators.query.filter(Translators.id==sid).one()

	for entry in validated['entries']:
		print(entry)

		if entry['type'] == 'alternate-names':
			updateGroupAltNames(group, entry['data'])
		else:
			raise AssertionError("Unknown modifification type!")

	ret = {
			"error"   : False,
			"message" : "Wat?!"
	}
	return ret

def validateReadingProgressData(inDat):
	assert 'mode'    in inDat
	assert 'item-id' in inDat
	assert 'vol'     in inDat
	assert 'chp'     in inDat
	assert 'frag'    in inDat

	try:
		vol  = float(inDat['vol'])
		chp  = float(inDat['chp'])
		frag = float(inDat['frag'])
		sid  = int(inDat['item-id'])
	except ValueError:
		raise AssertionError("Volume, chapter, and fragment must be numbers!")

	if any([item < 0 for item in (vol, chp, frag)]):
		raise AssertionError("Values cannot be lower then 0!")


	return sid, (vol, chp, frag)

def setReadingProgressJson(data):
	sid, progress = validateReadingProgressData(data)

	watch_row = Watches.query.filter(
			(Watches.user_id==getCurrentUserId()) &
			(Watches.series_id==sid)
		).one()

	vol, chp, frag = progress

	if chp == 0 and vol == 0:
		vol = -1
		chp = -1

	if vol == 0:
		vol = None

	if frag == 0:
		frag = None

	watch_row.volume   = vol
	watch_row.chapter  = chp
	watch_row.fragment = frag
	db.session.commit()

	return getResponse('Succeeded')

def getHash(filecont):
	m = hashlib.md5()
	m.update(filecont)
	fHash = m.hexdigest()
	return fHash

def saveCoverFile(filecont, filename):
	fHash = getHash(filecont)
	# use the first 3 chars of the hash for the folder name.
	# Since it's hex-encoded, that gives us a max of 2^12 bits of
	# directories, or 4096 dirs.
	fHash = fHash.upper()
	dirName = fHash[:3]

	dirPath = os.path.join(app.app.config['COVER_DIR_BASE'], dirName)
	if not os.path.exists(dirPath):
		os.makedirs(dirPath)

	ext = os.path.splitext(filename)[-1]
	ext   = ext.lower()

	# The "." is part of the ext.
	filename = '{filename}{ext}'.format(filename=fHash, ext=ext)


	# The "." is part of the ext.
	filename = '{filename}{ext}'.format(filename=fHash, ext=ext)

	# Flask config values have specious "/./" crap in them. Since that gets broken through
	# the abspath canonization, we pre-canonize the config path so it compares
	# properly.
	confpath = os.path.abspath(app.app.config['COVER_DIR_BASE'])

	fqpath = os.path.join(dirPath, filename)
	fqpath = os.path.abspath(fqpath)

	if not fqpath.startswith(confpath):
		raise ValueError("Generating the file path to save a cover produced a path that did not include the storage directory?")

	locpath = fqpath[len(confpath):]
	if not os.path.exists(fqpath):
		print("Saving cover file to path: '{fqpath}'!".format(fqpath=fqpath))
		with open(fqpath, "wb") as fp:
			fp.write(filecont)
	else:
		print("File '{fqpath}' already exists!".format(fqpath=fqpath))

	if locpath.startswith("/"):
		locpath = locpath[1:]
	return locpath

VALID_COVER_OPS = {
	'name',
	'new-cover'
}

def updateCoverTitle(series, updateDat):
	'''
	assert ALL THE THINGS
	'''
	assert 'new'   in updateDat
	assert 'old'   in updateDat
	assert 'type'  in updateDat
	assert 'covid' in updateDat
	assert 'c-input-' in updateDat['covid']
	assert len(updateDat['new']) < 255

	cid = int(updateDat['covid'].replace('c-input-', ''))
	cover = Covers.query.filter(Covers.id==cid).one()
	if cover.description == None:
		cover.description = ''
	assert cover.description == updateDat['old']

	cover.description = bleach.clean(str(updateDat['new']), tags=[], strip=True)
	db.session.commit()


# {'type': 'new-cover', 'name': 'DM01M.jpg', 'file': 'data:image
def addNewCover(series, updateDat):
	assert 'name' in updateDat
	assert 'file' in updateDat
	assert 'type' in updateDat

	data = DataURI(updateDat['file'])

	dathash = getHash(data.data).lower()
	have = Covers.query.filter(Covers.hash == dathash).scalar()
	if have:
		return getResponse("A cover with that MD5 hash already exists! Are you accidentally adding a duplicate?", True)

	covpath = saveCoverFile(data.data, updateDat['name'])

	new = Covers(
		srcfname    = updateDat['name'],
		series      = series.id,
		description = '',
		fspath      = covpath,
		hash        = dathash,
		)

	db.session.add(new)
	db.session.commit()

	# print(data.mimetype)
	# print(data.data)
	# with open(updateDat['name'], 'wb') as fp:
	# 	fp.write(data.data)

def processCoverUpdate(series, entry):
	assert 'type' in entry
	assert entry['type'] in VALID_COVER_OPS

	if entry['type'] == "name":
		return updateCoverTitle(series, entry)

	if entry['type'] == "new-cover":
		return addNewCover(series, entry)



def updateAddCoversJson(data):
	assert 'mode' in data
	assert 'entries' in data
	assert 'item-id' in data
	assert data['mode'] == 'cover-update'
	sid = data['item-id']

	series = Series.query.filter(Series.id==sid).one()

	# print(series)
	ret = None
	for entry in data['entries']:
		ret = processCoverUpdate(series, entry)
		if ret:
			return ret
	return getResponse("Success", False)


def setRatingJson(data):
	assert 'mode' in data
	assert 'rating' in data
	assert 'item-id' in data
	assert data['item-id']
	sid    = int(data['item-id'])
	rating = int(data['rating'])

	assert rating >= 0
	assert rating <= 10

	app.series_tools.set_rating(sid, rating)

	return getResponse("SetRating call!.", error=False)




