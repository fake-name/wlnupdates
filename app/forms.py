from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField, FormField, PasswordField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL
from .models import Users
from flask.ext.bcrypt import check_password_hash
from app import db
from app.models import Users
from app.models import Posts
from app.models import Series
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Releases
from app.models import Covers
from app.models import Watches
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
import markdown
import bleach
import wtforms
from flask.ext.login import current_user
import datetime
import app.nameTools as nt

def loginError():
	raise ValidationError("Your username or password is incorrect.")

class LoginForm(Form):
	username =   StringField('Username', validators=[DataRequired(), Length(min=5)])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
	remember_me = BooleanField('remember_me', default=False)

	# Validate on both the username and password,
	# because we don't want to accidentally leak if a user
	# exists or not
	def validate_password(form, field):
		user = Users.query.filter_by(nickname=form.username.data).first()
		if user is None:
			loginError()
		if not check_password_hash(user.password, form.password.data):
			loginError()

class SignupForm(Form):
	username  =   StringField('Username', validators=[DataRequired(), Length(min=5)])
	password  = PasswordField('Password', validators=[DataRequired(), Length(min=8), EqualTo('pconfirm', "Your passwords must match!")])
	pconfirm  = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=8)])
	email     =   StringField('Email Address', validators=[DataRequired(), Email()])

	def validate_username(form, field):
		user = Users.query.filter_by(nickname=field.data).first()
		if user is not None:
			raise ValidationError("That username is already used! Please choose another.")

class NewSeriesForm(Form):
	name =   StringField('Series Title', validators=[DataRequired(), Length(min=1)])

class NewGroupForm(Form):
	name  =   StringField('Group Name', validators=[DataRequired(), Length(min=1)])



def check_group(form, field):
	try:
		dat = int(field.data)
	except ValueError:
		raise ValidationError("Invalid group value! You must select a group.")
	if dat < 0:
		raise ValidationError("Invalid group value! You must select a group.")

def check_volume(form, field):
	if field.data:
		try:
			dat = int(field.data)
		except ValueError:
			raise ValidationError("Volume must be an integer value!")
	if not (field.data or form.chapter.data):
		raise ValidationError("Volume and chapter cannot both be empty!")


def check_chapter(form, field):
	if field.data:
		try:
			dat = int(field.data)
		except ValueError:
			raise ValidationError("Chapter must be an integer value!")
	if not (field.data or form.volume.data):
		raise ValidationError("Volume and chapter cannot both be empty!")

def check_sub_chapter(form, field):
	if field.data:
		try:
			dat = int(field.data)
		except ValueError:
			raise ValidationError("Sub-Chapter must be an integer value!")



class NewReleaseForm(Form):
	volume      = StringField('Volume', validators=[check_volume])
	chapter     = StringField('Chapter', validators=[check_chapter])
	subChap     = StringField('Sub-Chapter', validators=[check_sub_chapter])
	postfix     = StringField('Additional release titles', [Length(max=64)])
	group       = SelectField('Group', validators=[check_group], coerce=int)
	series_id   = HiddenField('series')
	release_pg  = StringField('Release URL', [URL(message='You must supply a link to the released chapter/volume.')])
	# releasetime = DateTimeField('Release Date/Time', format='%Y-%m-%dT%H:%M:%SZ')


# class EditForm(Form):
# 	nickname = StringField('nickname', validators=[DataRequired()])
# 	about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

# 	def __init__(self, original_nickname, *args, **kwargs):
# 		Form.__init__(self, *args, **kwargs)
# 		self.original_nickname = original_nickname

# 	def validate(self):
# 		if not Form.validate(self):
# 			return False
# 		if self.nickname.data == self.original_nickname:
# 			return True
# 		if self.nickname.data != Users.make_valid_nickname(self.nickname.data):
# 			self.nickname.errors.append(gettext(
# 				'This nickname has invalid characters. '
# 				'Please use letters, numbers, dots and underscores only.'))
# 			return False
# 		user = Users.query.filter_by(nickname=self.nickname.data).first()
# 		if user is not None:
# 			self.nickname.errors.append(gettext(
# 				'This nickname is already in use. '
# 				'Please choose another one.'))
# 			return False
# 		return True


# class PostForm(Form):
# 	post = StringField('post', validators=[DataRequired()])


class SearchForm(Form):
	search = StringField('search', validators=[DataRequired()])



VALID_KEYS = {
	'description-container'  : 'description',
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
	}
VALID_LICENSE_STATES = {
	"unknown" : None,
	"True"    : True,
	"False"   : False,
}

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
		assert itemType in ['singleitem', 'multiitem', 'combobox']

		if itemType == 'singleitem' or itemType == 'combobox':
			val['data'] = item['value'].strip()
		elif itemType == 'multiitem':
			tmp         = [entry.strip() for entry in item['value'].strip().split("\n")]
			val['data'] = [entry for entry in tmp if entry]
		else:
			raise AssertionError("Invalid item type!")

		if item['key'] not in VALID_KEYS:
			raise AssertionError("Invalid source key: '%s'!" % item['key'])
		else:
			val['type'] = VALID_KEYS[item['key']]

		update['entries'].append(val)

	# Ok, the JSON is valid, and we've more or less sanitized it.
	# Return the processed output.
	return update



def updateTags(series, tags):
	havetags = Tags.query.filter((Tags.series==series.id)).all()
	havetags = {item.tag.lower() : item for item in havetags}

	tags = [tag.lower().strip().replace(" ", "-") for tag in tags]
	tags = [tag for tag in tags if tag.strip()]
	for tag in tags:
		if tag in havetags:
			havetags.pop(tag)
		else:
			newtag = Tags(series=series.id, tag=tag, changetime=datetime.datetime.now(), changeuser=current_user.id)
			db.session.add(newtag)

	for key, value in havetags.items():
		db.session.delete(value)
	db.session.commit()

def updateGenres(series, genres):
	havegenres = Genres.query.filter((Genres.series==series.id)).all()
	havegenres = {item.genre.lower() : item for item in havegenres}

	genres = [genre.lower().strip().replace(" ", "-") for genre in genres]
	genres = [genre for genre in genres if genre.strip()]
	for genre in genres:
		if genre in havegenres:
			havegenres.pop(genre)
		else:
			newgenre = Genres(series=series.id, genre=genre, changetime=datetime.datetime.now(), changeuser=current_user.id)
			db.session.add(newgenre)

	for key, value in havegenres.items():
		db.session.delete(value)
	db.session.commit()


def updateAltNames(series, altnames):
	# print("Alt names:", altnames)
	altnames = [name.strip() for name in altnames]
	cleaned = {}
	for name in altnames:
		if name.lower().strip():
			cleaned[name.lower().strip()] = name

	havenames = AlternateNames.query.filter(AlternateNames.series==series.id).order_by(AlternateNames.name).all()
	havenames = {name.name.lower().strip() : name for name in havenames}

	for name in cleaned.keys():
		if name in havenames:
			havenames.pop(name)
		else:
			newname = AlternateNames(
					name       = cleaned[name],
					cleanname  = nt.prepFilenameForMatching(cleaned[name]),
					series     = series.id,
					changetime = datetime.datetime.now(),
					changeuser = current_user.id
				)
			db.session.add(newname)

	for key, value in havenames.items():
		db.session.delete(value)
	db.session.commit()



def setAuthorIllust(series, author=None, illust=None):
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
	# print(have)

	haveitems = {item.name.lower().strip() : item for item in have}
	initems   = {    value.lower().strip() : value for value in values}


	for name in initems.keys():
		if name in haveitems:
			haveitems.pop(name)
		else:
			newentry = table(
					series     = series.id,
					name       = initems[name],
					changetime = datetime.datetime.now(),
					changeuser = current_user.id
				)
			db.session.add(newentry)

	for key, value in haveitems.items():
		db.session.delete(value)

	db.session.commit()



def processMangaUpdateJson(data):
	validated = validateMangaData(data)

	sid = validated['id']
	series = Series.query.filter(Series.id==sid).one()
	print(validated)

	for entry in validated['entries']:
		# print(entry)
		if entry['type'] == 'description':
			processedData = markdown.markdown(bleach.clean(entry['data'], strip=True))
			if series.description == processedData:
				# print("No change?")
				pass
			else:
				series.description = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()


		elif entry['type'] == 'demographic':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				# print("No change?")
				pass
			else:
				series.demographic = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'region':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				# print("No change?")
				pass
			else:
				series.region = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'license_en':
			lic_state = entry['data']

			if lic_state not in VALID_LICENSE_STATES:
				raise ValueError("Invalid license data!")
			else:
				lic_state = VALID_LICENSE_STATES[lic_state]

			series.license_en = lic_state
			series.changeuser = current_user.id
			series.changetime = datetime.datetime.now()


			# if series.demographic == processedData:
			# 	# print("No change?")
			# 	pass
			# else:
			# 	series.region = processedData
			# 	series.changeuser = current_user.id
			# 	series.changetime = datetime.datetime.now()

		elif entry['type'] == 'type':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.type == processedData:
				# print("No change?")
				pass
			else:
				series.type = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'origin_loc':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.origin_loc == processedData:
				# print("No change?")
				pass
			else:
				series.origin_loc = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'orig_lang':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.orig_lang == processedData:
				# print("No change?")
				pass
			else:
				series.orig_lang = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'author':
			ret = setAuthorIllust(series, author=entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'illustrators':
			ret = setAuthorIllust(series, illust=entry['data'])
			if ret:
				return ret

		elif entry['type'] == 'tag':
			updateTags(series, entry['data'])

		elif entry['type'] == 'genre':
			updateGenres(series, entry['data'])

		elif entry['type'] == 'alternate-names':
			updateAltNames(series, entry['data'])
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
		update['listName'] = bleach.clean(str(data['list']), strip=True)
	except ValueError:
		raise AssertionError
	if len(update['listName']) > 256:
		raise AssertionError

	# Ok, the JSON is valid, and we've more or less sanitized it.
	# Return the processed output.
	return update


def setSeriesWatchJson(data):
	cleaned = validateWatchedData(data)

	watch_row = Watches.query.filter(
			(Watches.user_id==current_user.id) &
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
			user_id   = current_user.id,
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



def updateGroupAltNames(group, altnames):
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
					group     = group.id,
					changetime = datetime.datetime.now(),
					changeuser = current_user.id
				)
			db.session.add(newname)

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
		vol  = int(inDat['vol'])
		chp  = int(inDat['chp'])
		frag = int(inDat['frag'])
		sid  = int(inDat['item-id'])
	except ValueError:
		raise AssertionError("Volume, chapter, and fragment must be integers!")

	if any([item < 0 for item in (vol, chp, frag)]):
		raise AssertionError("Values cannot be lower then 0!")

	if frag > 99:
		raise AssertionError("A chapter can only have a maximum of 99 fragments!")

	chp += frag / 100.0


	return sid, (vol, chp)

def setReadingProgressJson(data):
	sid, progress = validateReadingProgressData(data)

	watch_row = Watches.query.filter(
			(Watches.user_id==current_user.id) &
			(Watches.series_id==sid)
		).one()

	vol, chp = progress

	if chp == 0 and vol == 0:
		vol = -1
		chp = -1

	if vol == 0:
		vol = -1

	watch_row.volume  = vol
	watch_row.chapter = chp
	db.session.commit()

	# sid = validated['id']
	# group = Translators.query.filter(Translators.id==sid).one()

	# for entry in validated['entries']:
	# 	print(entry)

	# 	if entry['type'] == 'alternate-names':
	# 		updateGroupAltNames(group, entry['data'])
	# 	else:
	# 		raise AssertionError("Unknown modifification type!")

	ret = {
			"error"   : False,
			"message" : "Wat?!"
	}
	return ret



# {'value': '',
# 'type': 'singleitem',
# 'key': 'demographic-container'},

# {'value': 'Novel\n', 'type': 'singleitem', 'key': 'type-container'}, {'value': '', 'type': 'singleitem', 'key': 'origin_loc-container'}], 'mode': 'manga-update'}
