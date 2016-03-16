#!/usr/bin/env python3
from FeedFeeder.AmqpInterface import RabbitQueueHandler
import settings
import json
import datetime
from app import db
from app.models import Feeds, FeedAuthors, FeedTags
from app.models import Translators, Releases, Series, AlternateNames, AlternateTranslatorNames
import traceback
import app.nameTools as nt
import time
import sqlalchemy.exc
import bleach
import app.series_tools
import sqlalchemy.exc
import Levenshtein
# user = Users(
# 	nickname  = form.username.data,
# 	password  = form.password.data,
# 	email     = form.email.data,
# 	verified  = 0
# )
# print("User:", user)
# db.session.add(user)
# db.session.commit()

# class Feeds(db.Model):

# 	id          = db.Column(db.Integer, primary_key=True)
# 	title       = db.Column(db.Text, nullable=False)
# 	contents    = db.Column(db.Text, nullable=False)
# 	guid        = db.Column(db.Text, unique=True)
# 	linkurl     = db.Column(db.Text, nullable=False)
# 	published   = db.Column(db.DateTime, index=True, nullable=False)
# 	updated     = db.Column(db.DateTime, index=True)
# 	region      = db.Column(region_enum, default='unknown')

# class FeedAuthors(db.Model):
# 	id          = db.Column(db.Integer, primary_key=True)
# 	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
# 	name        = db.Column(CIText(), index=True, nullable=False)

# class FeedTags(db.Model):
# 	id          = db.Column(db.Integer, primary_key=True)
# 	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
# 	tag         = db.Column(CIText(), index=True, nullable=False)



# Error!
# Error!
# Traceback (most recent call last):
#   File "/media/Storage/Scripts/wlnupdates/FeedFeeder/FeedFeeder.py", line 444, in process
#     beta_enabled = getattr(settings, "ENABLE_BETA", False)
#   File "/media/Storage/Scripts/wlnupdates/FeedFeeder/FeedFeeder.py", line 406, in dispatchItem
#     tmp = item['author']
#   File "/media/Storage/Scripts/wlnupdates/FeedFeeder/FeedFeeder.py", line 294, in insert_parsed_release
#     # return have.series_row
#   File "/media/Storage/Scripts/wlnupdates/FeedFeeder/FeedFeeder.py", line 172, in get_create_series
#     # print("AuthorName match!")
# AttributeError: 'list' object has no attribute 'lower'
# Main.Feeds.RPC.Thread-1 - INFO - Received data size: 563 bytes.
# Beta release!


# Hard coded RSS user ID. Probably a bad idea.
RSS_USER_ID = 3

def insert_raw_item(item):
	'''
	insert item `item` into the feed database.

	fields in `item`:
		"title"
		"contents"
		"guid"
		"linkUrl"
		"feedtype"
		"published"
		"updated"

		"authors"
		->	"href"
		->	"name"
		"tags"

	'''

	# print(item)

	if not 'srcname' in item:
		print("No srcname? Old item?")
		return


	entry = {}
	entry['title']     = item.pop('title')
	entry['contents']  = item.pop('contents', 'N/A')

	if not isinstance(entry['contents'], str):
		if isinstance(entry['contents'], list):
			entry['contents'] = entry['contents'].pop()
		if 'value' in entry['contents']:
			entry['contents'] = entry['contents']['value']
		else:
			print(entry['contents'])
			entry['contents'] = str(entry['contents'])

	entry['guid']      = item.pop('guid')
	entry['linkurl']   = item.pop('linkUrl')
	entry['region']    = item.pop('feedtype')
	entry['srcname']   = item.pop('srcname')
	entry['published'] = datetime.datetime.fromtimestamp(item.pop('published'))
	if 'updated' in item:
		entry['updated']   = datetime.datetime.fromtimestamp(item.pop('updated'))

	itemrow = Feeds.query.filter(Feeds.guid == entry['guid']).scalar()
	if not itemrow:
		print("New feed item: ", entry['guid'])
		itemrow = Feeds(**entry)

		db.session.add(itemrow)
		db.session.flush()


	for tag in item.pop('tags'):
		if not FeedTags.query                           \
			.filter(FeedTags.article_id==itemrow.id)    \
			.filter(FeedTags.tag == tag.strip()).scalar():

			newtag = FeedTags(article_id=itemrow.id, tag=tag.strip())
			db.session.add(newtag)
			db.session.flush()

	for author in item.pop('authors'):
		if not 'name' in author:
			continue

		if not FeedAuthors.query                        \
			.filter(FeedAuthors.article_id==itemrow.id) \
			.filter(FeedAuthors.name == author['name'].strip()).scalar():

			newtag = FeedAuthors(article_id=itemrow.id, name=author['name'].strip())
			db.session.add(newtag)
			db.session.flush()

	db.session.commit()


def pick_best_match(group_rows, targetname):

	gmap = {}

	for group_row in group_rows:
		name = group_row.name
		if not name in gmap:
			gmap[name] = []
		gmap[name].append(group_row)

	best_distance = 999
	best = None
	for item in group_rows:
		dist = Levenshtein.distance(item.name, targetname)
		if dist == 0:
			return item
		if dist < best_distance:
			best = item
			best_distance = dist

	assert best
	return best

def get_create_group(groupname):
	groupname = groupname[:500]
	cleanName = nt.prepFilenameForMatching(groupname)
	have = AlternateTranslatorNames.query.filter(AlternateTranslatorNames.cleanname==cleanName).all()
	if not have:
		print("Need to create new translator entry for ", groupname)
		new = Translators(
				name = groupname,
				changeuser = RSS_USER_ID,
				changetime = datetime.datetime.now()
				)
		db.session.add(new)
		db.session.commit()
		newalt = AlternateTranslatorNames(
			group      = new.id,
			name       = new.name,
			cleanname  = nt.prepFilenameForMatching(new.name),
			changetime = datetime.datetime.now(),
			changeuser = RSS_USER_ID,
			)
		db.session.add(newalt)
		db.session.commit()
		return new
	else:

		if len(have) == 1:
			group = have[0]
		else:
			group = pick_best_match(have, groupname)


		row = Translators.query.filter(Translators.id == group.group).one()
		return row

def get_create_series(seriesname, tl_type, author_name=False):
	# print("get_create_series(): '%s', '%s', '%s'" % (seriesname, tl_type, author_name))
	while 1:
		try:
			have  = AlternateNames                             \
					.query                                     \
					.filter(AlternateNames.name == seriesname) \
					.order_by(AlternateNames.id)               \
					.all()

			# for item in have:
			# 	print((item.series_row.id, item.series_row.title, [tmp.name.lower() for tmp in item.series_row.author]))
			# print("Want:", author_name)

			# There's 4 options here:
			#  - Update and have item has author ->
			#         match, fail if match fails.
			#  - Update has author, have does not ->
			#         only allow matches after haves with authors exhausted.
			#  - have has author, update does not ->
			#         Glob onto series anyways.
			#  - Update and have do not have author ->
			#         do best match.

			# From the perspective of our approach, if we have a name, we try for that, then
			# look for empty items, finally return none if nothing present.
			# if we don't have a name, we look for

			# Try to match any alt-names we have.

			valid_haves = [tmp for tmp in have if tmp.series_row.tl_type == tl_type]

			# Try for author match first:
			if author_name:
				for item in [tmp for tmp in valid_haves if tmp.series_row.author]:
					if isinstance(author_name, list):
						if any([auth_tmp.lower() in [tmp.name.lower() for tmp in item.series_row.author] for auth_tmp in author_name]):
							# print("AuthorName match!")
							return item.series_row
					else:
						if author_name.lower() in [tmp.name.lower() for tmp in item.series_row.author]:
							return item.series_row

				for item in [tmp for tmp in valid_haves if not tmp.series_row.author]:
					return item.series_row
			else:
				# No author specified globs onto first possible match.
				for item in valid_haves:
					return item.series_row



			# print("No match found while filtering by author-name!")


			haveS  = Series                              \
					.query                              \
					.filter(Series.title == seriesname) \
					.limit(1)                           \
					.scalar()

			if haveS and author_name:
				if isinstance(author_name, str):
					sName = "{} ({})".format(seriesname, author_name)
				else:
					sName = "{} ({})".format(seriesname, ", ".join(author_name))
			elif haveS:
				if haveS.tl_type != tl_type:
					if tl_type == "oel":
						st = "OEL"
					else:
						st = tl_type.title()
					sName = "{} ({})".format(seriesname, st)
				else:
					# print("Wat? Item that isn't in the altname table but still exists?")
					return haveS
			else:
				sName = seriesname


			print("Need to create new series entry for ", seriesname)
			new = Series(
					title=sName,
					changeuser = RSS_USER_ID,  # Hard coded RSS user ID. Probably a bad idea.
					changetime = datetime.datetime.now(),
					tl_type    = tl_type,


				)
			db.session.add(new)
			db.session.flush()

			if author_name:
				if isinstance(author_name, str):
					author_name = [author_name, ]
				app.series_tools.setAuthorIllust(new, author=author_name)

			altn1 = AlternateNames(
					name       = seriesname,
					cleanname  = nt.prepFilenameForMatching(seriesname),
					series     = new.id,
					changetime = datetime.datetime.now(),
					changeuser = RSS_USER_ID
				)
			db.session.add(altn1)

			if sName != seriesname:
				altn2 = AlternateNames(
						name       = sName,
						cleanname  = nt.prepFilenameForMatching(seriesname),
						series     = new.id,
						changetime = datetime.datetime.now(),
						changeuser = RSS_USER_ID
					)
				db.session.add(altn2)
			db.session.commit()


			return new
		except sqlalchemy.exc.IntegrityError:
			print("Concurrency issue?")
			print("'%s', '%s', '%s'" % (seriesname, tl_type, author_name))
			db.session.rollback()
			raise
		except Exception:
			print("Error!")
			raise


	# return have.series_row

def get_series_from_any(title_list, tl_type, author_name=False):
	# print("get_create_series(): '%s', '%s', '%s'" % (seriesname, tl_type, author_name))
	for seriesname in title_list:
		try:
			have  = AlternateNames                             \
					.query                                     \
					.filter(AlternateNames.name == seriesname) \
					.order_by(AlternateNames.id)               \
					.all()

			# for item in have:
			# 	print((item.series_row.id, item.series_row.title, [tmp.name.lower() for tmp in item.series_row.author]))
			# print("Want:", author_name)

			# Try to match any alt-names we have.
			if have:
				for item in [tmp for tmp in have if tmp.series_row.tl_type == tl_type]:
					if author_name:
						if author_name.lower() in [tmp.name.lower() for tmp in item.series_row.author]:
							# print("AuthorName match!")
							return item.series_row
					else:
						return item.series_row

				for item in [tmp for tmp in have if tmp.series_row.tl_type == tl_type]:
					if not item.series_row.author:
						return item.series_row

			# print("No match found while filtering by author-name!")



		except sqlalchemy.exc.IntegrityError:
			print("Concurrency issue?")
			print("'%s', '%s', '%s'" % (seriesname, tl_type, author_name))
			db.session.rollback()
			raise
		except Exception:
			print("Error!")
			raise

	return None

	# return have.series_row

def check_insert_release(item, group, series):
	have = Releases.query                            \
		.filter(Releases.series  == series.id)       \
		.filter(Releases.tlgroup == group.id)        \
		.filter(Releases.volume  == item['vol'])     \
		.filter(Releases.chapter == item['chp'])     \
		.filter(Releases.postfix == item['postfix']).all()
	if have:
		have = have.pop(0)
		# print("have?", series.title, have.volume, have.chapter, have.postfix)
		return
	print("Adding new release for series: ", series.title, " at date:", datetime.datetime.fromtimestamp(item['published']))
	release = Releases(
			series     = series.id,
			published  = datetime.datetime.fromtimestamp(item['published']),
			volume     = item['vol'],
			chapter    = item['chp'],
			include    = True,
			postfix    = item['postfix'],
			tlgroup    = group.id,
			changetime = datetime.datetime.now(),
			changeuser = RSS_USER_ID,
			srcurl     = item['itemurl'],
		)


	db.session.add(release)
	db.session.flush()
	db.session.commit()

def insert_parsed_release(item):
	assert 'tl_type' in item
	assert 'srcname' in item
	assert 'series'  in item


	if item["tl_type"] not in ['oel', 'translated']:
		raise ValueError("Invalid TL Type '%s'! Wat?" % item["tl_type"])

	group = get_create_group(item['srcname'])

	if 'match_author' in item and item['match_author']:
		series = get_create_series(item['series'], item["tl_type"], item['author'])
	else:
		series = get_create_series(item['series'], item["tl_type"])


	check_insert_release(item, group, series)

def update_series_info(item):
	# print("update_series_info", item)
	assert 'title'    in item
	assert 'author'   in item
	assert 'tags'     in item
	assert 'desc'     in item
	assert 'tl_type'  in item


	print("Series info update message for '%s'!" % item['title'])

	if not 'update_only' in item:
		item['update_only'] = False
	if not 'alt_titles' in item:
		item['alt_titles'] = []

	item['alt_titles'].append(item['title'])
	if item['update_only']:
		series = get_series_from_any(item['alt_titles'], item["tl_type"], item['author'])
	else:
		series = get_create_series(item['title'], item["tl_type"], item['author'])

	# Break if the tl type has changed, something is probably mismatched
	if series.tl_type != item['tl_type']:
		print("WARNING! TlType mismatch? Wat?")

		print("Series:", series)
		print("###################################")
		print(series.title)
		print("-----------------------------------")
		print(item['title'])
		print("###################################")
		print(series.author)
		print("-----------------------------------")
		print(item['author'])
		print("###################################")
		print(series.description)
		print("-----------------------------------")
		print(item['desc'])
		print("###################################")
		print(series.tl_type)
		print("-----------------------------------")
		print(item['tl_type'])
		print("###################################")
		print(series.tags)
		print("-----------------------------------")
		print(item['tags'])

		return

	if 'desc' in item and item['desc'] and not series.description:
		series.description = bleach.clean(item['desc'], strip=True, tags = ['p', 'em', 'strong', 'b', 'i', 'a'])

	if 'homepage' in item and item['homepage'] and not series.website:
		series.website = bleach.clean(item['homepage'])

	if 'author' in item and item['author']:
		tmp = item['author']
		if isinstance(tmp, str):
			tmp = [tmp, ]
		app.series_tools.setAuthorIllust(series, author=tmp, deleteother=False)

	if 'illust' in item and item['illust']:
		tmp = item['illust']
		if isinstance(tmp, str):
			tmp = [tmp, ]
		app.series_tools.setAuthorIllust(series, illust=tmp, deleteother=False)

	if 'tags' in item and item['tags']:
		app.series_tools.updateTags(series, item['tags'], deleteother=False, allow_new=False)

	if 'alt_titles' in item and item['alt_titles']:
		app.series_tools.updateAltNames(series, item['alt_titles'], deleteother=False)

	if 'pubnames' in item and item['pubnames']:
		app.series_tools.updatePublishers(series, item['pubnames'], deleteother=False)

	if 'pubdate' in item and item['pubdate']:
		if not series.pub_date:
			series.pub_date = datetime.datetime.utcfromtimestamp(item['pubdate'])

	if 'sourcesite' in item and item['sourcesite']:
		pass

	series.changeuser = RSS_USER_ID

	db.session.flush()
	db.session.commit()

def dispatchItem(item):
	item = json.loads(item)
	assert 'type' in item
	assert 'data' in item


	beta_enabled = getattr(settings, "ENABLE_BETA", False)
	if "beta" in item:
		if item['beta'] == True and not beta_enabled:
			return
		elif item['beta'] == True and beta_enabled:
			print("Beta release!")



	try:
		if item['type'] == 'raw-feed':
			# print("Dispatching item of type: ", item['type'])
			insert_raw_item(item['data'])
		elif item['type'] == 'parsed-release':
			# print("Dispatching item of type: ", item['type'])
			insert_parsed_release(item['data'])
		elif item['type'] == 'series-metadata':
			# print("Dispatching item of type: ", item['type'])
			update_series_info(item['data'])
		else:
			print(item)
			raise ValueError("No known packet structure in item!")
	except sqlalchemy.exc.IntegrityError:

		print("ERROR INSERTING ROW!")
		traceback.print_exc()
		db.session.rollback()
		return

class FeedFeeder(object):
	die = False

	def __init__(self):

		amqp_settings = {}
		amqp_settings["CLIENT_NAME"]        = settings.CLIENT_NAME
		amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
		amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
		amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
		amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
		amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST

		self.feeder = RabbitQueueHandler(settings=amqp_settings)

		print("Feed Feeder Initializing!")

	def process(self):
		while 1:
			data = self.feeder.get_item()
			if not data:
				break
			else:
				try:
					dispatchItem(data)
				except Exception:
					with open("error - %s.txt" % time.time(), 'w') as fp:
						fp.write(traceback.format_exc())
					print("Error!")
					traceback.print_exc()

	def close(self):
		self.feeder.close()

	def __del__(self):
		print("FeedFeeder being deleted")


if __name__ == "__main__":
	# ret = get_create_series("World Seed", "oel", author_name='karami92')
	assert None != get_series_from_any(["World Seed"], "oel", author_name='karami92')
	assert None != get_series_from_any(["Sendai Yuusha wa Inkyou Shitai", 'Sendai Yuusha wa Inkyoshitai', 'The Previous Hero wants to Retire', '先代勇者は隠居したい'], "translated", author_name='Iida K')
	assert None == get_series_from_any(["Sendai Yuusha wa Inkyou Shitai", 'Sendai Yuusha wa Inkyoshitai', 'The Previous Hero wants to Retire', '先代勇者は隠居したい'], "translated", author_name='BLURKKKK')
	assert None != get_series_from_any(["Sendai Yuusha wa Inkyou Shitai", 'Sendai Yuusha wa Inkyoshitai', 'The Previous Hero wants to Retire', '先代勇者は隠居したい'], "translated", author_name=None)
	assert None != get_series_from_any(['Kenkyo, Kenjitsu o Motto ni Ikite Orimasu', '謙虚、堅実をモットーに生きております！'], "translated", author_name=None)
	assert None != get_series_from_any(['Kenkyo, Kenjitsu o Motto ni Ikite Orimasu', '謙虚、堅実をモットーに生きております！'], "translated", author_name='Hiyoko no kēki')
	assert None != get_series_from_any(['Mythical Tyrant', '神魔灞体'], "translated", author_name='Yun Ting Fei')
	print(get_series_from_any(['Peerless Martial God'], "translated", author_name=["Jing Wu Hen", "净无痕"]))
	# assert None == get_series_from_any(['Mythical Tyrant', '神魔灞体'], "translated", author_name='BLHOOGLE!')



	# assert None != get_series_from_any(['Night Ranger', 'An Ye You Xia', '暗夜游侠'], "translated", author_name=None)
	# assert None != get_series_from_any(['Night Ranger', 'An Ye You Xia', '暗夜游侠'], "translated", author_name='Dark Blue Coconut Milk')
	# assert None != get_series_from_any(['Night Ranger', 'An Ye You Xia', '暗夜游侠'], "translated", author_name='深蓝椰子汁')
	pass
