from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField, FormField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from .models import User

import wtforms

class LoginForm(Form):
	username =   StringField('Username', validators=[DataRequired(), Length(min=6)])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
	remember_me = BooleanField('remember_me', default=False)

class SignupForm(Form):
	username  =   StringField('Username', validators=[DataRequired(), Length(min=6)])
	password  = PasswordField('Password', validators=[DataRequired(), Length(min=8), EqualTo('pconfirm', "Your passwords must match")])
	pconfirm  = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=8)])
	email     =   StringField('Email Address', validators=[DataRequired(), Email()])





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
		if self.nickname.data != User.make_valid_nickname(self.nickname.data):
			self.nickname.errors.append(gettext(
				'This nickname has invalid characters. '
				'Please use letters, numbers, dots and underscores only.'))
			return False
		user = User.query.filter_by(nickname=self.nickname.data).first()
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

def processMangaUpdateJson(data):
	validateMangaData(data)



# {'value': '',
# 'type': 'singleitem',
# 'key': 'demographic-container'},

# {'value': 'Novel\n', 'type': 'singleitem', 'key': 'type-container'}, {'value': '', 'type': 'singleitem', 'key': 'origin_loc-container'}], 'mode': 'manga-update'}
