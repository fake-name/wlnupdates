from flask_wtf import FlaskForm
from wtforms import SubmitField, TextField, TextAreaField
from wtforms.validators import Required
from wtforms.validators import Length

title_error_message_missing = "You have to provide a thread title!"
title_error_message_length  = "Thread titles can only be up to 80 characters long!"
body_error_message          = "You have to enter content for your post!"
class CreateThreadForm(FlaskForm):
	name = TextField(validators=[Required(message=title_error_message_missing), Length(max=80, message=title_error_message_length)])
	content = TextAreaField(validators=[Required(message=body_error_message)])
	submit = SubmitField()


class CreatePostForm(FlaskForm):
	content = TextAreaField(validators=[Required(message=body_error_message)])
	submit = SubmitField()


class EditPostForm(CreatePostForm):
	pass
