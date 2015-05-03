from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField, FormField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import Users
from flask.ext.bcrypt import check_password_hash
from app import db
from .models import Users, Post, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers
import markdown
import bleach
import wtforms
from flask.ext.login import current_user

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
	}

def validateMangaData(data):
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
			val['data'] = [entry.strip() for entry in item['value'].strip().split("\n")]
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


	#
	# releases     =     Releases.query.filter(Releases.series==sid).all()
	# covers       =       Covers.query.filter(Covers.series==sid).all()




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


		elif entry['type'] == 'demographic':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.demographic == processedData:
				print("No change?")
			else:
				series.demographic = processedData
				series.changeuser = current_user.id

		elif entry['type'] == 'type':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.type == processedData:
				print("No change?")
			else:
				series.type = processedData
				series.changeuser = current_user.id

		elif entry['type'] == 'origin_loc':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.origin_loc == processedData:
				print("No change?")
			else:
				series.origin_loc = processedData
				series.changeuser = current_user.id

		elif entry['type'] == 'orig_lang':
			processedData = bleach.clean(entry['data'], strip=True)
			if series.orig_lang == processedData:
				print("No change?")
			else:
				series.orig_lang = processedData
				series.changeuser = current_user.id

		elif entry['type'] == 'author':
			# author       =       Author.query.filter(Author.series==sid).all()
			pass
		elif entry['type'] == 'illustrators':
			# illustrators = Illustrators.query.filter(Illustrators.series==sid).all()
			pass
		elif entry['type'] == 'tag':
			tags = entry['data']
			print("tags:", tags)
			# tags         =         Tags.query.filter(Tags.series==sid).all()
			pass
		elif entry['type'] == 'genre':
			# genres       =       Genres.query.filter(Genres.series==sid).all()
			pass
		else:
			raise AssertionError("Unknown modifification type!")

	db.session.commit()

# {'value': '',
# 'type': 'singleitem',
# 'key': 'demographic-container'},

# {'value': 'Novel\n', 'type': 'singleitem', 'key': 'type-container'}, {'value': '', 'type': 'singleitem', 'key': 'origin_loc-container'}], 'mode': 'manga-update'}
