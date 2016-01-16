
from flask import jsonify
from flask import render_template
from flask import request
from flask.ext.login import current_user
import wtforms_json
from app import csrf

from app import app

from . import api_handlers
from . import api_handlers_admin
from . import api_handlers_anon

from app.api_common import getResponse
import traceback

wtforms_json.init()

LOGIN_REQ =  """
API Calls can only be made by a logged in user!<br>
<br>
If you are not logged in, please log in.<br>
<br>
If you do not have an account, you must create one in order to edit things or watch series."""


@csrf.exempt
@app.route('/api', methods=['POST'])
def handleApiPost():
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

@csrf.exempt
@app.route('/api', methods=['GET'])
def handleApiGet():
	return render_template('not-implemented-yet.html', message="API Endpoint requires a POST request.")



# call_name : (function_to_call, auth_required_bool, csrf_protect)
# CSRF protection is not needed if
DISPATCH_TABLE = {
	#
	'get-artist-id'             : (api_handlers_anon.get_artist_id,              False, False),
	'get-artists'               : (api_handlers_anon.get_artists,                False, False),
	'get-author-id'             : (api_handlers_anon.get_author_id,              False, False),
	'get-authors'               : (api_handlers_anon.get_authors,                False, False),
	'get-cover-img'             : (api_handlers_anon.get_cover_img,              False, False),
	'get-feeds'                 : (api_handlers_anon.get_feeds,                  False, False),
	'get-genre-id'              : (api_handlers_anon.get_genre_id,               False, False),
	'get-genres'                : (api_handlers_anon.get_genres,                 False, False),
	'get-group-id'              : (api_handlers_anon.get_group_id,               False, False),
	'get-groups'                : (api_handlers_anon.get_groups,                 False, False),
	'get-oel-releases'          : (api_handlers_anon.get_oel_releases,           False, False),
	'get-oel-series'            : (api_handlers_anon.get_oel_series,             False, False),
	'get-publisher-id'          : (api_handlers_anon.get_publisher_id,           False, False),
	'get-publishers'            : (api_handlers_anon.get_publishers,             False, False),
	'get-releases'              : (api_handlers_anon.get_releases,               False, False),
	'get-search'                : (api_handlers_anon.get_search,                 False, False),
	'get-series-id'             : (api_handlers_anon.get_series_id,              False, False),
	'get-series'                : (api_handlers_anon.get_series,                 False, False),
	'get-tag-id'                : (api_handlers_anon.get_tag_id,                 False, False),
	'get-tags'                  : (api_handlers_anon.get_tags,                   False, False),
	'get-translated-releases'   : (api_handlers_anon.get_translated_releases,    False, False),
	'get-translated-series'     : (api_handlers_anon.get_translated_series,      False, False),
	'get-watches'               : (api_handlers_anon.get_watches,                False, False),

	# Logged in stuff
	'manga-update'              : (api_handlers.processMangaUpdateJson,          True,  False),
	'group-update'              : (api_handlers.processGroupUpdateJson,          True,  False),
	'set-watch'                 : (api_handlers.setSeriesWatchJson,              True,  False),
	'read-update'               : (api_handlers.setReadingProgressJson,          True,  False),
	'cover-update'              : (api_handlers.updateAddCoversJson,             True,  False),
	'set-rating'                : (api_handlers.setRatingJson,                   False, True),

	# Admin API bits
	'merge-id'                  : (api_handlers_admin.mergeSeriesItems,          True,  False),
	'merge-group'               : (api_handlers_admin.mergeGroupItems,           True,  False),
	'release-ctrl'              : (api_handlers_admin.alterReleaseItem,          True,  False),
	'delete-series'             : (api_handlers_admin.deleteSeries,              True,  False),
	'delete-auto-releases'      : (api_handlers_admin.deleteAutoReleases,        True,  False),

	'flatten-series-by-url'     : (api_handlers_admin.flatten_series_by_url,     True,  False),
	'delete-duplicate-releases' : (api_handlers_admin.delete_duplicate_releases, True,  False),
	'fix-escapes'               : (api_handlers_admin.fix_escaped_quotes,        True,  False),
	'clean-tags'                : (api_handlers_admin.clean_tags,                True,  False),

}

def dispatchApiCall(reqJson):
	print("Json request:", reqJson)
	if not "mode" in reqJson:
		print("API JSON Request without mode!")
		return getResponse("No mode in API Request!", error=True)

	mode = reqJson["mode"]
	if not mode in DISPATCH_TABLE:
		print("Invalid mode in request: '{mode}'".format(mode=mode))
		return getResponse("Invalid mode in API Request ({mode})!".format(mode=mode), error=True)

	dispatch_method, auth_required, csrf_required = DISPATCH_TABLE[mode]
	try:
		if csrf_required:
			csrf.protect()

		if auth_required and not current_user.is_authenticated():
			return getResponse(LOGIN_REQ, error=True)

		else:
			ret = dispatch_method(reqJson)

	except AssertionError as e:
		traceback.print_exc()
		print(reqJson)
		return getResponse("Error processing API request: '%s'!" % e, error=True)



	return ret


