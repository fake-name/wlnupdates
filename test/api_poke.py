
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
	# 'get-watches',

	# 'enumerate-tags',
	# 'enumerate-genres',

	# 'search-title',
	# 'search-advanced',

]

def test():
	wg = webFunctions.WebGetRobust()

	endpoint = "http://127.0.0.1:5000/api"
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


	post = {
		'mode'   : 'search-advanced',
		# 'series-type'  : {'Translated' : 'included'},
		# 'tag-category' : {
		# 	'litrpg' : 'included',
		# 	},
		# 'sort-mode' : "update",
		'title-search-text' : "Isekai",
		# 'chapter-limits' : [1, 0],
	}

	print("Request: ")
	pprint.pprint(post)
	pg = wg.getpage(endpoint, postJson=post)
	pprint.pprint(pg)

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

if __name__ == "__main__":
	test()
