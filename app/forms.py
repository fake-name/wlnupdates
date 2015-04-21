from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from .models import User

import wtforms

class LoginForm(Form):
	openid = StringField('openid', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)


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
	ctype    = wtforms.StringField('ctype',   validators=[DataRequired()])
	contents = wtforms.StringField('contents')
	type     = wtforms.StringField('type',     validators=[DataRequired()])
	mode     = wtforms.StringField('mode',     validators=[DataRequired()])
	# blah   = wtforms.StringField('blah',     validators=[DataRequired()])
