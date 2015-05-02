from flask import g, jsonify, send_file, render_template, request
from flask.ext.login import login_required
# from guess_language import guess_language
from app import app, db, lm, oid, babel
from . import forms
from .models import Users, Post, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers

import traceback

import wtforms_json
wtforms_json.init()

@app.route('/api', methods=['POST'])
def handleApiPost():
	print("API Call!")
	if not request.json:
		print("Non-JSON request!")
		js = {
			"error"   : True,
			"message" : "This endpoint only accepts JSON requests."
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
	'manga-update' : forms.processMangaUpdateJson

}

def dispatchApiCall(reqJson):
	if not "mode" in reqJson:
		return getError("No mode in API Request!")

	mode = reqJson["mode"]
	if not mode in DISPATCH_TABLE:
		return getError("Invalid mode in API Request!")

	decoder = DISPATCH_TABLE[mode]
	try:
		response = decoder(reqJson)
	except AssertionError:
		traceback.print_exc()
		return getError("Invalid data in API request!")

	ret = {
			"error"   : False,
			"message" : "Wat?!"
	}

	return ret


