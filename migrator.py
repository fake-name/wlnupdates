
# DROP TABLE "alembic_version" CASCADE;
# DROP TABLE "alternate_names" CASCADE;
# DROP TABLE "author" CASCADE;
# DROP TABLE "covers" CASCADE;
# DROP TABLE "followers" CASCADE;
# DROP TABLE "genres" CASCADE;
# DROP TABLE "illustrators" CASCADE;
# DROP TABLE "post" CASCADE;
# DROP TABLE "releases" CASCADE;
# DROP TABLE "series" CASCADE;
# DROP TABLE "tags" CASCADE;
# DROP TABLE "translators" CASCADE;
# DROP TABLE "user" CASCADE;


# DROP SEQUENCE alternate_names_id_seq;
# DROP SEQUENCE genres_id_seq;
# DROP SEQUENCE series_id_seq;


import app.nameTools as nt
import settings
import psycopg2

move_to_con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
import_con = psycopg2.connect(host=settings.IMPORT_DATABASE_IP, dbname=settings.IMPORT_DATABASE_DB_NAME, user=settings.IMPORT_DATABASE_USER,password=settings.IMPORT_DATABASE_PASS)

def getItemEntry():
	item = {
		'name'   : [],
		'desc'   : [],
		'type'   : [],
		'demo'   : [],
		'tags'   : [],
		'genre'  : [],
		'author' : [],
		'illust' : [],
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
	item['desc']   = row['budescription']
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
	cur.execute('''INSERT INTO series (title, description, type, demographic) VALUES (%s, %s, %s, %s) RETURNING id;''',
			(
				item['name'],
				item['desc'],
				item['type'],
				item['demo']
			)
		)
	pkid = cur.fetchone()[0]
	for author in item['author']:
		cur.execute('''INSERT INTO author (author, series) VALUES (%s, %s);''', (author, pkid))

	for illust in item['illust']:
		cur.execute('''INSERT INTO illustrators (name, series) VALUES (%s, %s);''', (illust, pkid))

	for tag in item['tags']:
		cur.execute('''INSERT INTO tags (tag, series) VALUES (%s, %s);''', (tag, pkid))

	for genre in item['genre']:
		cur.execute('''INSERT INTO genres (genre, series) VALUES (%s, %s);''', (genre, pkid))

	for altn in item['altnames']:
		cur.execute('''INSERT INTO alternate_names (series, name, cleanname) VALUES (%s, %s, %s);''', (pkid, altn, nt.prepFilenameForMatching(altn)))

	for filename, vol, chapter, description, relpath, filehash in item['covers']:


		cur.execute("""
			INSERT INTO
				covers (srcFname, series, volume, chapter, description, fsPath, hash)
			VALUES
				(%s, %s, %s, %s, %s, %s, %s)
			;
			""", (filename, pkid, vol, chapter, description, relpath, filehash))


def insertData(data):
	print("Inserting!")
	cur = move_to_con.cursor()
	cur.execute("BEGIN;")
	for item in data:
		insertItem(cur, item)


	print("Gross rowcounts:")
	for table in ["alembic_version", "alternate_names", "author", "covers", "followers", "genres", "illustrators", "post", "releases", "series", "tags", "translators", "user"]:

		cur.execute("SELECT COUNT(*) FROM {table};".format(table=table))
		print("Rows in {table}: {count}".format(table=table, count=cur.fetchone()))


	# cur.execute("COMMIT;")
	cur.execute('''ROLLBACK;''')

def consolidate(inDat):

	# item['name']   =
	# item['desc']   =
	# item['type']   =
	# item['demo']   =
	# item['tags']   =
	# item['genre']  =
	# item['author'] =
	# item['illust'] =
	# item['altnames']
	# item['covers'] =

	out = {}
	titles = []
	for item in inDat:
		title = item['name'].lower()

		if not title in out:
			out[title] = item
		else:
			for key in [key for key in item.keys() if item[key]]:
				if not out[title][key]:
					out[title][key] = item[key]
				elif key == 'covers':
					out[title][key] += item[key]
				elif key == 'altnames':
					out[title][key] = list(set(out[title][key] + item[key]))
				elif str(out[title][key]).lower() == str(item[key]).lower():
					# print(key, "Match", str(out[title][key]).lower(), str(item[key]).lower())
					pass
				elif key == "illust" or key == "author":

					if out[title][key] == [""] or out[title][key] == ["n/a"]:
						out[title][key] = []


					out[title][key] = [lval.replace("\xa0", " ").strip() for lval in out[title][key]]
					inData = [lval.lower().replace("\xa0", " ").strip() for lval in item[key]]
					outData = [lval.lower() for lval in out[title][key]]

					outData = set([frozenset(val.split(" ")) for val in outData])
					inData = set([frozenset(val.split(" ")) for val in inData])

					extra = [inval for inval in inData if inval not in outData]
					if extra:
						print(extra)
						print(inData)
						print(outData)
						print()
					# if outData == inData:
					# 	pass
					# else:
					# 	print(outData, inData)
					# 	print("'%s', '%s'" % (outData, inData))
					# # print("wat?")
				else:
					print(out[title][key], item[key])
					print('wat', key)
			# print("Dup:", title)


	return list(out.values())

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


if __name__ == "__main__":
	go()
