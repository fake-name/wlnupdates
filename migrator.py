
# DROP TABLE author CASCADE;
# DROP TABLE followers CASCADE;
# DROP TABLE genres CASCADE;
# DROP TABLE illustrators CASCADE;
# DROP TABLE migrate_version CASCADE;
# DROP TABLE post CASCADE;
# DROP TABLE releases CASCADE;
# DROP TABLE series CASCADE;
# DROP TABLE tags CASCADE;
# DROP TABLE translators CASCADE;
# DROP TABLE "user" CASCADE;



import settings
import psycopg2

loc_con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
imp_con = psycopg2.connect(host=settings.IMPORT_DATABASE_IP, dbname=settings.IMPORT_DATABASE_DB_NAME, user=settings.IMPORT_DATABASE_USER,password=settings.IMPORT_DATABASE_PASS)

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
	item['author'] = row['buauthor']
	item['illust'] = row['buartist']
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
	item['author'] = row['author']
	item['illust'] = row['illust']
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
	print(item)
	cur.execute('''INSERT INTO series (title, description, type, demographic) VALUES (%s, %s, %s, %s) RETURNING id;''',
			(
				item['name'],
				item['desc'],
				item['type'],
				item['demo']
			)
		)
	pkid = cur.fetchone()[0]

	cur.execute('''INSERT INTO author (author, series) VALUES (%s, %s);''', (item['author'], pkid))
	cur.execute('''INSERT INTO illustrators (name, series) VALUES (%s, %s);''', (item['illust'], pkid))
	for tag in item['tags']:
		cur.execute('''INSERT INTO tags (tag, series) VALUES (%s, %s);''', (tag, pkid))

	for genre in item['genre']:
		cur.execute('''INSERT INTO genres (genre, series) VALUES (%s, %s);''', (genre, pkid))

def insertData(data):
	cur = loc_con.cursor()
	inserted = []
	for item in data:
		if not item['name'] in inserted:
			insertItem(cur, item)
			inserted.append(item['name'])

	cur.execute('''COMMIT;''')

def go():
	print(imp_con)

	cur = imp_con.cursor()
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
	insertData(data)


if __name__ == "__main__":
	go()
