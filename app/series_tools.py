
import sqlalchemy.exc
from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Covers
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Watches
from app.models import Publishers
from app.models import Ratings
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
from app import db
from app import app
import markdown
import bleach
import os.path
import os
import hashlib
from data_uri import DataURI
from flask_login import current_user
import datetime
import app.nameTools as nt

from sqlalchemy import or_
from sqlalchemy.sql import func

from flask import g
from flask import request

from app.api_common import getResponse
from app import tag_lut

def getCurrentUserId():
	'''
	if current_user == None, we're not executing within the normal flask runtime,
	which means we can probably assume that the caller is the system update
	service.
	'''
	if current_user != None:
		return current_user.id
	else:
		return app.config['SYSTEM_USERID']


def updateTitle(series, newTitle_raw):

	newTitle = bleach.clean(newTitle_raw.strip(), tags=[], strip=True)

	# Short circuit if nothing has changed.
	if newTitle == series.title:
		return

	conflict_series = Series.query.filter(Series.title==newTitle).scalar()

	if conflict_series and conflict_series.id != series.id:
		return getResponse("A series with that name already exists! Please choose another name", error=True)


	oldTitle          = series.title
	series.title      = newTitle
	series.changeuser = getCurrentUserId()
	series.changetime = datetime.datetime.now()

	ret = updateAltNames(series, [newTitle, oldTitle], deleteother=False)
	if ret:
		return ret

	return None

def updateTags(series, tags, deleteother=True, allow_new=True):
	havetags = Tags.query.filter((Tags.series==series.id)).all()
	havetags = {item.tag.lower() : item for item in havetags}

	tags = [tag.lower().strip().replace(" ", "-") for tag in tags]
	tags = [bleach.clean(item, strip=True) for item in tags]
	tags = [tag for tag in tags if tag.strip()]

	# Pipe through the fixer lut
	tags = [tag_lut.tag_fix_lut.get(tag, tag) for tag in tags]

	for tag in [n for n in tags]:
		if tag in tag_lut.tag_extend_lut:
			tags.append(tag_lut.tag_extend_lut[tag])

	tags = set(tags)

	for tag in tags:
		if tag in havetags:
			havetags.pop(tag)
		else:
			# If we're set to allow new, don't bother checking for other instances of the tag.
			if allow_new:
				newtag = Tags(series=series.id, tag=tag, changetime=datetime.datetime.now(), changeuser=getCurrentUserId())
				db.session.add(newtag)
			else:
				# Otherwise, make sure that tag already exists in the database before adding it.
				exists = Tags.query.filter((Tags.tag==tag)).count()
				if exists:
					newtag = Tags(series=series.id, tag=tag, changetime=datetime.datetime.now(), changeuser=getCurrentUserId())
					db.session.add(newtag)


	if deleteother:
		for dummy_key, value in havetags.items():
			db.session.delete(value)

	db.session.commit()

def updateGenres(series, genres, deleteother=True):
	havegenres = Genres.query.filter((Genres.series==series.id)).all()
	havegenres = {item.genre.lower() : item for item in havegenres}

	genres = [genre.lower().strip().replace(" ", "-") for genre in genres]
	genres = [bleach.clean(item, strip=True) for item in genres]
	genres = [genre for genre in genres if genre.strip()]
	for genre in genres:
		if genre in havegenres:
			havegenres.pop(genre)
		else:
			newgenre = Genres(series=series.id, genre=genre, changetime=datetime.datetime.now(), changeuser=getCurrentUserId())
			db.session.add(newgenre)
	if deleteother:
		for dummy_key, value in havegenres.items():
			db.session.delete(value)
	db.session.commit()

def updatePublishers(series, publishers, deleteother=True):
	havePublishers = Publishers.query.filter((Publishers.series==series.id)).all()
	havePublishers = {item.name.lower() : item for item in havePublishers}

	publishers = [publisher.strip() for publisher in publishers]
	publishers = [bleach.clean(item, strip=True) for item in publishers]
	publishers = [publisher for publisher in publishers if publisher.strip()]
	for publisher in publishers:
		if publisher.lower() in havePublishers:
			havePublishers.pop(publisher.lower())
		else:
			newgenre = Publishers(series=series.id, name=publisher, changetime=datetime.datetime.now(), changeuser=getCurrentUserId())
			db.session.add(newgenre)
	if deleteother:
		for dummy_key, value in havePublishers.items():
			db.session.delete(value)
	db.session.commit()


def updateAltNames(series, altnames, deleteother=True):
	# print("Alt names:", altnames)
	altnames = [name.strip() for name in altnames]
	cleaned = {}
	for name in altnames:
		if name.lower().strip():
			cleaned[name.lower().strip()] = name

	havenames = AlternateNames.query.filter(AlternateNames.series==series.id).order_by(AlternateNames.name).all()
	havenames = {bleach.clean(name.name.lower().strip(), strip=True) : name for name in havenames}

	for name in cleaned.keys():
		if name in havenames:
			havenames.pop(name)
		else:
			have = AlternateNames.query.filter(AlternateNames.series==series.id).filter(AlternateNames.name == cleaned[name]).count()
			if not have:
				newname = AlternateNames(
						name       = cleaned[name],
						cleanname  = nt.prepFilenameForMatching(cleaned[name]),
						series     = series.id,
						changetime = datetime.datetime.now(),
						changeuser = getCurrentUserId()
					)
				db.session.add(newname)

	if deleteother:
		for dummy_key, value in havenames.items():
			db.session.delete(value)
	db.session.commit()



def setAuthorIllust(series, author=None, illust=None, deleteother=True):
	# print(("setAuthorIllust: ", series, author, illust, deleteother))

	db.session.commit()

	if author and illust:
		return {'error' : True, 'message' : "How did both author and illustrator get passed here?"}
	elif author:
		table = Author
		values = author
	elif illust:
		table = Illustrators
		values = illust
	else:
		return {'error' : True, 'message' : "No parameters?"}

	have = table.query.filter(table.series==series.id).all()

	haveitems = {bleach.clean(item.name.lower().strip()) : item  for item  in have  }
	initems   = {bleach.clean(    value.lower().strip()) : value for value in values}

	for name in initems.keys():
		if name in haveitems:
			haveitems.pop(name)
		else:
			try:
				newentry = table(
						series     = series.id,
						name       = bleach.clean(initems[name], strip=True),
						changetime = datetime.datetime.now(),
						changeuser = getCurrentUserId()
					)
				db.session.add(newentry)
				db.session.commit()
			except sqlalchemy.exc.IntegrityError:
				db.session.rollback()
				print("Error adding name: %s (%s)" % (name, initems[name]))

	if deleteother:
		for key, value in haveitems.items():
			db.session.delete(value)

	db.session.commit()



def updateGroupAltNames(group, altnames, deleteother=True):
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
					name       = bleach.clean(cleaned[name], strip=True),
					cleanname  = nt.prepFilenameForMatching(cleaned[name]),
					group     = group.id,
					changetime = datetime.datetime.now(),
					changeuser = getCurrentUserId()
				)
			db.session.add(newname)

	if deleteother:
		for key, value in havenames.items():
			db.session.delete(value)
	db.session.commit()


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

	dirPath = os.path.join(app.config['COVER_DIR_BASE'], dirName)
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
	confpath = os.path.abspath(app.config['COVER_DIR_BASE'])

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


def get_identifier():
	if not g.user.is_anonymous():
		return g.user.id, None
	else:
		if request.headers.get('X-Forwarded-For'):
			return None, request.headers.get('X-Forwarded-For')
		else:
			return None, request.remote_addr


# def ci_lower_bound(pos, n)
# 	confidence = 1.96
# 	if n == 0
# 		return 0
# 	end
# 	z = Statistics2.pnormaldist(1-(1-confidence)/2)
# 	phat = 1.0*pos/n
# 	(phat + z*z/(2*n) - z * Math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)

def set_rating(sid, new_rating=None):

	if new_rating:
		uid, ip = get_identifier()
		print("Set-rating call for sid %s, uid %s, ip %s. Rating: %s" % (sid, uid, ip, new_rating))
		user_rtng = Ratings.query \
			.filter(Ratings.series_id == sid) \
			.filter(Ratings.user_id   == uid) \
			.filter(Ratings.source_ip == ip ) \
			.scalar()

		if user_rtng:
			user_rtng.rating = new_rating
		else:
			new_row = Ratings(
					rating    = new_rating,
					series_id = sid,
					user_id   = uid,
					source_ip = ip,
				)
			db.session.add(new_row)

		db.session.commit()

	# Now update the series row.
	s_ratings = Ratings.query \
		.filter(Ratings.series_id == sid) \
		.all()

	if s_ratings:
		ratings = [tmp.rating for tmp in s_ratings]
		newval  = sum(ratings) / len(ratings)
		rcnt    = len(ratings)
	else:
		newval = None
		rcnt   = None

	Series.query \
		.filter(Series.id == sid) \
		.update({'rating' : newval, 'rating_count' : rcnt})

	db.session.commit()

def get_rating(sid):
	uid, ip = get_identifier()
	user_rtng = Ratings.query \
		.filter(Ratings.series_id == sid) \
		.filter(Ratings.user_id   == uid) \
		.filter(Ratings.source_ip == ip ) \
		.scalar()

	# Funky tuple unpacking
	avg,   = db.session.query(Series.rating).filter(Series.id == sid).one()
	count, = db.session.query(func.count(Ratings.rating)).filter(Ratings.series_id == sid).one()
	user_rtng = -1 if user_rtng == None else user_rtng.rating

	# print("Rating - Average: %s from %s ratings, user-rating: %s" % (avg, count, user_rtng))
	# Rating return is the current user's rating, average rating, and the number of contributing ratings
	# for that average.
	ret = {
		"user" : user_rtng,
		"avg"  : avg,
		"num"  : count,
	}
	return ret
