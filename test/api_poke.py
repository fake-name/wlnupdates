
import logSetup
import json
import webFunctions
# if __name__ == "__main__":
# 	logSetup.initLogging()


MODES = [
	'get-artists',
	'get-authors',
	'get-genres',
	'get-groups',
	'get-publishers',

	'get-tags',

	'get-oel-releases',
	'get-releases',
	'get-translated-releases',

	'get-oel-series',
	'get-series',
	'get-translated-series',


	'get-artist-id',
	'get-author-id',
	'get-tag-id',
	'get-genre-id',
	'get-publisher-id',
	'get-group-id',

	'get-series-id',

	'get-feeds',
	'get-watches',

	'search-advanced',
	'enumerate-tags',
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



	post = {
		'mode'   : 'search-title',
		'title'     : "The Book Eating Magician",
	}
	print("Request: ", post)
	pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
	print(pg)

	post = {
		'mode'   : 'search-advanced',
		'series-type'  : {'Translated' : 'included'},
		'tag-category' : {
			'ability-steal' : 'included',
			'virtual-reality' : 'excluded'
			},
		'sort-mode' : "update",
		'chapter-limits' : [40, 0],
	}
	print("Request: ", post)
	pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
	print(pg)


if __name__ == "__main__":
	test()
