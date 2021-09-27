
import pprint
import json
import itertools
import urllib.parse
import tqdm

from app import db
from app import app
from app.models import AlternateNames
from app.models import AlternateNamesChanges
from app.models import AlternateTranslatorNames
from app.models import AlternateTranslatorNamesChanges
from app.models import Author
from app.models import AuthorChanges
from app.models import Genres
from app.models import GenresChanges
from app.models import Illustrators
from app.models import IllustratorsChanges
from app.models import Series
from app.models import SeriesChanges
from app.models import Tags
from app.models import TagsChanges
from app.models import Translators
from app.models import Ratings

from app.models import Covers
from app.models import CoversChanges

from app.models import Releases
from app.models import ReleasesChanges
from app.models import Watches
from app.models import Publishers
from app.models import PublishersChanges

from sqlalchemy import or_

from flask import flash
from flask_babel import gettext
from flask_login import current_user

from flask_login import current_user
import app.series_tools
from app.api_common import getResponse

import FeedFeeder.FeedFeeder
import sqlalchemy.exc


import util.text_tools as text_tools

import app.api_handlers


def setSortOrder(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	# Json request: {'item-id': '32606', 'mode': 'set-sort-mode', 'sort-mode': 'chronological_order'}
	assert data['mode'] == 'set-sort-mode'
	assert 'item-id' in data
	assert 'sort-mode' in data
	mid = int(data['item-id'])
	mode = data['sort-mode']


	assert mode in ['chronological_order', 'parsed_title_order']
	itm = Series.query.filter(Series.id==mid).one()

	print(itm.sort_mode)
	print(itm)

	itm.sort_mode = mode

	db.session.commit()

	return getResponse("Success", False)

	# return getResponse(error=True, message="lolwut!")

def get_config_json():
	val = {}
	try:
		ret = json.load(open("volatile_config.json"))
		if isinstance(ret, dict):
			val = ret
	except FileNotFoundError:
		val = {}
	except json.JSONDecodeError:
		val = {}

	val.setdefault("no-merge-series", [])
	val.setdefault("no-merge-groups", [])
	val.setdefault("delete-tags", [])
	return val


def save_config_json(newdat):
	with open("volatile_config.json", "w") as fp:
		json.dump(newdat, fp, indent="	")

def preventMergeSeriesItems(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'block-merge-id'
	assert 'item-id' in data
	assert 'separate_id' in data

	m1, m2 = int(data['item-id']), int(data['separate_id'])

	m1, m2 = min(m1, m2), max(m1, m2)
	have = get_config_json()


	if not [m1, m2] in have['no-merge-series']:
		have['no-merge-series'].append([m1, m2])
	save_config_json(have)

	return getResponse("Success", False)

def mergeSeriesItems(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'merge-id'
	assert 'item-id' in data
	assert 'merge_id' in data

	m1, m2 = int(data['item-id']), int(data['merge_id'])
	return merge_series_ids(m1, m2)



def preventMergeGroupEntries(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'block-group-merge-id'
	assert 'item-id' in data
	assert 'separate_id' in data

	m1, m2 = int(data['item-id']), int(data['separate_id'])

	m1, m2 = min(m1, m2), max(m1, m2)
	have = get_config_json()


	if not [m1, m2] in have['no-merge-groups']:
		have['no-merge-groups'].append([m1, m2])
	save_config_json(have)

	return getResponse("Success", False)

def mergeGroupEntries(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'do-group-merge-id'
	assert 'item-id' in data
	assert 'merge_id' in data

	m1, m2 = int(data['item-id']), int(data['merge_id'])
	return merge_tl_group_ids(m1, m2)


def mergeGroupItems(data):
	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	assert 'mode' in data
	assert data['mode'] == 'merge-group'
	assert 'item-id' in data
	assert 'merge_id' in data

	m1, m2 = int(data['item-id']), int(data['merge_id'])

	return merge_tl_group_ids(m1, m2)



def merge_tl_group_ids(m1, m2):
	merge_from = max(m1, m2)
	merge_to   = min(m1, m2)

	itm_from = Translators.query.filter(Translators.id==merge_from).one()
	itm_to   = Translators.query.filter(Translators.id==merge_to).one()

	print(itm_from)
	print(itm_to)


	Releases       .query.filter(Releases.tlgroup       ==merge_from).update({'tlgroup': merge_to})
	ReleasesChanges.query.filter(ReleasesChanges.tlgroup==merge_from).update({'tlgroup': merge_to})

	app.api_handlers.updateGroupAltNames(itm_to, [itm.name for itm in itm_from.alt_names], delete=False)

	AlternateTranslatorNamesChanges.query                   \
		.filter(AlternateTranslatorNamesChanges.group==itm_from.id) \
		.delete(synchronize_session="fetch")

	db.session.delete(itm_from)
	db.session.commit()

	return getResponse("Success", False)

def merge_series_ids(m1, m2):
	merge_from = max(m1, m2)
	merge_to   = min(m1, m2)

	itm_from = Series.query.filter(Series.id==merge_from).scalar()
	itm_to = Series.query.filter(Series.id==merge_to).scalar()
	if not itm_from:
		return getResponse("Item from (id: {num}) not found?".format(num=merge_from), error=True)
	if not itm_to:
		return getResponse("Item to (id: {num}) not found?".format(num=merge_to), error=True)


	alts   = []
	author = []
	illust = []
	tags   = []
	genres = []
	publs  = []

	alts.append(itm_from.title)
	for altname in AlternateNames.query.filter(AlternateNames.series==itm_from.id).all():
		alts.append(altname.name)

	for val in Author.query.filter(Author.series==itm_from.id).all():
		author.append(val.name)

	for val in Illustrators.query.filter(Illustrators.series==itm_from.id).all():
		illust.append(val.name)

	for val in Tags.query.filter(Tags.series==itm_from.id).all():
		tags.append(val.tag)

	for val in Genres.query.filter(Genres.series==itm_from.id).all():
		genres.append(val.genre)

	for val in Publishers.query.filter(Publishers.series==itm_from.id).all():
		publs.append(val.name)

	Ratings.query.filter(Ratings.series_id==merge_from).update({'series_id': merge_to})

	# !Ordering here matters!
	# Change-tables have to go second.
	delete_from = [
			AlternateNames,
			AlternateNamesChanges,
			Author,
			AuthorChanges,
			Illustrators,
			IllustratorsChanges,
			Tags,
			TagsChanges,
			Genres,
			GenresChanges,
			Publishers,
			PublishersChanges,
		]

	for clearTable in delete_from:
		clearTable.query.filter(clearTable.series==itm_from.id).delete()

	app.series_tools.updateAltNames   ( itm_to, alts,                deleteother=False )
	app.series_tools.setAuthorIllust  ( itm_to, author     = author, deleteother=False )
	app.series_tools.setAuthorIllust  ( itm_to, illust     = illust, deleteother=False )
	app.series_tools.updateTags       ( itm_to, tags       = tags,   deleteother=False )
	app.series_tools.updateGenres     ( itm_to, genres     = genres, deleteother=False )
	app.series_tools.updatePublishers ( itm_to, publishers = publs,  deleteother=False )

	# For each user watch, if the user is already watching the merge-to item,
	# just delete it. If not, update the user-id
	for watch in Watches.query.filter(Watches.series_id==itm_from.id).all():
		if not Watches                              \
				.query                                  \
				.filter(Watches.series_id==itm_to.id)   \
				.filter(Watches.user_id==watch.user_id) \
				.scalar():

			watch.series_id = itm_to.id

		else:
			db.session.delete(watch)

	if itm_from.description and not itm_to.description:
		itm_to.description = itm_from.description

	if itm_from.description and not itm_to.description:
		itm_to.description = itm_from.description
	if itm_from.type and not itm_to.type:
		itm_to.type = itm_from.type
	if itm_from.origin_loc and not itm_to.origin_loc:
		itm_to.origin_loc = itm_from.origin_loc
	if itm_from.demographic and not itm_to.demographic:
		itm_to.demographic = itm_from.demographic
	if itm_from.orig_lang and not itm_to.orig_lang:
		itm_to.orig_lang = itm_from.orig_lang
	if itm_from.region and not itm_to.region:
		itm_to.region = itm_from.region
	if itm_from.license_en and not itm_to.license_en:
		itm_to.license_en = itm_from.license_en
	if itm_from.orig_status and not itm_to.orig_status:
		itm_to.orig_status = itm_from.orig_status

	if itm_from.pub_date and not itm_to.pub_date:
		itm_to.pub_date = itm_from.pub_date


	if itm_from.website and not itm_to.website:
		itm_to.website = itm_from.website.lower()

	# Merge item links
	elif itm_from.website and itm_to.website:
		websites = list(set(itm_from.website.split("\n") + itm_to.website.split("\n")))
		websites.sort()
		websites = "\n".join(websites)
		itm_to.website = websites


	db.session.flush()
	sid = itm_from.id
	tid = itm_to.id
	Covers.query.filter(Covers.series==sid).update({'series': tid})
	CoversChanges.query.filter(CoversChanges.series==sid).update({'series': tid})

	# Move releases over
	Releases.query.filter(Releases.series==sid).update({'series': tid})
	ReleasesChanges.query.filter(ReleasesChanges.series==sid).update({'series': tid})

	Series.query.filter(Series.id==sid).delete(synchronize_session="fetch")
	SeriesChanges.query.filter(SeriesChanges.id==sid).delete(synchronize_session="fetch")

	db.session.commit()

	app.series_tools.set_rating(sid, new_rating=None)

	return getResponse("Success", False)

def getReleaseFromId(inId):
	ret = Releases.query.filter(Releases.id==inId).one()
	return ret

def toggle_counted(data):
	release = getReleaseFromId(data['id'])
	release.include = not release.include

	app.utilities.update_latest_row(release.series_row)

	db.session.commit()

	flash(gettext('Release %(id)s count-state toggled. New state: %(state)s', id=release.id, state="counted" if release.include else "uncounted"))
	return getResponse("Item count-state toggled!", error=False)

def delete(data):
	release = getReleaseFromId(data['id'])
	db.session.delete(release)
	db.session.commit()
	flash(gettext('Release deleted.'))
	return getResponse("Release deleted.", error=False)


RELEASE_OPS = {
	'toggle-counted' : toggle_counted,
	'delete'         : delete,
}

BOOL_LUT = {
	"True"  : True,
	"False" : False,
}


def alterReleaseItem(data):

	if not current_user.is_mod():
		return getResponse(error=True, message="You have to have moderator privileges to do that!")
	assert 'op' in data
	assert 'mode' in data
	assert 'count' in data
	assert 'id' in data

	assert data['mode'] == "release-ctrl"

	try:
		data['id'] = int(data['id'])
	except ValueError:
		raise AssertionError("Failure converting item ID to integer!")
	assert data['count'] in BOOL_LUT
	data['count'] = BOOL_LUT[data['count']]

	assert data['op'] in RELEASE_OPS

	return RELEASE_OPS[data['op']](data)



def clean_bad_releases(data, admin_override=False):
	badurls = [
		"https://www.novelupdates.com/",
	]

	bad = 0
	for badurl in badurls:
		matches = Releases.query.filter(Releases.srcurl==badurl).all()
		if matches:
			for match in matches:
				bad += 1
				db.session.delete(match)
			db.session.commit()
	print("Deleted %s items." % bad)



def _consolidate_rrl_items():

	dups = db.engine.execute('''
		SELECT
			id, website
		FROM
			series
		WHERE
			website IS NOT NULL AND website != ''
		;''')

	match_num = 0
	paths = {}

	dups = list(dups)

	print("Found %s rows with non-null URLs" % (len(dups), ))
	for idno, website in dups:
		if not ("royalroadl.com" in website.lower() or "royalroad.com" in website.lower()):
			continue


		parsed = urllib.parse.urlsplit(website)
		if not parsed.path in paths:
			paths[parsed.path] = []
		paths[parsed.path].append((idno, website, parsed))

		# matches = Series.query.filter(Series.website==website).all()
		# ids = [match.id for match in matches]
		# zipped = list(zip(ids, ids[1:]))
		# for m1, m2 in zipped:
		# 	match_num += 1
		# 	merge_series_ids(m1, m2)

	long = []
	for key in paths.keys():
		if len(paths[key]) > 1:
			long.append(paths[key])


	for item in long:
		# if not all([(tmp[2].netloc == 'royalroadl.com' or tmp[2].netloc == 'www.royalroadl.com') for tmp in item]):
		if not all((
				all([item[0][2].path   == tmp[2].path for tmp in item]),
				all([item[0][2].query  == tmp[2].query for tmp in item]),
				all([(tmp[2].netloc == 'royalroadl.com' or tmp[2].netloc == 'www.royalroadl.com' or tmp[2].netloc == 'royalroad.com' or tmp[2].netloc == 'www.royalroad.com') for tmp in item]),
			)):
			print("Wat?")
			print([item[0][2].path   == tmp[2].path for tmp in item])
			print([item[0][2].query  == tmp[2].query for tmp in item])
			print([(tmp[2].netloc == 'royalroadl.com' or tmp[2].netloc == 'www.royalroadl.com' or tmp[2].netloc == 'royalroad.com' or tmp[2].netloc == 'www.royalroad.com') for tmp in item])
			print(item)
			assert True == False
		# if not all((
		# 		all([item[0][2].scheme == tmp[2].scheme for tmp in item]),
		# 		all([item[0][2].path   == tmp[2].path for tmp in item]),
		# 		all([item[0][2].query  == tmp[2].query for tmp in item]),
		# 		all([(tmp[2].netloc == 'royalroadl.com' or tmp[2].netloc == 'www.royalroadl.com') for tmp in item]),
		# 	)):
		# 	print("Wut: ", item)
		# 	print("	", all([tmp[2].scheme for tmp in item]))
		# 	print("	", all([tmp[2].path for tmp in item]))
		# 	print("	", all([tmp[2].query for tmp in item]))
		# 	print("	", all([(tmp[2].netloc == 'royalroadl.com' or tmp[2].netloc == 'www.royalroadl.com') for tmp in item]))
		# for sub in item:
		# 	print("	", sub[2])
		print("Need to merge: ", [tmp[0] for tmp in item])


		match_num += 1
		print("merging:", item[0][0], item[1][0])
		merge_series_ids(item[0][0], item[1][0])
		db.session.commit()

	print("Merged: ", match_num)
	return match_num


def consolidate_rrl_items(data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	# We repeatedly execute the merge until it no longer results in any changes.
	match_num = 0
	merged = _consolidate_rrl_items()
	while merged:
		match_num += merged
		merged = _consolidate_rrl_items()

	return getResponse("%s Items merged." % match_num, error=False)

def dump_results(res_list):
	for row in res_list:
		print("	https://www.wlnupdates.com/series-id/%s/ , %s" % (row.series, (
					row.volume, row.chapter, row.fragment, row.postfix
				)
			))

	pass

class MatchTracker():
	def __init__(self):
		self.map = {}

	def add_match(self, s1, s2):

		assert isinstance(s1, int)
		assert isinstance(s2, int)

		if s1 == s2:
			return

		s1, s2 = min((s1, s2)), max((s1, s2))
		self.map.setdefault((s1, s2), 0)
		self.map[(s1, s2)] += 1

def pairwise(iterable):
	"s -> (s0,s1), (s1,s2), (s2, s3), ..."
	a, b = itertools.tee(iterable)
	next(b, None)
	return zip(a, b)

def _update_consolidate_release(mt, from_url, new_url):
	old = Releases.query.filter(Releases.srcurl == from_url).all()
	new = Releases.query.filter(Releases.srcurl == new_url).all()

	if not old:
		print("What?", from_url, new_url)
		return

	if len(old) > 1:
		# print("Multiple old results: ", from_url)
		# dump_results(old)
		map(mt.add_match, pairwise([tmp.series for tmp in old]))
		if new:
			map(mt.add_match, pairwise([tmp.series for tmp in old+new]))
			map(mt.add_match, pairwise([tmp.series for tmp in new+old]))
		return
	if len(new) > 1:
		# print("Multiple new results: ", new_url)
		# dump_results(new)
		map(mt.add_match, pairwise([tmp.series for tmp in new]))
		if old:
			map(mt.add_match, pairwise([tmp.series for tmp in old+new]))
			map(mt.add_match, pairwise([tmp.series for tmp in new+old]))
		return

	if old:
		old, = old
	if new:
		new, = new

	if old and not new:
		old.srcurl = new_url
		db.session.commit()
		return

	if old and new:
		if old.series == new.series:
			db.session.delete(old)
			db.session.commit()
			return


		mt.add_match(old.series, new.series)
		# print("Series mismatch! https://www.wlnupdates.com/series-id/%s , https://www.wlnupdates.com/series-id/%s" % (old.series, new.series))



def consolidate_rrl_releases(data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	rrl = Translators.query.filter(Translators.name == "RoyalRoadL").scalar()

	print("RRL TL Group")
	print(rrl)

	mt = MatchTracker()

	print("Total releases:")
	print(Releases.query.filter(Releases.tlgroup == rrl.id).count())
	print("Loading releases....")
	db.session.execute("BEGIN;")
	urls = Releases.query.with_entities(Releases.srcurl).filter(Releases.tlgroup == rrl.id).all()
	try:
		for srcurl, in tqdm.tqdm(urls):
			if 'http://royalroadl.com/forum/showthread.php?tid=' in srcurl:
				to_delete = Releases.query.filter(Releases.srcurl == srcurl).all()
				for bad in to_delete:
					db.session.delete(bad)
				continue


			fixed = text_tools.clean_fix_url(srcurl)

			if fixed != srcurl:
				to_fix = Releases.query.filter(Releases.srcurl == srcurl).all()
				for row in to_fix:
					row.srcurl = fixed

				db.session.commit()

				# _update_consolidate_release(mt, srcurl, fixed)
				# print("Change: %s <- %s" % (fixed, release.srcurl))
	finally:
		with open("rrl_match_items.json", "w") as fp:
			json.dump(mt.map, fp=fp, indent=4)

	match_num = 0
	return getResponse("%s Items merged." % match_num, error=False)


def flatten_series_by_url(data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	dups = db.engine.execute('''
		SELECT
			website, COUNT(*) AS dupes
		FROM
			series
		WHERE
			website IS NOT NULL AND website != ''
		GROUP
			BY website
		HAVING
			(COUNT(*) > 1);''')
	dups = list(dups)

	match_num = 0
	for website, number in dups:
		if not "royalroadl" in website.lower():
			continue

		matches = Series.query.filter(Series.website==website).all()
		ids = [match.id for match in matches]
		zipped = list(zip(ids, ids[1:]))
		for m1, m2 in zipped:
			match_num += 1
			merge_series_ids(m1, m2)

	return getResponse("%s Items merged." % match_num, error=False)

def delete_duplicate_releases(data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	dups = db.engine.execute('''
		SELECT
			srcurl, COUNT(*) AS dupes
		FROM
			releases
		WHERE
			srcurl IS NOT NULL AND srcurl != ''
		GROUP
			BY srcurl
		HAVING
			(COUNT(*) > 1);''')
	dups = list(dups)

	match_num = 0
	mismatches = set()
	for release_url, number in dups:
		matches = Releases.query.filter(Releases.srcurl==release_url).all()
		zipped = list(zip(matches, matches[1:]))
		for m1, m2 in zipped:
			if m1.series != m2.series:
				tup = (int(m1.series), int(m2.series))
				if tup not in mismatches:
					print("Mismatch: ", m1.series, m2.series, m1.srcurl, m2.srcurl)
					mismatches.add(tup)
			else:
				match_num += 1
				# print(m1.series, m2.series)

				# Pick the older version, since untimed duplicates keep
				# cropping up from japtem.
				# However, if a newer release has a postfix, go with that instead.
				if m2.postfix and m2.postfix != m1.postfix:
					older = m2
					newer = m1
				elif m1.changetime < m2.changetime:
					older = m1
					newer = m2
				else:
					older = m2
					newer = m1
				if not older.include:
					# If the to-be-removed chapter has been expliclty excluded from
					# the chapter count, don't do the merge.
					pass
				else:
					db.session.delete(newer)
					db.session.commit()

	# print(dups)
	# print(list(dups))
	mismatches = list(mismatches)

	with open("rrl_match_items.json", "w") as fp:
		json.dump(mismatches, fp=fp, indent=4)


	return getResponse("%s Items merged." % match_num, error=False)

def fix_escaped_quotes(dummy_data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	# SELECT * FROM series WHERE title LIKE E'%\\\'%';
	bad_title = 0


	q = Series.query.filter(or_(Series.title.like(r"%'%"), Series.title.like(r"%’%"), Series.title.like(r"%‘%"), Series.title.like(r"%“%"), Series.title.like(r"%”%")))
	items = q.all()
	print("Name fixing processing query resulted in %s items" % len(items))
	for item in items:
		old = item.title
		new = old
		while any([r"\"" in new, r"\'" in new, "’" in new, "‘" in new, "“" in new, "”" in new]):
			new = new.replace(r"\'", "'")
			new = new.replace(r'\"', '"')
			new = new.replace(r"’", "'")
			new = new.replace(r"‘", "'")
			new = new.replace(r"“", '"')
			new = new.replace(r"”", '"')

		have = Series.query.filter(Series.title == new).scalar()
		if old != new:
			if have:
				print("Duplicate item!", (old, new), old==new)
				merge_series_ids(have.id, item.id)
			else:
				print("Fixing title.")
				item.title = new
				db.session.commit()
			bad_title += 1

	bad_alt_title = 0


	q = AlternateNames.query.filter(or_(AlternateNames.name.like(r"%'%"), AlternateNames.name.like(r"%’%"), AlternateNames.name.like(r"%‘%"), AlternateNames.name.like(r"%“%"), AlternateNames.name.like(r"%”%")))

	conflicts = ''
	items = q.all()
	print("Alternate names processing query resulted in %s items" % len(items))
	for item in items:
		old = item.name
		new = old
		while any([r"\"" in new, r"\'" in new, "’" in new, "‘" in new, "“" in new, "”" in new]):
			new = new.replace(r"\'", "'")
			new = new.replace(r'\"', '"')
			new = new.replace(r"’", "'")
			new = new.replace(r"‘", "'")
			new = new.replace(r"“", '"')
			new = new.replace(r"”", '"')
		if old != new:
			haves = AlternateNames.query.filter(AlternateNames.name == new).all()
			# assert(len(have) <= 1), "too many results - '%s'" % [(t.id, t.series, t.name) for t in have]

			for have in haves:
				if have.series == item.series:
					print("Duplicate names")
					assert have.series == item.series
					# We don't care about duplicates if one is the escaped version of the other
					db.session.delete(item)
					db.session.commit()
				else:
					conflicts += """\nSeries mismatch?\nSeries %s: '%s'\nSeries %s: '%s'""" % (have.series, have.name, item.series, item.name)
					print("Wat?", have.name, item.name)
					print("Wat?", have.series, item.series)
			else:
				print("Fixing title.")
				item.name = new
				db.session.commit()
			bad_alt_title += 1

	bad_desc = 0



	# FUCK ALL SMART QUOTE BULLSHITS EVER
	q = Series.query.filter(or_(Series.description.like(r"%'%"), Series.description.like(r"%’%"), Series.description.like(r"%‘%"), Series.description.like(r"%“%"), Series.description.like(r"%”%")))

	items = q.all()
	print("Series description processing query resulted in %s items" % len(items))
	for item in items:
		old = item.description
		new = old

		while any([r"\"" in new, r"\'" in new, "’" in new, "‘" in new, "“" in new, "”" in new]):
			new = new.replace(r"\'", "'")
			new = new.replace(r'\"', '"')
			new = new.replace(r"’", "'")
			new = new.replace(r"‘", "'")
			new = new.replace(r"“", '"')
			new = new.replace(r"”", '"')
		if old != new:
			print("Fixing description smart-quotes and over-escapes for series: %s" % item.id)
			item.description = new
			db.session.commit()
			bad_desc += 1

	print("Update complete.")

	return getResponse("%s main titles, %s alt titles, %s descriptions required fixing.%s" % (bad_title, bad_alt_title, bad_desc, conflicts), error=False)


def clean_singleton_tags(dummy_data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")
	bad_tags = 0

	bad_tags = db.session.execute('''
		SELECT
			COUNT(*)
		FROM
			tags
		WHERE
			tag IN (
			SELECT tag
			FROM (
				SELECT tag
				FROM tags
				GROUP BY tag
				HAVING COUNT(*) = 1
			) AS ONLY_ONCE
			)
		''')

	bad_tags = list(bad_tags)

	db.session.execute('''
		DELETE
		FROM
			tags
		WHERE
			tag IN (
			SELECT tag
			FROM (
				SELECT tag
				FROM tags
				GROUP BY tag
				HAVING COUNT(*) = 1
			) AS ONLY_ONCE
			)
		;
		''')
	db.session.commit()

	return getResponse("Found %s tags that required patching." % (bad_tags), error=False)

def delete_bad_tags(dummy_data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")

	conf = get_config_json()
	print("Bad tags:", conf['delete-tags'])
	removed = 0
	for bad_tag in conf['delete-tags']:
		items = Tags.query.filter(Tags.tag == bad_tag).count()
		print("Found %s instances of tag: %s" % (items, bad_tag))
		removed += 1
		Tags.query.filter(Tags.tag == bad_tag).delete()

	save_config_json(conf)
	removed = 0
	return getResponse("Found %s tags that required patching." % (removed), error=False)


def check_merge(fromrow):
	other = Series.query.filter(Series.title == fromrow.title.strip()).one()
	if fromrow.title.strip() == other.title.strip():
		fromauths = [auth.name for auth in fromrow.author]
		toauths   = [auth.name for auth in other.author]
		if (fromrow.tl_type == other.tl_type and
			fromauths == toauths and
			fromauths ):

			print("Wut")

			print("	", (fromrow.title, other.title))
			print("	", (fromrow.tl_type, other.tl_type))
			print("	", (fromauths, toauths))

			print("Doing merge")
			merge_series_ids(fromrow.id, other.id)
			return
	print("Mismatch:")
	print("	URLs:")
	print("		1: https://www.wlnupdates.com/series-id/{}/".format(fromrow.id))
	print("		2: https://www.wlnupdates.com/series-id/{}/".format(other.id))

def clean_spaces(dummy_data, admin_override=False):
	if admin_override is False and (not current_user.is_mod()):
		return getResponse(error=True, message="You have to have moderator privileges to do that!")


	items = Series.query.all()

	for item in items:
		if item.title != item.title.strip():

			item.title = item.title.strip()

			try:
				db.session.commit()
			except sqlalchemy.exc.IntegrityError:
				db.session.rollback()
				check_merge(item)

	# return getResponse("Found %s tags that required patching." % (bad_tags), error=False)

def deleteSeries(data):

	if not current_user.is_mod():
		return getResponse(error=True, message="I see what you (tried) to do there!")
	assert 'item-id' in data
	assert 'mode' in data

	delete_id = data["item-id"]
	clean_item = Series.query.filter(Series.id==delete_id).one()


	# !Ordering here matters!
	# Change-tables have to go second.
	delete_from = [
			AlternateNames,
			AlternateNamesChanges,
			Author,
			AuthorChanges,
			Illustrators,
			IllustratorsChanges,
			Tags,
			TagsChanges,
			Genres,
			GenresChanges,
			Publishers,
			PublishersChanges,
			Covers,
			CoversChanges,
			Releases,
			ReleasesChanges,
			# Series,
			# SeriesChanges,
		]


	for clearTable in delete_from:
		clearTable.query.filter(clearTable.series==clean_item.id).delete()

	Ratings.query.filter(Ratings.series_id==clean_item.id).delete()
	Watches.query.filter(Watches.series_id==clean_item.id).delete()

	Series.query.filter(Series.id==clean_item.id).delete()
	SeriesChanges.query.filter(SeriesChanges.srccol==clean_item.id).delete()
	# db.session.delete(clean_item)
	db.session.commit()

	return getResponse("Series was deleted entirely!", error=False)

def deleteAutoReleases(data):

	if not current_user.is_mod():
		return getResponse(error=True, message="I see what you (tried) to do there!")

	assert 'item-id' in data
	assert 'mode' in data
	assert data['mode'] == "delete-auto-releases"

	try:
		delete_id = int(data["item-id"])
	except ValueError:
		raise AssertionError("Failure converting item ID to integer!")


	clean_item = Series.query.filter(Series.id==delete_id).one()

	print(clean_item)
	for release in clean_item.releases:
		if release.changeuser == FeedFeeder.FeedFeeder.RSS_USER_ID:
			db.session.delete(release)
			# print(release.id, release.volume, release.chapter, release.postfix, release.changeuser)
		else:
			print("Not deleting: ", release.id, release.volume, release.chapter, release.postfix, release.changeuser)

	app.utilities.update_latest_row(clean_item)

	db.session.commit()

	return getResponse("Autogen releases deleted. Reloading.", error=False)

def deleteGroup(data):
	return getResponse("Not implemented yet!", error=True)

	# if not current_user.is_mod():
	# 	return getResponse(error=True, message="I see what you (tried) to do there!")
	# assert 'item-id' in data
	# assert 'mode' in data

	# delete_id = data["item-id"]
	# clean_item = Series.query.filter(Series.id==delete_id).one()


	# # !Ordering here matters!
	# # Change-tables have to go second.
	# delete_from = [
	# 		AlternateNames,
	# 		AlternateNamesChanges,
	# 		Author,
	# 		AuthorChanges,
	# 		Illustrators,
	# 		IllustratorsChanges,
	# 		Tags,
	# 		TagsChanges,
	# 		Genres,
	# 		GenresChanges,
	# 		Publishers,
	# 		PublishersChanges,
	# 		Covers,
	# 		CoversChanges,
	# 		Releases,
	# 		ReleasesChanges,
	# 		# Series,
	# 		# SeriesChanges,
	# 	]


	# for clearTable in delete_from:
	# 	clearTable.query.filter(clearTable.series==clean_item.id).delete()

	# Watches.query.filter(Watches.series_id==clean_item.id).delete()
	# Series.query.filter(Series.id==clean_item.id).delete()
	# SeriesChanges.query.filter(SeriesChanges.srccol==clean_item.id).delete()
	# # db.session.delete(clean_item)
	# db.session.commit()

	return getResponse("Series was deleted entirely!", error=False)

def deleteGroupAutoReleases(data):

	if not current_user.is_mod():
		return getResponse(error=True, message="I see what you (tried) to do there!")

	assert 'item-id' in data
	assert 'mode' in data
	assert data['mode'] == "delete-auto-from-group"

	try:
		delete_id = int(data["item-id"])
	except ValueError:
		raise AssertionError("Failure converting item ID to integer!")


	clean_item = Translators.query.filter(Translators.id==delete_id).one()

	print(clean_item)
	for release in clean_item.releases:
		if release.changeuser == FeedFeeder.FeedFeeder.RSS_USER_ID:
			db.session.delete(release)
			# print(release.id, release.volume, release.chapter, release.postfix, release.changeuser)
		else:
			print("Not deleting: ", release.id, release.volume, release.chapter, release.postfix, release.changeuser)

	db.session.commit()

	return getResponse("Autogen releases deleted. Reloading.", error=False)

def bulkToggleVolumeCountedStatus(data):

	if not current_user.is_mod():
		return getResponse(error=True, message="I see what you (tried) to do there!")

	assert 'item-id' in data
	assert 'mode'    in data
	assert 'enable'  in data
	assert data['mode'] == "toggle-volume-releases"

	try:
		series_id = int(data["item-id"])
	except ValueError:
		raise AssertionError("Failure converting item ID to integer!")

	enable = data['enable']
	assert enable in ['Include', 'Exclude']

	should_include = enable == 'Include'


	item_row = Series.query.filter(Series.id==series_id).one()

	print(item_row)
	for release in item_row.releases:
		if release.changeuser == FeedFeeder.FeedFeeder.RSS_USER_ID or release.changeuser == FeedFeeder.FeedFeeder.NU_SRC_USER_ID:
			if release.volume:
				release.include = should_include


	app.utilities.update_latest_row(item_row)

	db.session.commit()

	return getResponse("Autogen releases deleted. Reloading.", error=False)
