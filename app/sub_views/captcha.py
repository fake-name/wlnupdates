# From https://github.com/Tethik/flask-session-captcha
# Forked because you can't silence a raise RuntimeWarning, apparently.

import base64
from random import SystemRandom
import logging

from captcha.image import ImageCaptcha
from flask import session, request, Markup

class FlaskSessionCaptcha(object):

	def __init__(self, app=None):
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		"""
		Initialize the captcha extension to the given app object.
		"""
		self.enabled = app.config.get("CAPTCHA_ENABLE", True)
		self.digits = app.config.get("CAPTCHA_LENGTH", 4)
		self.max = 10**self.digits
		self.image_generator = ImageCaptcha()
		self.rand = SystemRandom()

		def _generate():
			if not self.enabled:
				return ""
			base64_captcha = self.generate()
			return Markup("<img src='{}'>".format("data:image/png;base64, {}".format(base64_captcha)))

		app.jinja_env.globals['captcha'] = _generate

		# Check for sessions that do not persist on the server. Issue a warning because they are most likely open to replay attacks.
		# This addon is built upon flask-session.
		session_type = app.config.get('SESSION_TYPE', None)
		if session_type is None or session_type == "null":
			pass
			# raise RuntimeWarning("Flask-Sessionstore is not set to use a server persistent storage type. This likely means that captchas are vulnerable to replay attacks.")
		elif session_type == "sqlalchemy":
			# I have to do this as of version 0.3.1 of flask-session if using sqlalchemy as the session type in order to create the initial database.
			# Flask-sessionstore seems to have the same problem.
			app.session_interface.db.create_all()


	def generate(self):
		"""
		Generates and returns a numeric captcha image in base64 format.
		Saves the correct answer in `session['captcha_answer']`
		Use later as:

		src = captcha.generate()
		<img src="{{src}}">
		"""
		answer = self.rand.randrange(self.max)
		answer = str(answer).zfill(self.digits)
		image_data = self.image_generator.generate(answer)
		base64_captcha = base64.b64encode(image_data.getvalue()).decode("ascii")
		logging.debug('Generated captcha with answer: ' + answer)
		session['captcha_answer'] = answer
		return base64_captcha


	def validate(self, form_key="captcha", value=None):
		"""
		Validate a captcha answer (taken from request.form) against the answer saved in the session.
		Returns always true if CAPTCHA_ENABLE is set to False. Otherwise return true only if it is the correct answer.
		"""
		if not self.enabled:
			return True

		session_value = session.get('captcha_answer', None)
		if not session_value:
			return False

		if not value and form_key in request.form:
			value = request.form[form_key].strip()

		# invalidate the answer to stop new tries on the same challenge.
		session['captcha_answer'] = None
		return value and value == session_value

	def get_answer(self):
		"""
		Shortcut function that returns the currently saved answer.
		"""
		return session.get('captcha_answer', None)
