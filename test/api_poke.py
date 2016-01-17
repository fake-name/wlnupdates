
import logSetup
import webFunctions
# if __name__ == "__main__":
# 	logSetup.initLogging()


MODES = [
	# 'get-artists',
	# 'get-authors',
	# 'get-genres',
	# 'get-groups',
	# 'get-publishers',

	# 'get-cover-img',
	# 'get-search',

	# 'get-tags',

	# 'get-oel-releases',
	# 'get-releases',
	# 'get-translated-releases',

	'get-oel-series',
	'get-series',
	'get-translated-series',

	# 'get-watches',
	# 'get-artist-id',
	# 'get-author-id',
	# 'get-genre-id',
	# 'get-group-id',
	# 'get-publisher-id',
	# 'get-series-id',
	# 'get-tag-id',

	# 'get-feeds',
]

def test():
	wg = webFunctions.WebGetRobust()
	for mode in MODES:

		post = {
			'mode'   : mode,
			# 'id'     : 1,
		}
		print("Request: ", post)
		pg = wg.getpage("http://127.0.0.1:5000/api", postJson=post)
		print(pg)

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



if __name__ == "__main__":
	test()
