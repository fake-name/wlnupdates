#!python
import sys
import time
import datetime
import bleach
import markdown
import app.nameTools as nt
import settings
import psycopg2

move_to_con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
import_con = psycopg2.connect(host=settings.IMPORT_DATABASE_IP, dbname=settings.IMPORT_DATABASE_DB_NAME, user=settings.IMPORT_DATABASE_USER,password=settings.IMPORT_DATABASE_PASS)

def getItemEntry():
	item = {
		'name'     : '',
		'desc'     : '',
		'type'     : '',
		'demo'     : '',
		'author'   : [],
		'illust'   : [],
		'tags'     : [],
		'genre'    : [],
		'altnames' : [],
		'covers'   : [],
	}
	return item


def processMngSeries(cur, name, srcTable):
	cur.execute("""
		SELECT
			dbid,
			buname,
			buid,
			butags,
			bugenre,
			bulist,
			buartist,
			buauthor,
			buoriginstate,
			budescription,
			burelstate,
			readingprogress,
			availprogress,
			rating,
			lastchanged,
			lastchecked,
			itemadded,
			butype
		FROM {tableName}
		WHERE
			buname=%s
		;
		""".format(tableName=srcTable), (name, ))
	data = cur.fetchall()
	if not data or len(data) != 1:
		print(srcTable, data, name)
		return
	structure = [
			'dbid',
			'buname',
			'buid',
			'butags',
			'bugenre',
			'bulist',
			'buartist',
			'buauthor',
			'buoriginstate',
			'budescription',
			'burelstate',
			'readingprogress',
			'availprogress',
			'rating',
			'lastchanged',
			'lastchecked',
			'itemadded',
			'butype'
	]
	row = dict(zip(structure, data[0]))

	for key in list(row.keys()):
		if not row[key]:
			row[key] = ''

	item = getItemEntry()


	item['name']   = row['buname'].replace('(Novel)', '').strip()
	item['desc']   = markdown.markdown(bleach.clean(row['budescription'], strip=True))
	item['type']   = row['butype']
	item['demo']   = ''
	item['tags']   = row['butags'].split(" ")
	item['genre']  = row['bugenre'].split(" ")
	item['author'] = row['buauthor'].split(", ")
	item['illust'] = row['buartist'].split(", ")


	while "" in item['genre']: item['genre'].remove("")
	while "" in item['tags']: item['tags'].remove("")

	cur.execute("""SELECT name FROM munamelist WHERE buid=%s""", (row['buid'], ))

	alts =[item['name']]
	for alt, in cur.fetchall():
		if alt.endswith("(Novel)"):
			alt = alt.replace("(Novel)", "").strip()
		alts.append(alt)

	item['altnames'] = alts


	cur.execute("""
		SELECT
			filename, vol, chapter, description, relpath, filehash
		FROM
			series_covers
		WHERE
				srctable=%s
			AND
				srcid=%s
		ORDER BY
			vol, chapter, filename
		;
		""", (srcTable, row['dbid']))

	covers = cur.fetchall()

	item['covers'] = covers

	return item

def processBookTbl(cur, name, srcTable):
	cur.execute("""
		SELECT
			dbid,
			changestate,
			ctitle,
			cleanedtitle,
			otitle,
			vtitle,
			jtitle,
			jvtitle,
			series,
			pub,
			label,
			volno,
			author,
			illust,
			target,
			description,
			seriesentry,
			covers,
			reldate,
			lastchanged,
			lastchecked,
			firstseen
		FROM {tableName}
		WHERE
			ctitle=%s
		;
		""".format(tableName=srcTable), (name, ))
	data = cur.fetchall()
	if not data or len(data) != 1:
		print(srcTable, data, name)
		return False

	structure = [
			'dbid',
			'changestate',
			'ctitle',
			'cleanedtitle',
			'otitle',
			'vtitle',
			'jtitle',
			'jvtitle',
			'series',
			'pub',
			'label',
			'volno',
			'author',
			'illust',
			'target',
			'description',
			'seriesentry',
			'covers',
			'reldate',
			'lastchanged',
			'lastchecked',
			'firstseen'
	]

	row = dict(zip(structure, data[0]))

	for key in list(row.keys()):
		if not row[key]:
			row[key] = ''

	item = getItemEntry()


	item['name']   = row['ctitle']
	item['desc']   = row['description']
	item['type']   = ''
	item['demo']   = row['target']
	item['tags']   = []
	item['genre']  = []
	item['author'] = row['author'].split(", ")
	item['illust'] = row['illust'].split(", ")
	item['altnames'] = [item['name']]


	cur.execute("""
		SELECT
			filename, vol, chapter, description, relpath, filehash
		FROM
			series_covers
		WHERE
				srctable=%s
			AND
				srcid=%s
		;
		""", (srcTable, row['dbid']))

	covers = cur.fetchall()

	item['covers'] = covers

	return item

# --------+---------------------+----------+---------
#  public | author              | table    | wlnuser
#  public | author_id_seq       | sequence | wlnuser
#  public | followers           | table    | wlnuser
#  public | genres              | table    | wlnuser
#  public | genres_id_seq       | sequence | wlnuser
#  public | illustrators        | table    | wlnuser
#  public | illustrators_id_seq | sequence | wlnuser
#  public | migrate_version     | table    | wlnuser
#  public | post                | table    | wlnuser
#  public | post_id_seq         | sequence | wlnuser
#  public | releases            | table    | wlnuser
#  public | releases_id_seq     | sequence | wlnuser
#  public | series              | table    | wlnuser
#  public | series_id_seq       | sequence | wlnuser
#  public | translators         | table    | wlnuser
#  public | translators_id_seq  | sequence | wlnuser
#  public | user                | table    | wlnuser
#  public | user_id_seq         | sequence | wlnuser

#    Column    |  Type   |                      Modifiers
# -------------+---------+-----------------------------------------------------
#  id          | integer | not null default nextval('series_id_seq'::regclass)
#  description | text    |
#  type        | text    |
#  origin_loc  | text    |
#  demographic | text    |
#  title       | text    |


def insertItem(cur, item):
	cur.execute('''INSERT INTO series (title, description, type, demographic, changeuser, changetime) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;''',
			(
				item['name'],
				item['desc'],
				item['type'],
				item['demo'],
				1,
				datetime.datetime.now()
			)
		)

	pkid = cur.fetchone()[0]
	for author in item['author']:
		cur.execute('''INSERT INTO author (name, series, changeuser, changetime) VALUES (%s, %s, %s, %s);''', (author, pkid, 1, datetime.datetime.now()))

	for illust in item['illust']:
		cur.execute('''INSERT INTO illustrators (name, series, changeuser, changetime) VALUES (%s, %s, %s, %s);''', (illust, pkid, 1, datetime.datetime.now()))

	for tag in item['tags']:
		cur.execute('''INSERT INTO tags (tag, series, changeuser, changetime) VALUES (%s, %s, %s, %s);''', (tag, pkid, 1, datetime.datetime.now()))

	for genre in item['genre']:
		cur.execute('''INSERT INTO genres (genre, series, changeuser, changetime) VALUES (%s, %s, %s, %s);''', (genre, pkid, 1, datetime.datetime.now()))

	for altn in item['altnames']:
		cur.execute('''INSERT INTO alternatenames (series, name, cleanname, changeuser, changetime) VALUES (%s, %s, %s, %s, %s);''', (pkid, altn, nt.prepFilenameForMatching(altn), 1, datetime.datetime.now()))

	for filename, vol, chapter, description, relpath, filehash in item['covers']:


		cur.execute("""
			INSERT INTO
				covers (srcFname, series, volume, chapter, description, fsPath, hash, changeuser, changetime)
			VALUES
				(%s, %s, %s, %s, %s, %s, %s, %s, %s)
			;
			""", (filename, pkid, vol, chapter, description, relpath, filehash, 1, datetime.datetime.now()))


def install_news(cur):
	article = '''
	<p>This site is currently a bit of a work-in-progress.</p>
	<p>Yes, I know there is some (slightly) garbled data, and a lot of functionality is not
	quite complete yet. Please bear with it, much of the planned functionality has not
	been implemented yet.</p>
	'''
	title = 'Hey There!'

	# userid 2 is admin
	cur.execute("""INSERT INTO posts (title, body, timestamp, user_id) VALUES (%s, %s, %s, %s);""",
			(title, article, datetime.datetime.now(), 2)
		)

def insertData(data):
	print("Inserting!")
	cur = move_to_con.cursor()


	cur.execute("BEGIN;")

	base_setup(cur)

	for item in data:
		insertItem(cur, item)

	install_news(cur)

	print("Gross rowcounts:")
	for table in ["alembic_version",
					"alternatenames",
					"author",
					"covers",
					"genres",
					"illustrators",
					"posts",
					"releases",
					"series",
					"tags",
					"translators",
					"user",
					'alternatenameschanges',
					'authorchanges',
					'coverschanges',
					'genreschanges',
					'illustratorschanges',
					'releaseschanges',
					'serieschanges',
					'tagschanges',
					'translatorschanges',
					]:

		cur.execute("SELECT COUNT(*) FROM {table};".format(table=table))
		print("Rows in {table}: {count}".format(table=table, count=cur.fetchone()))


	cur.execute("COMMIT;")
	# cur.execute('''ROLLBACK;''')

def cleanItem(inStr):
	inStr = inStr.replace("\xa0[", "").replace("\xa0", " ").strip()
	while "  " in inStr:
		inStr = inStr.replace("  ", " ")
	return inStr

def mergeItem(inOne, inTwo):


	try:
		# Trick the merge logic into working by copying things across if needed.
		inTwo.setdefault('name',     inOne['name'])
		inTwo.setdefault('desc',     inOne['desc'])
		inTwo.setdefault('type',     inOne['type'])
		inTwo.setdefault('demo',     inOne['demo'])
		inTwo.setdefault('author',   inOne['author'])
		inTwo.setdefault('illust',   inOne['illust'])
		inTwo.setdefault('tags',     inOne['tags'])
		inTwo.setdefault('genre',    inOne['genre'])
		inTwo.setdefault('altnames', inOne['altnames'])
		inTwo.setdefault('covers',   inOne['covers'])
	except KeyError:
		print("Wat?", inOne)
		raise

	ret = {}
	for key in inOne.keys():

		if key == "illust" or key == "author":
			inNames = set(inOne[key]) | set(inTwo[key])

			bad = ["", "n/a", "N/A", "Key", "[", "]", "Add"]
			for badVal in bad:
				if badVal in inNames:
					# print("Removing", badVal)
					inNames.remove(badVal)
			inNames = set([name.replace("\xa0[", "").replace("\xa0", " ").strip() for name in inNames])
			tmpDict = {}
			for name in inNames:
				if name.lower() in tmpDict:
					print("Duplicate names?", name, tmpDict[name.lower()])
				tmpDict[name.lower()] = name

			inNames = set(tmpDict.values())

			ret[key] = inNames
			# print("After filtering:", title, key, inNames)

		elif inOne[key] == inTwo[key]:
			ret[key] = inOne[key]
		elif not inOne[key] and not inTwo[key]:
			ret[key] = inOne[key]
		elif not inOne[key]:
			ret[key] = inTwo[key]
		elif not inTwo[key]:
			ret[key] = inOne[key]
		elif isinstance(inOne[key], (list, set)):
			ret[key] = set(inOne[key]) | set(inTwo[key])
		else:
			ret[key] = inOne[key]
			print("Lol? %s '%s', '%s'" % (key, inOne[key], inTwo[key]))

	assert 'name'     in ret
	assert 'desc'     in ret
	assert 'type'     in ret
	assert 'demo'     in ret
	assert 'author'   in ret
	assert 'illust'   in ret
	assert 'tags'     in ret
	assert 'genre'    in ret
	assert 'altnames' in ret
	assert 'covers'   in ret


	return ret


def consolidate(inDat):

	out = {}

	for item in inDat:

		title = item['name'].lower().strip().replace("\xa0", " ")



		if not title in out:
			out[title] = mergeItem(item, {})
		else:
			out[title] = mergeItem(out[title], item)

			# print("Dup:", title)



	out = list(out.values())

	bad = [[loltmp['illust'], loltmp['name']] for loltmp in out if 'add' in str(loltmp['illust']).lower()]
	for badIllust, badName in bad:
		print(badIllust)

	return out


def base_setup(cur):

	cur.execute("INSERT INTO users (nickname, verified) VALUES (%s, %s) RETURNING id", ("system-migrator", 1))
	ret = cur.fetchall()
	print("System user ID = ", ret)
	# Install my user ID (since the pasword is hashed AND salted, it should be safe. If not, it's not like I can't recover anyways.)
	cur.execute("INSERT INTO users (nickname, email, password, verified, has_admin, has_mod) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
			("admin", "lemuix@gmail.com", "$2a$12$31.y.Bj9Pr705daMQFi/3.EjT0LkT80E7TJhlDqib/h5TUY0ukJU.", 1, True, True)
		)
	ret = cur.fetchall()
	print("Admin ID = ", ret)


	languages = [
		"English",
		"Japanese",
		"Chinese",
		"Korean",
	]
	for language in languages:
		cur.execute("INSERT INTO language (language, changetime) VALUES (%s, %s)", (language, datetime.datetime.now()))


def go():
	print(import_con)

	cur = import_con.cursor()
	cur.execute("""
		SELECT
			book_series.itemname,
			book_series_table_links.tablename
		FROM
			book_series
		INNER JOIN
			book_series_table_links
		ON
			book_series_table_links.dbid = book_series.itemtable;
			;
		""")

	items = cur.fetchall()

	data = []
	for name, srcTable in items:

		if 'book' in srcTable:
			item = processBookTbl(cur, name, srcTable)
		else:
			item = processMngSeries(cur, name, srcTable)

		if item:
			data.append(item)


	proc = consolidate(data)
	insertData(proc)


def reset_db():

	cur = move_to_con.cursor()
	print("Dropping all tables!")

	commands = [
		'''DROP TABLE "users" CASCADE;''',
		'''DELETE FROM "alembic_version";''',
		'''DROP TABLE "alternatenames" CASCADE;''',
		'''DROP TABLE "author" CASCADE;''',
		'''DROP TABLE "covers" CASCADE;''',
		'''DROP TABLE "followers" CASCADE;''',
		'''DROP TABLE "genres" CASCADE;''',
		'''DROP TABLE "illustrators" CASCADE;''',
		'''DROP TABLE "posts" CASCADE;''',
		'''DROP TABLE "releases" CASCADE;''',
		'''DROP TABLE "series" CASCADE;''',
		'''DROP TABLE "tags" CASCADE;''',
		'''DROP TABLE "translators" CASCADE;''',
		'''DROP TABLE "language" CASCADE;''',
		'''DROP TABLE "watches" CASCADE;''',
		'''DROP TABLE "alternatenameschanges" CASCADE;''',
		'''DROP TABLE "authorchanges" CASCADE;''',
		'''DROP TABLE "coverschanges" CASCADE;''',
		'''DROP TABLE "genreschanges" CASCADE;''',
		'''DROP TABLE "illustratorschanges" CASCADE;''',
		'''DROP TABLE "releaseschanges" CASCADE;''',
		'''DROP TABLE "serieschanges" CASCADE;''',
		'''DROP TABLE "tagschanges" CASCADE;''',
		'''DROP TABLE "translatorschanges" CASCADE;''',
		'''DROP TABLE "languagechanges" CASCADE;''',
	]
	for command in commands:
		try:
			cur.execute("BEGIN;")
			cur.execute(command)
			cur.execute('COMMIT;')
		except psycopg2.ProgrammingError as e:
			cur.execute("ROLLBACK")
			print("Error:", str(e).strip())

if __name__ == "__main__":
	if "destroy" in sys.argv:
		print("DESTROYING DATABASE! WARNING! WARNING!")
		reset_db()
	else:
		go()

'''
DROP TABLE "alembic_version" CASCADE;
DROP TABLE "alternatenames" CASCADE;
DROP TABLE "alternatenameschanges" CASCADE;
DROP TABLE "author" CASCADE;
DROP TABLE "authorchanges" CASCADE;
DROP TABLE "covers" CASCADE;
DROP TABLE "coverschanges" CASCADE;
DROP TABLE "genres" CASCADE;
DROP TABLE "genreschanges" CASCADE;
DROP TABLE "illustrators" CASCADE;
DROP TABLE "illustratorschanges" CASCADE;
DROP TABLE "language" CASCADE;
DROP TABLE "languagechanges" CASCADE;
DROP TABLE "post" CASCADE;
DROP TABLE "releases" CASCADE;
DROP TABLE "releaseschanges" CASCADE;
DROP TABLE "series" CASCADE;
DROP TABLE "serieschanges" CASCADE;
DROP TABLE "tags" CASCADE;
DROP TABLE "tagschanges" CASCADE;
DROP TABLE "translators" CASCADE;
DROP TABLE "translatorschanges" CASCADE;
DROP TABLE "users" CASCADE;

'''
