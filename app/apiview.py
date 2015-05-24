from flask import g, jsonify, send_file, render_template, request
from flask.ext.login import login_required, current_user
# from guess_language import guess_language
from app import app, db, lm, babel
from . import forms
from .models import Users, Posts, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers

import traceback

import wtforms_json
wtforms_json.init()

@app.route('/api', methods=['POST'])
def handleApiPost():
	if not current_user.is_authenticated():
		js = {
			"error"   : True,
			"message" : """
API Calls can only be made by a logged in user!

If you are not logged in, please log in.

If you do not have an account, you must create one in order to edit things or watch series."""
		}
		resp = jsonify(js)
		resp.status_code = 200
		resp.mimetype="application/json"
		return resp

	if not request.json:
		# print("Non-JSON request!")
		js = {
			"error"   : True,
			"message" : "This endpoint only accepts JSON POST requests."
		}
		resp = jsonify(js)
		resp.status_code = 200
		resp.mimetype="application/json"
		return resp

	ret = dispatchApiCall(request.json)

	assert "error"   in ret, ("API Response missing status code!")
	assert "message" in ret, ("API Response missing status message!")

	resp = jsonify(ret)
	resp.status_code = 200
	resp.mimetype="application/json"
	return resp


@app.route('/api', methods=['GET'])
def handleApiGet():
	return render_template('not-implemented-yet.html', message="API Endpoint requires a POST request.")


def getError(message):
	ret = {
		'error'   : True,
		'message' : message
	}
	return ret

DISPATCH_TABLE = {
	'manga-update' : forms.processMangaUpdateJson,
	'group-update' : forms.processGroupUpdateJson,
	'set-watch'    : forms.setSeriesWatchJson,
	'read-update'  : forms.setReadingProgressJson,
}

def dispatchApiCall(reqJson):
	# print("Json request:", reqJson)
	if not "mode" in reqJson:
		return getError("No mode in API Request!")

	mode = reqJson["mode"]
	if not mode in DISPATCH_TABLE:
		return getError("Invalid mode in API Request!")

	dispatch_method = DISPATCH_TABLE[mode]
	try:
		ret = dispatch_method(reqJson)

	except AssertionError:
		traceback.print_exc()
		print(reqJson)
		return getError("Invalid data in API request!")



	return ret


