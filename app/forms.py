
import binascii
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import BooleanField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import HiddenField
from wtforms.fields import RadioField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import ValidationError
from wtforms.validators import URL
from .models import Users
from .bcrypt_wrapper import check_password_hash
from app.models import Users
from app import db

def loginError():
	raise ValidationError("Your username or password is incorrect.")

def validate_login_password(username, password):
	user = Users.query.filter_by(nickname=username).first()
	if user is None:
		loginError()

	# Handle flask's new annoying way of mis-packing password strings. Sigh.
	if user.password.startswith("\\x"):
		print("Mis-packed password! Fixing!")
		old = user.password
		user.password = binascii.unhexlify(user.password[2:]).decode("utf-8")
		print("Old: ", old, "new: ", user.password)
		db.session.commit()

	if not check_password_hash(user.password.encode("UTF-8"), password.encode("UTF-8")):
		loginError()



class LoginForm(FlaskForm):
	username    = StringField('Username', validators=[DataRequired(), Length(min=5)])
	password    = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
	remember_me = BooleanField('remember_me', default=False)

	# Validate on both the username and password,
	# because we don't want to accidentally leak if a user
	# exists or not
	def validate_password(form, field):
		validate_login_password(username=form.username.data, password=form.password.data)

class SignupForm(FlaskForm):
	username  =   StringField('Username', validators=[DataRequired(), Length(min=5)])
	password  = PasswordField('Password', validators=[DataRequired(), Length(min=8), EqualTo('pconfirm', "Your passwords must match!")])
	pconfirm  = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=8)])
	email     =   StringField('Email Address', validators=[DataRequired(), Email()])

	def validate_username(form, field):
		user = Users.query.filter_by(nickname=field.data).first()
		if user is not None:
			raise ValidationError("That username is already used! Please choose another.")

class NewSeriesForm(FlaskForm):
	name =   StringField('Series Title', validators=[DataRequired(), Length(min=1)])
	type =   RadioField( 'Series Type',
				validators=[DataRequired(message='You must supply select a type.')],
				choices=[('oel', 'OEL - (original english language)'), ('translated', 'Translated')])

class NewGroupForm(FlaskForm):
	name  =   StringField('Group Name', validators=[DataRequired(), Length(min=1)])



def check_group(form, field):

	try:
		dat = int(field.data)
	except ValueError:
		raise ValidationError("Invalid group value! You must select a group.")
	if dat < 0:
		raise ValidationError("Invalid group value! You must select a group.")
	print("group validated")

def check_volume(form, field):
	if field.data:
		try:
			dat = float(field.data)
		except ValueError:
			raise ValidationError("Volume must be an numeric value!")
	if not (field.data or form.chapter.data):
		raise ValidationError("Volume and chapter cannot both be empty!")


def check_chapter(form, field):
	if field.data:
		try:
			dat = float(field.data)
		except ValueError:
			raise ValidationError("Chapter must be an numeric value!")
	if not (field.data or form.volume.data):
		raise ValidationError("Volume and chapter cannot both be empty!")

def check_sub_chapter(form, field):
	if field.data:
		try:
			dat = float(field.data)
		except ValueError:
			raise ValidationError("Sub-Chapter must be an numeric value!")



class NewReleaseForm(FlaskForm):
	volume      = StringField('Volume', validators=[check_volume])
	chapter     = StringField('Chapter', validators=[check_chapter])
	subChap     = StringField('Sub-Chapter', validators=[check_sub_chapter])
	postfix     = StringField('Additional release titles', [Length(max=64)])
	group       = SelectField('Group', validators=[check_group], coerce=int, default=-1)
	series_id   = HiddenField('series')
	is_oel      = HiddenField('is_oel')
	release_pg  = StringField('Release URL', [URL(message='You must supply a link to the released chapter/volume.')])
	releasetime = DateTimeField('Release Date', format='%Y/%m/%d %H:%M')


# class EditForm(FlaskForm):
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


class PostForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired(), Length(max=128)])
	content = TextAreaField('Content', validators=[DataRequired()])


class SearchForm(FlaskForm):
	search = StringField('search', validators=[DataRequired()])

