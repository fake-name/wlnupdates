
import logSetup
import json
import webFunctions
# if __name__ == "__main__":
# 	logSetup.initLogging()


MODES = [
	# 'get-artists',
	# 'get-authors',
	# 'get-genres',
	# 'get-groups',
	# 'get-publishers',

	# 'get-tags',

	# 'get-oel-releases',
	# 'get-releases',
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
	#
	# 'get-artist-data',
	# 'get-author-data',
	# 'get-tag-data',
	# 'get-genre-data',
	# 'get-publisher-data',
	# 'get-group-data',

	# 'get-series-id',
	# 'get-series-data',

	# 'get-feeds',
	# 'get-watches',

	# 'search-title',
	# 'search-advanced',
	# 'enumerate-tags',
]

def test():
	wg = webFunctions.WebGetRobust()
	for mode in MODES:

		post = {
			'mode'   : mode,
			'id'     : 3,
		}
		print("Request: ", post)
		pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
		print(json.loads(pg))

		# for letter in "abcdefghijklmnopqrstuvwxyz0123456789":
		# 	for page in range(4):
		# 		post = {
		# 			'mode'   : mode,
		# 			'offset' : page+1,
		# 			'prefix' : letter,
		# 		}

		# 		# post = {
		# 		# 	'mode'   : mode,
		# 		# 	# 'id'     : 1,
		# 		# }
		# 		print("Request: ", post)
		# 		pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
		# 		print(pg)



	# post = {
	# 	'mode'   : 'search-title',
	# 	'title'     : "",
	# }
	# print("Request: ", post)
	# pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
	# print(pg)

	post = {
		'mode'   : 'search-advanced',
		# 'series-type'  : {'Translated' : 'included'},
		# 'tag-category' : {
		# 	'litrpg' : 'included',
		# 	},
		'sort-mode' : "update",
		'title-search-text' : "Fire Girl",
		'chapter-limits' : [40, 0],
	}
	print("Request: ", post)
	pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
	print(pg)


if __name__ == "__main__":
	test()
