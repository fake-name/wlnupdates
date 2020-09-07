
import cachetools

from flask import jsonify
from flask import render_template
from flask import request
from flask_login import current_user
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



# These people look kinda like spammers, or are doing bizarre things.
weird_ips = [
		'101.173.145.176',
		'179.199.182.48',
	]

@csrf.exempt
@app.route('/api', methods=['POST'])
def handleApiPost():
	if not request.json:
		print("Non-JSON API Post!")
		js = {
			"error"   : True,
			"message" : "This endpoint only accepts JSON POST requests."
		}
		resp = jsonify(js)
		resp.status_code = 200
		resp.mimetype="application/json"
		return resp
	from_ip = request.headers.get('X-Forwarded-For', "Empty").strip()
	if from_ip in weird_ips:
		print("Bouncing IP with strange behaviour: %s" % (from_ip, ))
		# print("Non-JSON request!")
		js = {
			"error"   : True,
			"message" : "You're behaving weirdly or running a bot, so your api access privileges have been disabled. If you believe this is in error, please let me know at https://github.com/fake-name/wlnupdates/issues"
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



# call_name : (function_to_call, auth_required_bool, csrf_protect, rate_limit)
# CSRF protection is not needed if
DISPATCH_TABLE = {
	#
	# 'get'                       : (api_handlers_anon.get_listing,                       False, False),
	'do-login'                  : (api_handlers_anon.do_login,                          False, False, True),

	'get-artists'               : (api_handlers_anon.get_artists,                       False, False, True),
	'get-authors'               : (api_handlers_anon.get_authors,                       False, False, True),
	'get-genres'                : (api_handlers_anon.get_genres,                        False, False, True),
	'get-groups'                : (api_handlers_anon.get_groups,                        False, False, True),
	'get-oel-releases'          : (api_handlers_anon.get_oel_releases,                  False, False, True),
	'get-oel-series'            : (api_handlers_anon.get_oel_series,                    False, False, True),
	'get-publishers'            : (api_handlers_anon.get_publishers,                    False, False, True),
	'get-releases'              : (api_handlers_anon.get_releases,                      False, False, True),
	'get-series'                : (api_handlers_anon.get_series,                        False, False, True),
	'get-translated-releases'   : (api_handlers_anon.get_translated_releases,           False, False, True),
	'get-translated-series'     : (api_handlers_anon.get_translated_series,             False, False, True),

	'get-watches'               : (api_handlers_anon.get_watches,                       True,  False, True),
	'get-feeds'                 : (api_handlers_anon.get_feeds,                         False, False, True),

	'enumerate-tags'            : (api_handlers_anon.enumerate_search_tags,             False, False, True),
	'enumerate-genres'          : (api_handlers_anon.enumerate_search_genres,           False, False, True),

	'search-title'              : (api_handlers_anon.get_search_title,                  False, False, True),
	'search-advanced'           : (api_handlers_anon.get_search_advanced,               False, False, True),

	'get-artist-id'             : (api_handlers_anon.get_artist_id,                     False, False, True),
	'get-author-id'             : (api_handlers_anon.get_author_id,                     False, False, True),
	'get-genre-id'              : (api_handlers_anon.get_genre_id,                      False, False, True),
	'get-group-id'              : (api_handlers_anon.get_group_id,                      False, False, True),
	'get-publisher-id'          : (api_handlers_anon.get_publisher_id,                  False, False, True),
	'get-series-id'             : (api_handlers_anon.get_series_id,                     False, False, True),
	'get-series-data'           : (api_handlers_anon.get_series_id,                     False, False, True),
	'get-tag-id'                : (api_handlers_anon.get_tag_id,                        False, False, True),

	'get-artist-data'           : (api_handlers_anon.get_artist_id,                     False, False, True),
	'get-author-data'           : (api_handlers_anon.get_author_id,                     False, False, True),
	'get-genre-data'            : (api_handlers_anon.get_genre_id,                      False, False, True),
	'get-group-data'            : (api_handlers_anon.get_group_id,                      False, False, True),
	'get-publisher-data'        : (api_handlers_anon.get_publisher_id,                  False, False, True),
	'get-tag-data'              : (api_handlers_anon.get_tag_id,                        False, False, True),

	# Logged in stuff
	'series-update'             : (api_handlers.process_series_update_json,             True,  False, False),
	'release-update'            : (api_handlers.processReleaseUpdateJson,               True,  False, False),
	'group-update'              : (api_handlers.processGroupUpdateJson,                 True,  False, False),
	'set-watch'                 : (api_handlers.setSeriesWatchJson,                     True,  False, False),
	'read-update'               : (api_handlers.setReadingProgressJson,                 True,  False, False),
	'cover-update'              : (api_handlers.updateAddCoversJson,                    True,  False, False),
	'set-rating'                : (api_handlers.setRatingJson,                          False, True,  False),

	# Admin API bits
	'merge-id'                  : (api_handlers_admin.mergeSeriesItems,                 True,  False, False),
	'block-merge-id'            : (api_handlers_admin.preventMergeSeriesItems,          True,  False, False),

	'do-group-merge-id'         : (api_handlers_admin.mergeGroupEntries,                True,  False, False),
	'block-group-merge-id'      : (api_handlers_admin.preventMergeGroupEntries,         True,  False, False),

	'set-sort-mode'             : (api_handlers_admin.setSortOrder,                     True,  False, False),
	'merge-group'               : (api_handlers_admin.mergeGroupItems,                  True,  False, False),
	'release-ctrl'              : (api_handlers_admin.alterReleaseItem,                 True,  False, False),
	'delete-series'             : (api_handlers_admin.deleteSeries,                     True,  False, False),
	'delete-auto-releases'      : (api_handlers_admin.deleteAutoReleases,               True,  False, False),

	'flatten-series-by-url'     : (api_handlers_admin.flatten_series_by_url,            True,  False, False),
	'delete-duplicate-releases' : (api_handlers_admin.delete_duplicate_releases,        True,  False, False),
	'fix-escapes'               : (api_handlers_admin.fix_escaped_quotes,               True,  False, False),
	'clean-singleton-tags'      : (api_handlers_admin.clean_singleton_tags,             True,  False, False),

	'delete-group'              : (api_handlers_admin.deleteGroup,                      True,  False, False),
	'delete-auto-from-group'    : (api_handlers_admin.deleteGroupAutoReleases,          True,  False, False),
	'toggle-volume-releases'    : (api_handlers_admin.bulkToggleVolumeCountedStatus,    True,  False, False),

}

RATE_LIMITER = cachetools.TTLCache(maxsize = 1000 * 1000, ttl = 0.25)

def dispatchApiCall(reqJson):

	forwarded_for = request.headers.get('X-Forwarded-For', "Empty")

	# if forwarded_for == '108.28.56.67':
	# 	print("Bouncing possible abuse from %s" % (forwarded_for, ))
	# 	return getResponse("Hi there! Please contact me on github.com/fake-name/wlnupdates before doing bulk scraping, please!", error=True)

	if not "mode" in reqJson:
		print("API JSON Request without mode!")
		return getResponse("No mode in API Request!", error=True)

	mode = reqJson["mode"]
	if not mode in DISPATCH_TABLE:
		print("Invalid mode in request: '{mode}'".format(mode=mode))
		return getResponse("Invalid mode in API Request ({mode})!".format(mode=mode), error=True)

	ua = request.headers.get('User-Agent', "No user agent?")
	print("Api Post! Mode: '{}', Source IP: '{}', User agent: '{}'".format(mode, forwarded_for, ua))

	dispatch_method, auth_required, csrf_required, rate_limited = DISPATCH_TABLE[mode]
	try:
		if csrf_required:
			csrf.protect()

		if auth_required and not current_user.is_authenticated():
			return getResponse(LOGIN_REQ, error=True)

		if rate_limited and not current_user.is_authenticated():
			limiter_key = forwarded_for + " " + mode
			if limiter_key in RATE_LIMITER:
				print("Anon User hit rate limiting. Bouncing.")
				return getResponse("API calls when not logged in are rate limited. Please either log in, or slow down. "
					"Complain at github.com/fake-name/wlnupdates/issues if this is a problem", error=True)

			print("Inserting anon requester into rate-limit cache.")
			RATE_LIMITER[limiter_key] = True

			ret = dispatch_method(reqJson)

		else:
			ret = dispatch_method(reqJson)

	except AssertionError as e:
		traceback.print_exc()
		print(reqJson)
		return getResponse("Error processing API request: '%s'!" % e, error=True)



	return ret


