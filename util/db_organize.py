
import re
import json

from app import models
from app import db
from app import app

from . import askUser

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from app.models import AlternateNames
from app.models import Series
from app.models import AlternateTranslatorNames
from app.models import Translators
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.orm import joinedload_all

import Levenshtein as lv

def search_for_seriesname(name):

	similarity = Function('similarity', AlternateNames.cleanname, (name))
	query = select(
			[AlternateNames.series, AlternateNames.cleanname, AlternateNames.name, similarity],
			from_obj=[AlternateNames],
			order_by=desc(similarity)
		).where(
			AlternateNames.cleanname.op("%%")(name)
		).limit(
			50
		)

	results = db.session.execute(query).fetchall()

	data = {}

	for result in results:
		dbid = result[0]
		if not dbid in data:
			data[dbid] = {}

			data[dbid] = []
		data[dbid].append(result)

	return data

def search_for_tlname(name):

	similarity = Function('similarity', AlternateTranslatorNames.cleanname, (name))
	query = select(
			[AlternateTranslatorNames.group, AlternateTranslatorNames.cleanname, AlternateTranslatorNames.name, similarity],
			from_obj=[AlternateTranslatorNames],
			order_by=desc(similarity)
		).where(
			AlternateTranslatorNames.cleanname.op("%%")(name)
		).limit(
			50
		)

	results = db.session.execute(query).fetchall()

	data = {}

	for result in results:
		dbid = result[0]
		if not dbid in data:
			data[dbid] = {}

			data[dbid] = []
		data[dbid].append(result)

	return data


def print_match(s1, s2, id1, id2, n1, n2, distance):
	print("Merge targets: {} - {} (distance: {})".format(id1, id2, distance))
	print("		Name 1: '{}'".format(n1))
	print("		Name 2: '{}'".format(n2))
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

		if key in self.memory['no-merge']:
			return
		if key in self.matchsets:
			return
		print_match(s1, s2, id1, id2, n1, n2, distance)
		self.matchsets[key] = {
				"id1"      : id1,
				"id2"      : id2,
				"n1"       : n1,
				"n2"       : n2,
				"ns1"      : [n.name for n in s1.alternatenames],
				"ns2"      : [n.name for n in s2.alternatenames],
				"distance" : distance,
			}
	def add_match_group(self, s1, s2, id1, id2, n1, n2, distance):
		key = (id1, id2) if id1 <= id2 else (id2, id1)

		if key in self.memory['no-merge']:
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


def match_to_series(target, matches, callback):
	fromid = target.series


	for key in [key for key in matches.keys() if key != fromid]:
		for key, dummy_clean_name, name, dummy_similarity in matches[key]:
			if key != fromid:
				dist = lv.distance(target.name, name)
				if dist <= 1:

					merge_query_series(key, target.series, target.name, name, dist, callback=callback)


def match_to_group(target, matches, callback):
	fromid = target.group


	for key in [key for key in matches.keys() if key != fromid]:
		for key, dummy_clean_name, name, dummy_similarity in matches[key]:
			if key != fromid:
				dist = lv.distance(target.name, name)
				if dist <= 1:

					merge_query_group(key, target.group, target.name, name, dist, callback=callback)

def levenshein_merger_series(interactive=True):

	matchlogger = MatchLogBuilder()
	if interactive:
		callback=askuser_callback_series
	else:
		callback=matchlogger.add_match_series

	print("fetching series")
	with app.app_context():
		items = models.Series.query.all()
		altn = []
		for item in items:
			for name in item.alternatenames:
				altn.append((name.id, name.name))

	print("Sorting names")
	altn.sort(key=lambda x: (x[1], x[0]))

	print("Searching for duplicates from %s names" % len(altn))
	for nid, name in altn:
		if name == 'RoyalRoadL':
			continue
		with app.app_context():
			matches = search_for_seriesname(name)
			if matches:
				try:
					namerow = models.Alterna.query.filter(models.AlternateNames.id==nid).one()
					match_to_series(namerow, matches, callback)
				except sqlalchemy.orm.exc.NoResultFound:
					print("Row merged already?")


	print(len(items))
	print("wat?")

	if not interactive:
		matchlogger.save_log("./seriesname-matchset.json")



def levenshein_merger_groups(interactive=True):


	matchlogger = MatchLogBuilder()
	if interactive:
		callback=askuser_callback
	else:
		callback=matchlogger.add_match_group

	print("fetching series")
	with app.app_context():
		items = models.Translators.query.all()
		altn = []
		for item in items:
			for name in item.alt_names:
				altn.append((name.id, name.name))

	print("Sorting names")
	altn.sort(key=lambda x: (x[1], x[0]))

	print("Searching for duplicates from %s names" % len(altn))
	for nid, name in altn:
		with app.app_context():
			matches = search_for_tlname(name)
			if matches:
				try:
					namerow = models.AlternateTranslatorNames.query.filter(models.AlternateTranslatorNames.id==nid).one()
					match_to_group(namerow, matches, callback)
				except sqlalchemy.orm.exc.NoResultFound:
					print("Row merged already?")


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


	# for item in items:
	# 	for name in item.alternatenames:
	# 		matches = search_for_name(name.name)
	# 		if matches:
	# 			try:
	# 				match_to(name, matches)
	# 			except sqlalchemy.orm.exc.NoResultFound:
	# 				print("Row merged already?")

	db.session.commit()
	print(len(items))
	print(mismatch)
	print("wat?")
