from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField, FormField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import Users
from flask.ext.bcrypt import check_password_hash
from app import db
from .models import Users, Posts, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers, Watches, AlternateNames
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



class EditForm(Form):
	nickname = StringField('nickname', validators=[DataRequired()])
	about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

	def __init__(self, original_nickname, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.original_nickname = original_nickname

	def validate(self):
		if not Form.validate(self):
			return False
		if self.nickname.data == self.original_nickname:
			return True
		if self.nickname.data != Users.make_valid_nickname(self.nickname.data):
			self.nickname.errors.append(gettext(
				'This nickname has invalid characters. '
				'Please use letters, numbers, dots and underscores only.'))
			return False
		user = Users.query.filter_by(nickname=self.nickname.data).first()
		if user is not None:
			self.nickname.errors.append(gettext(
				'This nickname is already in use. '
				'Please choose another one.'))
			return False
		return True


class PostForm(Form):
	post = StringField('post', validators=[DataRequired()])


class SearchForm(Form):
	search = StringField('search', validators=[DataRequired()])




class SeriesUpdate(Form):
	mangaId  = wtforms.IntegerField('mangaId', validators=[DataRequired()])
	mode     = wtforms.StringField('mode',     validators=[DataRequired()])
	entries  = wtforms.StringField('entries',  validators=[DataRequired()])


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
	}

def validateMangaData(data):
	print("Manga Data:", data)
	assert "entries" in data
	assert "mangaId" in data

	try:
		itemId = int(data['mangaId'])
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
		assert itemType in ['singleitem', 'multiitem']

		if itemType == 'singleitem':
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
	print("Alt names:", altnames)
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
	print(have)

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

	for entry in validated['entries']:
		print(entry)
		if entry['type'] == 'description':
			processedData = markdown.markdown(bleach.clean(entry['data'], strip=True))
			if series.description == processedData:
				print("No change?")
			else:
				series.description = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()


		elif entry['type'] == 'demographic':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				print("No change?")
			else:
				series.demographic = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'type':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.type == processedData:
				print("No change?")
			else:
				series.type = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'origin_loc':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.origin_loc == processedData:
				print("No change?")
			else:
				series.origin_loc = processedData
				series.changeuser = current_user.id
				series.changetime = datetime.datetime.now()

		elif entry['type'] == 'orig_lang':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.orig_lang == processedData:
				print("No change?")
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

# {'watch': True, 'mode': 'set-watch', 'mangaId': '1857', 'list': 'watched'}

def validateWatchedData(data):
	assert "watch" in data
	assert "list" in data
	assert "mangaId" in data

	update = {}
	try:
		update['watch'] = bool(data['watch'])
	except ValueError:
		raise AssertionError

	try:
		update['mangaId'] = int(data['mangaId'])
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
			(Watches.series_id==cleaned['mangaId'])
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
			series_id = cleaned['mangaId'],
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


# {'value': '',
# 'type': 'singleitem',
# 'key': 'demographic-container'},

# {'value': 'Novel\n', 'type': 'singleitem', 'key': 'type-container'}, {'value': '', 'type': 'singleitem', 'key': 'origin_loc-container'}], 'mode': 'manga-update'}
