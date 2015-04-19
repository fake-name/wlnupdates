from flask import g, jsonify, send_file, render_template, request
from flask.ext.login import login_required
# from guess_language import guess_language
from app import app, db, lm, oid, babel
from .forms import LoginForm, EditForm, PostForm, SearchForm
from .models import User, Post, Series, Tags, Genres, Author, Illustrators, Translators, Releases, Covers

import wtforms_json

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

	resp = jsonify(ret)
	resp.status_code = 200
	resp.mimetype="application/json"
	return resp


@app.route('/api', methods=['GET'])
def handleApiGet():
	return render_template('not-implemented-yet.html', message="API Endpoint requires a POST request.")

def dispatchApiCall(reqJson):
	print("Request JSON:", reqJson)
	ret = {
			"error"   : False,
			"message" : "Wattttt?"

	}

	return ret

