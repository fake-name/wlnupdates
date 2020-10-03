
import json
import pprint
import webFunctions
import logSetup
# if __name__ == "__main__":
# 	logSetup.initLogging()


MODES = [
	# 'get-artists',
	# 'get-authors',
	# 'get-genres',
	# 'get-groups',
	# 'get-publishers',

	# 'get-tags',

	# 'get-releases',
	# 'get-oel-releases',
	# 'get-translated-releases',

	# 'get-oel-series',
	# 'get-series',
	# 'get-translated-series',


	# 'get-artist-id',
	# 'get-author-id',
	# 'get-tag-id',
	# 'get-genre-id',
	# 'get-publisher-id',
	# 'get-group-id',

	# 'get-artist-data',
	# 'get-author-data',
	# 'get-tag-data',
	# 'get-genre-data',
	# 'get-publisher-data',
	# 'get-group-data',

	'get-series-id',
	# 'get-series-data',

	# 'get-feeds',
	'get-watches',

	# 'enumerate-tags',
	# 'enumerate-genres',

	# 'search-title',
	# 'search-advanced',

]

endpoint = "http://127.0.0.1:5000/api"

def test():
	wg = webFunctions.WebGetRobust()

	# endpoint = "https://www.wlnupdates.com/api"

	# for mode in MODES:

	# 	post = {
	# 		'mode'   : mode,
	# 		'id'     : 231,
	# 	}
	# 	pprint.pprint("Request: ")
	# 	pprint.pprint(post)
	# 	pg = wg.getpage(endpoint, postJson=post)
	# 	pprint.pprint(json.loads(pg))

	# 	# for letter in "abcdefghijklmnopqrstuvwxyz0123456789":
	# 	# 	for page in range(4):
	# 	# 		post = {
	# 	# 			'mode'   : mode,
	# 	# 			'offset' : page+1,
	# 	# 			'prefix' : letter,
	# 	# 		}

	# 	# 		# post = {
	# 	# 		# 	'mode'   : mode,
	# 	# 		# 	# 'id'     : 1,
	# 	# 		# }
	# 	# 		print("Request: ", post)
	# 	# 		pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
	# 	# 		print(pg)



	# post = {
	# 	'mode'   : 'search-title',
	# 	'title'     : "",
	# }
	# print("Request: ", post)
	# pg = wg.getpage(endpoint, postJson=post)
	# print(pg)
	#


	post = {
		'mode'   : 'search-advanced',
		'series-type'  : {'Translated' : 'included'},
		'tag-category' : { 'ability-steal' : 'included', 'virtual-reality' : 'excluded' },
		'sort-mode' : "update",
		# 'chapter-limits' : [40, 0],
		# 'tag-category' : {
		# 	'litrpg' : 'included',
		# 	},
		# 'sort-mode' : "update",
		# 'title-search-text' : "Isekai",
		# 'chapter-limits' : [1, 0],
	}

	print("Request: ")
	pprint.pprint(post)
	pg = wg.getpage(endpoint, postJson=post)
	pg = json.loads(pg)
	pprint.pprint(pg)

	print("Results:", len(pg['data']))

	# include_options = ['covers', 'tags', 'genres', 'description']

	# for include in include_options:
	# 	post = {
	# 		'mode'   : 'search-advanced',
	# 		# 'series-type'  : {'Translated' : 'included'},
	# 		# 'tag-category' : {
	# 		# 	'litrpg' : 'included',
	# 		# 	},
	# 		'sort-mode' : "update",
	# 		'title-search-text' : "Fire Girl",
	# 		'chapter-limits' : [40, 0],
	# 		'include-results' : [include]
	# 	}
	# 	print("Request: ", post)
	# 	pg = wg.getpage(endpoint, postJson=post)
	# 	print(pg)

def watches_test():

	wg = webFunctions.WebGetRobust()

	post = {
		'mode'          : 'get-watches',
		'active-filter' : 'active',
	}
	print("Request: ", post)
	pg = wg.getpage(endpoint, postJson=post)
	pg = json.loads(pg)
	pprint.pprint(pg)


def login_test():
	wg = webFunctions.WebGetRobust()

	with open("login_secret.json") as fp:
		params = json.load(fp)

	post = {
		'mode'   : 'do-login',

		'username' : params['username'],
		'password' : params['password'],
		'remember_me' : True,

		# 'chapter-limits' : [40, 0],
		# 'tag-category' : {
		# 	'litrpg' : 'included',
		# 	},
		# 'sort-mode' : "update",
		# 'title-search-text' : "Isekai",
		# 'chapter-limits' : [1, 0],
	}

	print("Request: ")
	pprint.pprint(post)
	pg = wg.getpage(endpoint, postJson=post)
	pg = json.loads(pg)
	pprint.pprint(pg)


	print(params)

def other_poke():
	import requests
	headers = {'Content-Type': 'application/json'}
	url = "https://www.wlnupdates.com/api"
	payload = { "mode" : "search-advanced", "series-type" : {"Translated" : "included"}, "genre-category": {"harem" : "included"}, "tag-category": { "ability-steal" : "included", "virtual-reality" : "excluded" }, "sort-mode" : "update", "chapter-limits" : [40, 0], }
	response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
	json_data = response.json()
	print(len(json_data['data']))


if __name__ == "__main__":
	import logging
	logging.basicConfig(level=logging.DEBUG)
	other_poke()
	# login_test()
	# watches_test()
	# test()
