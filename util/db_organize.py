
import re
import json
import pprint
import urllib.parse
import tqdm

from app import models
from app import db
from app import app

from . import askUser
from concurrent.futures import ProcessPoolExecutor

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from app.models import AlternateNames
from app.models import Series
from app.models import AlternateTranslatorNames
from app.models import Translators
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc, delete
from sqlalchemy.orm import joinedload
from sqlalchemy import and_

import Levenshtein as lv
from datasketch import MinHash, MinHashLSH
from nltk import ngrams

def pairwise(iterable):
	it = iter(iterable)
	a = next(it, None)

	for b in it:
		yield (a, b)
		a = b

def search_for_seriesname(name, nid):

	similarity = Function('similarity', AlternateNames.cleanname, (name))
	query = select(
			[AlternateNames.series, AlternateNames.cleanname, AlternateNames.name, similarity],
			from_obj=[AlternateNames],
			order_by=desc(similarity)
		).where(
			and_(AlternateNames.cleanname.op("%%")(name), AlternateNames.series != nid)
		).limit(
			10
		)
	# print("Query:", query)
	results = db.session.execute(query).fetchall()

	data = {}


	for mgid, mcleanname, mname, similarity in results:
		if not mgid in data:
			data[mgid] = []

		distance = lv.distance(name, mcleanname)
		# The distance is normalized to the effective changed characters against the
		# entire title length.
		# This should ideally make close short-names not a match.
		distance_corr = 1 - (distance / min(len(name), len(mcleanname)))
		# print("Corrected distance:", distance, distance_corr, len(name), len(mcleanname), min(len(name), len(mcleanname)))
		data[mgid].append((mgid, mcleanname, mname, distance_corr))

	return data

def get_rows(altn):
	query = select(
			[AlternateTranslatorNames.group, AlternateTranslatorNames.cleanname, AlternateTranslatorNames.name],
			from_obj=[AlternateTranslatorNames]
		).where(
			AlternateTranslatorNames.name == altn
		)

	results = db.session.execute(query).fetchall()
	ret = []
	for result in results:
		ret.append((result[0], result[1], result[2], 0.1))
	return ret

def search_for_tlname(name, nid, alts):

	# print("Searching:", (nid, name))

	similarity = Function('similarity', AlternateTranslatorNames.cleanname, (name))
	query = select(
			[AlternateTranslatorNames.group, AlternateTranslatorNames.cleanname, AlternateTranslatorNames.name, similarity],
			from_obj=[AlternateTranslatorNames],
			order_by=desc(similarity)
		).where(
			and_(AlternateTranslatorNames.cleanname.op("%%")(name), AlternateTranslatorNames.group != nid)
		).limit(
			10
		)

	results = db.session.execute(query).fetchall()

	data = {}

	for mgid, mcleanname, mname, similarity in results:
		if not mgid in data:
			data[mgid] = []

		distance = lv.distance(name, mcleanname)
		data[mgid].append((mgid, mcleanname, mname, distance))


	for mgid, mcleanname, mname, similarity in results:
		if not mgid in data:
			data[mgid] = []
		distance = lv.distance(mcleanname, name)
		data[mgid].append((mgid, mcleanname, mname, distance))

	for oid, altn, caltn in alts:
		if not altn:
			continue

		if name.lower().startswith(altn.lower()) or altn.lower().startswith(name.lower()) and altn and name:
			if not oid in data:
				data[oid] = []


			# rows = get_rows(altn)
			# for row in rows:
			# 	data[oid].append(row)

	return data


def print_match(s1, s2, id1, id2, n1, n2, distance):
	print("Merge targets: {} - {} (distance: {})".format(id1, id2, distance))
	print("		Name 1: '{}'".format(n1))
	print("		Name 2: '{}'".format(n2))

	if hasattr(s1, "name"):
		print("	Target Group:")
		print("		Name 1: '{}'".format(s1.name))
		for altn in s1.alt_names:
			print("			Alt: '{}'".format(altn.name))
		print("		Name 2: '{}'".format(s2.name))
		for altn in s2.alt_names:
			print("			Alt: '{}'".format(altn.name))

		print("	URLs:")
		print("		1: https://www.wlnupdates.com/group-id/{}/".format(s1.id))
		print("		2: https://www.wlnupdates.com/group-id/{}/".format(s2.id))


	if hasattr(s1, "title"):
		print("	Target Series:")
		print("		Name 1: '{}'".format(s1.title))
		for altn in s1.alternatenames:
			print("			Alt: '{}'".format(altn.name))
		print("		Name 2: '{}'".format(s2.title))
		for altn in s2.alternatenames:
			print("			Alt: '{}'".format(altn.name))

		print("	Authors:")
		for altn in s1.author: print("			A1: '{}'".format(altn.name))
		if not s1.author: print("			A2: <none>")
		print("		----------")
		for altn in s2.author: print("			A2: '{}'".format(altn.name))
		if not s2.author: print("			A2: <none>")
		print("	Illustrators:")
		for altn in s1.illustrators: print("			A1: '{}'".format(altn.name))
		if not s1.illustrators: print("			A1: <none>")
		print("		----------")
		for altn in s2.illustrators: print("			A2: '{}'".format(altn.name))
		if not s2.illustrators: print("			A2: <none>")

		print("	URLs:")
		print("		1: https://www.wlnupdates.com/series-id/{}/".format(s1.id))
		print("		2: https://www.wlnupdates.com/series-id/{}/".format(s2.id))

def askuser_callback_series(s1, s2, id1, id2, n1, n2, distance):
	print_match(s1, s2, id1, id2, n1, n2, distance)

	do_merge = askUser.query_response_bool("Merge items?")
	if do_merge:
		print("Merging!")
		api_admin.merge_series_ids(s1.id, s2.id)
		print("Merged.")

def merge_query_series(id1, id2, n1, n2, distance, callback):
	s1 = Series.query.filter(Series.id==id1).one()
	s2 = Series.query.filter(Series.id==id2).one()

	# If both series are RoyalRoadL series, and they don't have the
	# same seriesURL, assume it's no-match
	ws1 = s1.website if s1.website is not None else ""
	ws2 = s2.website if s2.website is not None else ""
	urls1 = set([w.strip() for w in ws1.split("\n") if "royalroadl.com" in w])
	urls2 = set([w.strip() for w in ws2.split("\n") if "royalroadl.com" in w])

	if urls1 and urls2 and urls1 != urls2:
		return

	# Don't cross-match OEL and translated series.
	if s1.tl_type != s2.tl_type:
		return

	callback(s1, s2, id1, id2, n1, n2, distance)

def merge_query_group(id1, id2, n1, n2, distance, callback):
	s1 = Translators.query.filter(Translators.id==id1).one()
	s2 = Translators.query.filter(Translators.id==id2).one()


	callback(s1, s2, id1, id2, n1, n2, distance)

class MatchLogBuilder(object):
	def __init__(self):
		self.matchsets = {}
		self.memory = api_admin.get_config_json()



	def add_match_series(self, s1, s2, id1, id2, n1, n2, distance):
		key = (id1, id2) if id1 <= id2 else (id2, id1)

		if key in self.memory['no-merge-series']:
			return
		if key in self.matchsets:
			return
		print_match(s1, s2, id1, id2, n1, n2, distance)
		self.matchsets[key] = {
				"id1"      : int(id1),
				"id2"      : int(id2),
				"n1"       : str(n1),
				"n2"       : str(n2),
				"ns1"      : [str(n.name) for n in s1.alternatenames],
				"ns2"      : [str(n.name) for n in s2.alternatenames],
				"distance" : float(distance),
			}
	def add_match_group(self, s1, s2, id1, id2, n1, n2, distance):
		key = (id1, id2) if id1 <= id2 else (id2, id1)

		if key in self.memory['no-merge-groups']:
			return
		if key in self.matchsets:
			return
		# print_match(s1, s2, id1, id2, n1, n2, distance)
		self.matchsets[key] = {
				"id1"      : id1,
				"id2"      : id2,
				"n1"       : n1,
				"n2"       : n2,
				"ns1"      : [n.name for n in s1.alt_names],
				"ns2"      : [n.name for n in s2.alt_names],
				"ser1"      : list(set([tmp.series_row.title for tmp in s1.releases])),
				"ser2"      : list(set([tmp.series_row.title for tmp in s2.releases])),
				"url1"      : s1.releases[0].srcurl if s1.releases else None,
				"url2"      : s2.releases[0].srcurl if s2.releases else None,
				"distance" : distance,
			}
	def save_log(self, filepath):
		items = list(self.matchsets.values())
		with open(filepath, "w") as fp:
			fp.write(json.dumps(items, indent=4, sort_keys=True))

SIMILARITY_RATIO = 0.85

def match_to_series(target, matches, callback):
	fromid = target.series

	for key in [key for key in matches.keys() if key != fromid]:
		for key, dummy_clean_name, name, similarity in matches[key]:
			if key != fromid:
				if similarity >= SIMILARITY_RATIO:
					merge_query_series(
						id1      = key,
						id2      = target.series,
						n1       = target.name,
						n2       = name,
						distance = similarity,
						callback = callback
						)


def match_to_group(target, matches, callback):
	fromid = target.group


	for key in [key for key in matches.keys() if key != fromid]:
		for key, dummy_clean_name, name, similarity in matches[key]:
			# print((key, target.name, name, similarity))
			if key != fromid:
				if similarity >= SIMILARITY_RATIO:
					merge_query_group(
							id1      = key,
							id2      = target.group,
							n1       = target.name,
							n2       = name,
							distance = similarity,
							callback = callback
							)


def release_merger_series(interactive=False, builder=None):

	if builder:
		matchlogger = builder
	else:
		matchlogger = MatchLogBuilder()

	if interactive:
		callback=askuser_callback_series
	else:
		callback=matchlogger.add_match_series

	print("Fetching releases")
	reldicts = []
	with app.app_context():
		items = models.Releases.query.with_entities(models.Releases.series, models.Releases.srcurl, models.Releases.tlgroup).all()
		print("Fetched %s release objects" % len(items))
		for (series, srcurl, tlgroup) in tqdm.tqdm(items):
			reldicts.append({
				"series"  : series,
				"srcurl"  : srcurl,
				"tlgroup" : tlgroup,
				})

	print("Have %s items." % len(reldicts))

	relmap = {}
	for item in tqdm.tqdm(reldicts):
		relmap.setdefault(item['srcurl'], [])
		relmap[item['srcurl']].append(item)

	print("%s unique release URLs." % len(relmap))

	for key, val in relmap.items():
		if len(val) > 1:
			print("(release_merger_series) More then 1: ", key, )

			sids = list(set([tmp['series'] for tmp in val]))
			if len(sids) > 1:
				for sid_1, sid_2 in pairwise(sids):

					if len(sids) <= sid_1 or len(sids) <= sid_2:
						continue

					print("Match values: ", ((sid_1, val[sid_1]), (sid_2, val[sid_2])))

					# If we have at least 5 netlocs in common
					if val[sid_1] > 5 and val[sid_2] > 5:
						with app.app_context():
							s1 = models.Series.query.filter(
								models.Series.id==sid_1
								).one()
							s2 = models.Series.query.filter(
								models.Series.id==sid_2
								).one()

							print("Merge request for %s -> %s" % (sid_1, sid_2))
							print("	%s " % (s1.title, ))
							print("	%s " % (s2.title, ))

							merge_query_series(
								id1      = sid_1,
								id2      = sid_2,
								n1       = s1.title,
								n2       = s2.title,
								distance = 1,
								callback = callback
								)

def levenshein_merger_series(interactive=True, builder=None):

	if builder:
		matchlogger = builder
	else:
		matchlogger = MatchLogBuilder()

	if interactive:
		callback=askuser_callback_series
	else:
		callback=matchlogger.add_match_series

	print("fetching series")
	with app.app_context():
		items = models.Series.query.options(
			joinedload(Series.alternatenames)
			).all()
		altn = []
		for item in items:
			for name in item.alternatenames:
				altn.append((name.id, name.cleanname))

	print("Sorting names")
	altn.sort(key=lambda x: (x[1], x[0]))

	print("Searching for duplicates from %s names" % len(altn))
	done = 0
	for nid, name in tqdm.tqdm(altn):
		if name == 'RoyalRoadL':
			continue
		with app.app_context():
			matches = search_for_seriesname(name, nid)
			if matches:
				try:
					namerow = models.AlternateNames.query.filter(models.AlternateNames.id==nid).one()
					match_to_series(namerow, matches, callback)
				except sqlalchemy.orm.exc.NoResultFound:
					print("Row merged already?")
		done += 1



	print(len(items))
	print("wat?")

	if not interactive:
		matchlogger.save_log("./seriesname-matchset.json")



def minhash_str(in_str, perms, gram_sz):
	minhash = MinHash(num_perm=perms)
	for d in ngrams(in_str, gram_sz):
		minhash.update("".join(d).encode('utf-8'))
	return minhash


def minhash_merger_series(interactive=True):


	matchlogger = MatchLogBuilder()
	if interactive:
		callback=askuser_callback_series
	else:
		callback=matchlogger.add_match_series

	print("fetching series")
	with app.app_context():
		items = models.Series.query.options(
			joinedload(Series.alternatenames)
			).all()
		altn = []
		for item in items:
			for name in item.alternatenames:
				altn.append((name.id, name.series, name.cleanname, item.title))

	print("Building mapping dictionaries")
	# Map altname id to series id
	altnid_sid_dict  = dict([(tmp[0], tmp[1]) for tmp in altn])
	altnid_name_dict = dict([(tmp[0], tmp[2]) for tmp in altn])
	sid_sname_dict   = dict([(tmp[1], tmp[3]) for tmp in altn])

	sid_altnid_dict = {}
	for nid, sid in altnid_sid_dict.items():
		sid_altnid_dict.setdefault(sid, [])
		sid_altnid_dict[sid].append(nid)


	print("Have %s altnames for %s series" % (len(altnid_sid_dict), len(sid_altnid_dict)))

	perms = 512
	gram_sz = 3
	minhashes = {}
	lsh = MinHashLSH(threshold=SIMILARITY_RATIO, num_perm=perms)

	print("Building lsh minhash data structure")
	with ProcessPoolExecutor(max_workers=8) as ex:
		print("Submitting jobs")
		futures = [(key, ex.submit(minhash_str, content, perms, gram_sz))
				for
					key, content
				in
					altnid_name_dict.items()
				if
					len(content) >= 5
			]

		print("Consuming futures")
		for key, future in tqdm.tqdm(futures):
			minhash = future.result()
			lsh.insert(key, minhash)
			minhashes[key] = minhash

	print("Doing search")

	for key, minhash in minhashes.items():

		result = lsh.query(minhashes[key])
		if key in result:
			result.remove(key)
		if result:
			sid = altnid_sid_dict[result[0]]
			src_sid = altnid_sid_dict[key]
			if sid != src_sid:
				sname = sid_sname_dict[sid]
				res_sids = set([altnid_sid_dict[tmp] for tmp in result])
				names = []
				for res_id in result:
					if altnid_sid_dict[res_id] != src_sid:
						names.append((altnid_sid_dict[res_id], res_id, altnid_name_dict[res_id]))
				if names:
					names.sort()
					print("Search returned %s results in %s series for %s:%s" % (len(result), len(res_sids), src_sid, sname))
					for sid, nid, name in names:
						print("	%s -> %s: %s" % (str(sid).rjust(8), str(nid).rjust(8), name))


	if not interactive:
		matchlogger.save_log("./seriesname-matchset-minhash.json")


def release_merger_groups(interactive=True, builder=None):

	if builder:
		matchlogger = builder
	else:
		matchlogger = MatchLogBuilder()

	if interactive:
		callback=askuser_callback_series
	else:
		callback=matchlogger.add_match_group

	print("Fetching releases")
	reldicts = []

	with app.app_context():
		items = models.Releases.query.with_entities(models.Releases.series, models.Releases.srcurl, models.Releases.tlgroup).all()
		print("Fetched %s release objects" % len(items))
		for (series, srcurl, tlgroup) in tqdm.tqdm(items):
			reldicts.append({
				"series"  : series,
				"srcurl"  : srcurl,
				"tlgroup" : tlgroup,
				})

	print("Have %s items. Parsing out unique netlocs." % len(reldicts))

	tlgroups = set()
	relmap = {}
	for item in tqdm.tqdm(reldicts):
		relnl = urllib.parse.urlsplit(item['srcurl']).netloc
		if relnl:
			relmap.setdefault(relnl, {})
			relmap[relnl].setdefault(item['tlgroup'], 0)
			relmap[relnl][item['tlgroup']] += 1
			tlgroups.add(item['tlgroup'])

	print("%s unique release netlocs, %s groups." % (len(relmap), len(tlgroups)))

	# relmap is a dict[netloc][group] = count_of_releases_at_netloc

	for key, val in relmap.items():
		val = {key : item_cnt for key, item_cnt in val.items() if (item_cnt > 100 and key)}
		if len(val) > 1:
			print("(release_merger_groups) More then 1: key: %s, val: " % (key, ))
			pprint.pprint(val)
			if len(val) > 1:
				for gid_1, gid_2 in pairwise(val):
					with app.app_context():

						try:
							g1 = models.Translators.query.filter(
								models.Translators.id==gid_1
								).one()
							g2 = models.Translators.query.filter(
								models.Translators.id==gid_2
								).one()
							merge_query_group(
									id1      = gid_1,
									id2      = gid_2,
									n1       = g1.name,
									n2       = g2.name,
									distance = 1,
									callback = callback
								)
						except sqlalchemy.orm.exc.NoResultFound:
							print("Missing a source?")
							print("TL IDs: %s, %s" % (gid_1, gid_2))

	if not interactive:
		matchlogger.save_log("./translatorname-matchset.json")


def levenshein_merger_groups(interactive=True, builder=None):

	if builder:
		matchlogger = builder
	else:
		matchlogger = MatchLogBuilder()

	query = delete(AlternateTranslatorNames).where(AlternateTranslatorNames.group == None)
	db.session.execute(query)


	if interactive:
		callback=askuser_callback
	else:
		callback=matchlogger.add_match_group

	print("fetching series")
	with app.app_context():
		items = models.Translators.query.options(
			joinedload(Translators.alt_names)
			).all()
		altn = []
		for item in items:
			for name in item.alt_names:
				altn.append((name.id, name.name, name.cleanname))

	print("Sorting names")
	altn.sort(key=lambda x: (x[1], x[0]))

	print("Searching for duplicates from %s names" % len(altn))
	done = 0
	for nid, name, cleanname in tqdm.tqdm(altn):
		with app.app_context():
			matches = search_for_tlname(cleanname, nid, altn)
			if matches:
				try:
					namerow = models.AlternateTranslatorNames.query.filter(models.AlternateTranslatorNames.id==nid).one()
					match_to_group(namerow, matches, callback)
				except sqlalchemy.orm.exc.NoResultFound:
					print("Row merged already?")
		done += 1


	print(len(items))
	print("wat?")

	if not interactive:
		matchlogger.save_log("./translatorname-matchset.json")


def delete_postfix():
	print("fetching series")
	items = models.Releases.query.filter(models.Releases.postfix != "").all()

	mismatch = 0

	for item in items:
		if re.match(r'^(V\d+)?(C\d+)?( part\d+)?$', item.postfix, re.IGNORECASE):
			item.postfix = ""
			mismatch += 1


	db.session.commit()
	print(len(items))
	print(mismatch)
	print("wat?")
