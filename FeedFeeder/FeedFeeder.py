#!/usr/bin/env python3
#
import json
import datetime
import traceback
import pprint
import time

import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import desc
from sqlalchemy import or_
import bleach
import Levenshtein
import app.utilities
from app import db
from app.models import Feeds
from app.models import FeedAuthors
from app.models import FeedTags
from app.models import Translators
from app.models import Releases
from app.models import Series
from app.models import SeriesChanges
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
import app.nameTools as nt
import app.series_tools as series_tools

import util.text_tools as text_tools

from FeedFeeder.AmqpInterface import RabbitQueueHandler
import settings

# Hard coded RSS user ID. Probably a bad idea.
RSS_USER_ID    = 3
NU_SRC_USER_ID = 4

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

	item = text_tools.fix_dict(item, recase=False)

	itemrows = Feeds.query.filter(Feeds.guid == entry['guid']).all()
	if not itemrows:
		print("New feed item: ", entry['guid'])
		itemrow = Feeds(**entry)

		db.session.add(itemrow)
		db.session.flush()
	else:
		itemrow = itemrows[0]


	for tag in item.pop('tags'):

		# This is hitting duplicate tags somehow.
		if tag and not FeedTags.query                      \
			.filter(FeedTags.article_id==itemrow.id)       \
			.filter(FeedTags.tag == tag.strip()).count():

			newtag = FeedTags(article_id=itemrow.id, tag=tag.strip())
			db.session.add(newtag)
			db.session.flush()

	for author in item.pop('authors'):
		if not 'name' in author:
			continue

		if not FeedAuthors.query                        \
			.filter(FeedAuthors.article_id==itemrow.id) \
			.filter(FeedAuthors.name == author['name'].strip()).count():

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
		if dist < best_distance:
			if item.group_row:
				best = item
				best_distance = dist

	print("Flushing")
	db.session.flush()
	assert best, "Failed to find best match for name: %s, candidates '%s'" % (targetname, [(tmp.name, tmp.id) for tmp in group_rows])
	assert best.group_row, "Group_Row is null - Failed to find best match for name: %s, candidates '%s' row = %s:%s" % \
			(targetname, [(tmp.name, tmp.id) for tmp in group_rows], best.id, best.group_row)
	return best

def get_create_group(groupname, changeuser):
	groupname = groupname[:500]
	cleanName = nt.prepFilenameForMatching(groupname)

	have = False
	fails = 0

	while True:
		try:

			# If the group name collapses down to nothing when cleaned, search for it without cleaning.
			if len(cleanName):
				have = AlternateTranslatorNames.query.filter(AlternateTranslatorNames.cleanname==cleanName).all()

			if not have:
				have = AlternateTranslatorNames.query.filter(AlternateTranslatorNames.name==groupname).all()

			if not have:
				last_try = Translators.query.filter(Translators.name == groupname).scalar()
				if last_try:
					# How would this be reached? Something adding groups without adding the appropriate AlternateNames?
					return last_try

				print("Need to create new translator entry for ", groupname)
				new = Translators(
						name = groupname,
						changeuser = changeuser,
						changetime = datetime.datetime.now()
						)
				db.session.add(new)
				db.session.commit()
				newalt = AlternateTranslatorNames(
					group      = new.id,
					name       = new.name,
					cleanname  = nt.prepFilenameForMatching(new.name),
					changetime = datetime.datetime.now(),
					changeuser = changeuser,
					)
				db.session.add(newalt)
				db.session.commit()
				return new
			else:
				if len(have) == 1:
					group = have[0]
					assert group.group_row is not None, ("Wat? Row: '%s', '%s', '%s'" % (group.id, group.name, group.group_row))
				elif len(have) > 1:
					group = pick_best_match(have, groupname)
				else:
					raise ValueError("Wat for groupname: '%s'" % groupname)

				row = group.group_row
				return row


		except sqlalchemy.exc.IntegrityError:
			print("Concurrency issue?")
			print("'%s', '%s'a" % (groupname, changeuser))
			fails += 1
			db.session.rollback()

			if fails > 5:
				raise


def create_series(seriesname, tl_type, changeuser, author_name, alt_names = None):

	if alt_names is None:
		alt_names = []

	alt_names.append(seriesname)

	print("Need to create new series entry for ", seriesname)
	new = Series(
			title=seriesname,
			changeuser = changeuser,  # Hard coded RSS user ID. Probably a bad idea.
			changetime = datetime.datetime.now(),
			tl_type    = tl_type,


		)
	db.session.add(new)
	db.session.flush()

	if author_name:
		if isinstance(author_name, str):
			author_name = [author_name, ]
		series_tools.setAuthorIllust(new, author=author_name)

	for altname in alt_names:
		have  = AlternateNames                          \
				.query                                  \
				.filter(AlternateNames.name == altname) \
				.order_by(AlternateNames.id)            \
				.scalar()

		if not have:
			altn_row = AlternateNames(
					name       = altname,
					cleanname  = nt.prepFilenameForMatching(altname),
					series     = new.id,
					changetime = datetime.datetime.now(),
					changeuser = changeuser
				)
			db.session.add(altn_row)

	return new

def get_create_series(input_series_name, tl_type, changeuser, author_name_list=False, should_create_series_if_missing=True):
	# print("get_create_series(): '%s', '%s', '%s'" % (input_series_name, tl_type, author_name))

	if isinstance(author_name_list, str):
		author_name_list = [author_name_list]

	tries = 0
	while 1:
		try:
			have  = AlternateNames                             \
					.query                                     \
					.filter(AlternateNames.name == input_series_name) \
					.order_by(AlternateNames.id)               \
					.all()

			# print("get_create_series for title: '%s'" % input_series_name)
			# print("Altnames matches: ", have)
			# for item in have:
			# 	print((item.series_row.id, item.series_row.title, [tmp.name.lower() for tmp in item.series_row.author]))
			# print("Want:", author_name_list)

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
			if not all([tmp.series_row for tmp in have]):
				db.session.commit()


			valid_haves = [tmp for tmp in have if tmp.series_row and tmp.series_row.tl_type == tl_type]

			# Try for author match first:
			if author_name_list:
				for item in [tmp for tmp in valid_haves if tmp.series_row.author]:
					if isinstance(author_name_list, list):
						if any([auth_tmp.lower() in [tmp.name.lower() for tmp in item.series_row.author] for auth_tmp in author_name_list]):
							return item.series_row


				for item in [tmp for tmp in valid_haves if not tmp.series_row.author]:
					return item.series_row
			else:
				# No author specified globs onto first possible match.
				for item in valid_haves:
					return item.series_row


			have_series_row  = Series                              \
					.query                              \
					.filter(Series.title == input_series_name) \
					.limit(1)                           \
					.scalar()

			if have_series_row and author_name_list:
				full_series_name = "{} ({})".format(input_series_name, ", ".join(author_name_list))
			elif have_series_row:
				if have_series_row.tl_type != tl_type:
					if tl_type == "oel":
						st = "OEL"
					else:
						st = tl_type.title()
					full_series_name = "{} ({})".format(input_series_name, st)
				else:
					# print("Wat? Item that isn't in the altname table but still exists?")
					return have_series_row
			else:
				full_series_name = input_series_name


			# We've built a new series title by appending the author/tl_type
			# Now we need to check if that exists too.
			if full_series_name != input_series_name:
				have_series_row  = Series                              \
						.query                              \
						.filter(Series.title == input_series_name) \
						.limit(1)                           \
						.scalar()

				return have_series_row

			if not should_create_series_if_missing:
				return None

			new = create_series(seriesname=full_series_name, tl_type=tl_type, changeuser=changeuser, author_name=author_name_list, alt_names=[input_series_name])

			db.session.commit()

			return new
		except sqlalchemy.exc.IntegrityError:
			print("Concurrency issue?")
			print("'%s', '%s', '%s'" % (input_series_name, tl_type, author_name_list))
			db.session.rollback()

			tries += 1

			if tries > 3:
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

def check_insert_release(item, group, series, update_id, loose_match=False, prefix_match=False):
	cleankeys = ['itemurl', 'postfix']
	for cleans in cleankeys:
		if item[cleans] and isinstance(item[cleans], str):
			item[cleans] = item[cleans].strip()

	for key in ['vol', 'chp', 'frag']:
		if item[key] is not None:
			item[key]  = float(item[key])

	relQ = have = Releases.query
	relQ = relQ.filter(Releases.series   == series.id)
	relQ = relQ.filter(Releases.tlgroup  == group.id)

	# Allow http/https ambiguities. Sigh.
	if item['itemurl'].startswith("http://"):
		mainurl = item['itemurl']
		alturl  = "https://" + item['itemurl'][7:]
	elif item['itemurl'].startswith("https://"):
		mainurl = item['itemurl']
		alturl  = "http://" + item['itemurl'][8:]
	else:
		raise RuntimeError("Invalid url for item! Url '%s', item: '%s'" % (item['itemurl'], item))

	# Patch the URL (principally the bunch of ways you can access RRL chapters.)
	mainurl = text_tools.clean_fix_url(mainurl)
	alturl  = text_tools.clean_fix_url(alturl)

	# "Loose matching" means just check against the URL.
	if prefix_match:
		relQ = relQ.filter(or_(Releases.srcurl.startswith(mainurl), Releases.srcurl.startswith(alturl)))
	elif loose_match:
		relQ = relQ.filter(or_(Releases.srcurl == mainurl, Releases.srcurl == alturl))
	else:
		relQ = relQ.filter(or_(Releases.srcurl == mainurl, Releases.srcurl == alturl))
		relQ = relQ.filter(Releases.volume   == item['vol'])
		relQ = relQ.filter(Releases.chapter  == item['chp'])
		relQ = relQ.filter(Releases.fragment == item['frag'])
		relQ = relQ.filter(Releases.postfix  == item['postfix'])

	have = relQ.all()

	if have:
		have = have.pop(0)
		if loose_match:
			print("Loosely matched release:", series.title, have.volume, have.chapter, have.postfix)
		return

	# Clamp timestamp
	published_on = datetime.datetime.fromtimestamp(min(max(0, item['published']), time.time()))

	print("Adding new release for series: ", series.title, " at date:", published_on)
	release = Releases(
			series     = series.id,
			published  = published_on,
			volume     = item['vol'],
			chapter    = item['chp'],
			fragment   = item['frag'],
			include    = True,
			postfix    = item['postfix'],
			tlgroup    = group.id,
			changetime = datetime.datetime.now(),
			changeuser = update_id,
			srcurl     = item['itemurl'],
		)

	db.session.add(release)
	db.session.flush()

	app.utilities.update_latest_row(series)

	db.session.commit()

def check_delete_release(item, group, series, update_id, loose_match=False, prefix_match=False):
	cleankeys = ['itemurl', 'postfix']
	for cleans in cleankeys:
		if item[cleans] and isinstance(item[cleans], str):
			item[cleans] = item[cleans].strip()

	for key in ['vol', 'chp', 'frag']:
		if item[key] is not None:
			item[key]  = float(item[key])

	relQ = have = Releases.query
	relQ = relQ.filter(Releases.series   == series.id)
	relQ = relQ.filter(Releases.tlgroup  == group.id)

	# "Loose matching" means just check against the URL.
	if prefix_match:
		relQ = relQ.filter(Releases.srcurl.startswith(item['itemurl']))
	elif loose_match:
		relQ = relQ.filter(Releases.srcurl   == item['itemurl'])
	else:
		relQ = relQ.filter(Releases.srcurl   == item['itemurl'])
		relQ = relQ.filter(Releases.volume   == item['vol'])
		relQ = relQ.filter(Releases.chapter  == item['chp'])
		relQ = relQ.filter(Releases.fragment == item['frag'])
		relQ = relQ.filter(Releases.postfix  == item['postfix'])

	have = relQ.all()

	have = list(have)
	print("Deleting %s releases!" % len(have))

	if not have:
		return

	for bad in have:
		db.session.delete(bad)


	app.utilities.update_latest_row(series)
	db.session.commit()


def insert_parsed_release(item):
	assert 'tl_type' in item
	assert 'srcname' in item
	assert 'series'  in item

	if "nu_release" in item:
		update_id = NU_SRC_USER_ID
	else:
		update_id = RSS_USER_ID


	item = text_tools.fix_dict(item, recase=False)

	if item["tl_type"] not in ['oel', 'translated']:
		raise ValueError("Invalid TL Type '%s'! Wat?" % item["tl_type"])

	group = get_create_group(item['srcname'], update_id)
	assert group is not None

	kwargs = {
		"input_series_name" : item['series'],
		"tl_type"           : item["tl_type"],
		"changeuser"        : update_id,
	}


	if 'match_author' in item and item['match_author']:
		kwargs['author_name_list'] = item['author']
	series = get_create_series(**kwargs)


	prefix_match = item.get('prefix_match', False)
	loose_match  = item.get('loose_match', False)
	check_insert_release(item, group, series, update_id, loose_match=loose_match, prefix_match=prefix_match)

def delete_parsed_release(item):
	assert 'tl_type' in item
	assert 'srcname' in item
	assert 'series'  in item

	if "nu_release" in item:
		update_id = NU_SRC_USER_ID
	else:
		update_id = RSS_USER_ID


	item = text_tools.fix_dict(item, recase=False)

	if item["tl_type"] not in ['oel', 'translated']:
		raise ValueError("Invalid TL Type '%s'! Wat?" % item["tl_type"])

	group = get_create_group(item['srcname'], update_id)
	assert group is not None

	kwargs = {
		"input_series_name" : item['series'],
		"tl_type"           : item["tl_type"],
		"changeuser"        : update_id,
	}

	if 'match_author' in item and item['match_author']:
		kwargs['author_name_list'] = item['author']

	series = get_create_series(should_create_series_if_missing=False, **kwargs)

	if not series:
		return

	prefix_match = item.get('prefix_match', False)
	loose_match  = item.get('loose_match', False)

	check_delete_release(item, group, series, update_id, loose_match=loose_match, prefix_match=prefix_match)

def rowToDict(row):
	return {x.name: getattr(row, x.name) for x in row.__table__.columns}

maskedRows = ['id', 'operation', 'srccol', 'changeuser', 'changetime']

def generate_automated_only_change_flags(series):
	inRows  = SeriesChanges                              \
			.query                                     \
			.filter(SeriesChanges.srccol == series.id) \
			.order_by(desc(SeriesChanges.changetime))  \
			.all()

	inRows = [rowToDict(row) for row in inRows]
	inRows.sort(key = lambda x: x['id'])

	# Generate the list of rows we actually want to process by extracting out
	# the keys in the passed row, and masking out the ones we specifically don't want.
	if inRows:
		processKeys = [key for key in inRows[0].keys() if key not in maskedRows]
		processKeys.sort()
	else:
		processKeys = []

	# Prime the loop by building an empty dict to compare against
	previous = {key: None for key in processKeys}

	can_change = {key : True for key in processKeys}

	for row in inRows:
		for key in processKeys:
			if (row[key] != previous[key]) and (row[key] or previous[key]):
				if row['changeuser'] != RSS_USER_ID:
					can_change[key] = False
				previous[key] = row[key]

	return can_change

def update_series_info(item):
	# print("update_series_info", item)
	assert 'title'    in item
	assert 'author'   in item
	assert 'tags'     in item
	assert 'desc'     in item
	assert 'tl_type'  in item

	item = text_tools.fix_dict(item, recase=False)



	print("Series info update message for '%s'!" % item['title'])

	if not 'update_only' in item:
		item['update_only'] = False
	if not 'alt_titles' in item:
		item['alt_titles'] = []

	item['alt_titles'].append(item['title'])
	if item['update_only']:
		series = get_series_from_any(item['alt_titles'], item["tl_type"], item['author'])
	else:
		series = get_create_series(
				input_series_name = item['title'],
				tl_type           = item["tl_type"],
				changeuser        = RSS_USER_ID,
				author_name_list  = item['author']
			)

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

	changeable = generate_automated_only_change_flags(series)
	# print(changeable)
	# print(item)

	# {
	# 	'license_en': True,
	# 	'orig_lang': True,
	# 	'pub_date': True,
	# 	'title': True,
	# 	'description': False,
	# 	'chapter': True,
	# 	'origin_loc': True,
	# 	'website': True,
	# 	'region': True,
	# 	'tl_type': True,
	# 	'tot_chapter': True,
	# 	'orig_status': True,
	# 	'sort_mode': True,
	# 	'volume': True,
	# 	'demographic': True,
	# 	'tot_volume': True,
	# 	'type': True
	# }

	# This only generates a change is it needs to, so we can call it unconditionally.
	if changeable['title']:
		series_tools.updateTitle(series, item['title'])

	if changeable['description'] and 'desc' in item and item['desc']:
		newd = bleach.clean(item['desc'], strip=True, tags = ['p', 'em', 'strong', 'b', 'i', 'a'])
		if newd != series.description and len(newd.strip()):
			series.description = newd
	elif ('desc' in item and item['desc'] and not series.description):
		newd = bleach.clean(item['desc'], strip=True, tags = ['p', 'em', 'strong', 'b', 'i', 'a'])
		if len(newd.strip()):
			series.description = newd

	if 'homepage' in item  and item['homepage']:
		cleaned_homepage = bleach.clean(item['homepage']).lower().strip()
		if (
			not series.website or
			(cleaned_homepage not in series.website.lower() and changeable['website'])
		):

			have_pages = series.website.lower().split("\n") if series.website else []

			have_pages = [pg.strip() for pg in have_pages if pg.strip()]
			have_pages = set(have_pages)


			if len(cleaned_homepage):
				have_pages.add(cleaned_homepage)

				have_pages = list(have_pages)
				have_pages.sort()                # Order resulting site list.

				series.website = "\n".join(have_pages)

	if 'coostate' in item  and item['coostate']:
		if not series.orig_status or (item['coostate'] != series.orig_status and changeable['orig_status']):
			neww = bleach.clean(item['coostate'])
			if  len(neww.strip()):
				series.orig_status = neww

	if 'tl_type' in item  and item['tl_type']:
		if not series.tl_type or (item['tl_type'] != series.tl_type and changeable['tl_type']):
			neww = bleach.clean(item['tl_type']).strip()
			if neww and neww in ['western', 'eastern', 'unknown']:
				series.tl_type = neww

	# if 'transcomplete' in item  and item['transcomplete']:
	# 	if not series.tl_complete or (item['transcomplete'] != series.tl_complete and changeable['transcomplete']):
	# 		neww = item['transcomplete'].strip()
	# 		if neww and neww in ['yes', 'no']:
	# 			series.tl_complete = neww

	if 'licensed' in item  and item['licensed']:
		if not series.license_en or (item['licensed'] != series.license_en and changeable['license_en']):
			neww = item['licensed'].strip().lower()
			if neww and neww in ['yes', 'no']:
				series.license_en = neww == 'yes'

	if 'author' in item and item['author']:
		tmp = item['author']
		if isinstance(tmp, str):
			tmp = [tmp, ]
		series_tools.setAuthorIllust(series, author=tmp, deleteother=False)

	if 'illust' in item and item['illust']:
		tmp = item['illust']
		if isinstance(tmp, str):
			tmp = [tmp, ]
		series_tools.setAuthorIllust(series, illust=tmp, deleteother=False)

	if 'tags' in item and item['tags']:
		series_tools.updateTags(series, item['tags'], deleteother=False, allow_new=item.get('create_tags', False))

	if 'genres' in item and item['genres']:
		series_tools.updateGenres(series, item['genres'], deleteother=False)

	if 'alt_titles' in item and item['alt_titles']:
		series_tools.updateAltNames(series, item['alt_titles']+[item['title'], ], deleteother=False)

	if 'pubnames' in item and item['pubnames']:
		series_tools.updatePublishers(series, item['pubnames'], deleteother=False)

	if 'pubdate' in item and item['pubdate']:
		if not series.pub_date:
			series.pub_date = datetime.datetime.utcfromtimestamp(item['pubdate'])

	if 'sourcesite' in item and item['sourcesite']:
		pass

	series.changeuser = RSS_USER_ID

	db.session.flush()
	db.session.commit()

def dispatchItem(item):
	if isinstance(item, bytes):
		item = item.decode("utf-8")
	item = json.loads(item)
	assert 'type' in item
	assert 'data' in item


	beta_enabled = getattr(settings, "ENABLE_BETA", False)
	if "beta" in item:
		if item['beta'] == True and not beta_enabled:
			return
		elif item['beta'] == True and beta_enabled:
			print("Beta release!")


	for x in range(100):

		try:

			db.session.flush()
			if item['type'] == 'raw-feed':
				# print("Dispatching item of type: ", item['type'])
				insert_raw_item(item['data'])
			elif item['type'] == 'parsed-release':
				# print("Dispatching item of type: ", item['type'])
				insert_parsed_release(item['data'])
			elif item['type'] == 'delete-release':
				# print("Dispatching item of type: ", item['type'])
				delete_parsed_release(item['data'])
			elif item['type'] == 'series-metadata':
				# print("Dispatching item of type: ", item['type'])
				update_series_info(item['data'])
			elif item['type'] == "system-feed-counts":
				pass
			elif item['type'] == "system-update-times":
				pass
			else:
				print(item)
				raise ValueError("No known packet structure in item: '%s'" % item)

			return
		except AssertionError as e:

			print("ERROR INSERTING ROW (attempt %s)!" % x)
			traceback.print_exc()
			try:
				db.session.rollback()
			except Exception:
				print("Rollback failed!")

			if x > 3:
				e.extra_message = "Assertion Error inserting row (attempt %s)!" % x
				raise e

		except sqlalchemy.orm.exc.StaleDataError as e:
			print("ERROR INSERTING ROW (attempt %s)!" % x)
			traceback.print_exc()
			db.session.rollback()
			if x > 20:
				e.extra_message = "Failure after %s retries!" % x
				raise e

		except sqlalchemy.exc.IntegrityError as e:
			print("ERROR INSERTING ROW (attempt %s)!" % x)
			traceback.print_exc()
			db.session.rollback()
			if x > 20:
				e.extra_message = "Failure after %s retries!" % x
				raise e

		except Exception as e:
			print("Unknown error inserting row")
			traceback.print_exc()
			try:
				db.session.rollback()
			except Exception:
				print("Rollback failed!")
			e.extra_message = "Unknown error inserting row"
			raise e


	try:
		db.session.rollback()
	except Exception:
		print("Rollback failed!")

	print("CRITICAL:")
	print("Failed to update item!")

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
				except Exception as exc:
					with open("error - %s.txt" % time.time(), 'w') as fp:
						fp.write("Error inserting item!\n")
						if hasattr(exc, "extra_message"):
							fp.write(exc.extra_message)
							fp.write("\n")
						fp.write("\n")
						fp.write(pprint.pformat(data))
						fp.write("\n")
						fp.write("\n")
						fp.write(traceback.format_exc())
					print("Error!")
					traceback.print_exc()

	def close(self):
		self.feeder.close()

	def __del__(self):
		print("FeedFeeder being deleted")


def amqp_thread_run():
	import flags

	try:
		interface = FeedFeeder()
		for x in range(90):
			interface.process()
			time.sleep(1)
	finally:
		print("Closing")
		interface.close()



if __name__ == '__main__':
	import logSetup
	logSetup.initLogging()
	amqp_thread_run()
