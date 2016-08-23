
import re

from app import models
from app import db
from app import app

from . import askUser

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from app.models import AlternateNames
from app.models import Series
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.orm import joinedload_all

import Levenshtein as lv

def search_for_name(name):

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

def merge_query(id1, id2, n1, n2, distance):
	s1 = Series.query.filter(Series.id==id1).one()
	s2 = Series.query.filter(Series.id==id2).one()
	print("Merge targets: {} - {}".format(id1, id2))
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

	do_merge = askUser.query_response_bool("Merge items?")
	if do_merge:
		print("Merging!")
		api_admin.merge_series_ids(s1.id, s2.id)
		print("Merged.")
	# print(id1, id2, n1, n2, distance)

def match_to(target, matches):
	fromid = target.series

	for key in [key for key in matches.keys() if key != fromid]:
		for key, dummy_clean_name, name, dummy_similarity in matches[key]:
			if key != fromid:
				dist = lv.distance(target.name, name)
				if dist <= 1:

					merge_query(key, target.series, target.name, name, dist)

	# print("Match from: ", target)
	# print("To: ", matches)


def levenshein_merger():
	print("fetching series")
	with app.app_context():
		items = models.Series.query.all()
		altn = []
		for item in items:
			for name in item.alternatenames:
				altn.append((name.id, name.name))

	print("Searching for duplicates from %s names" % len(altn))
	for nid, name in altn:
		with app.app_context():
			matches = search_for_name(name)
			if matches:
				try:
					namerow = models.AlternateNames.query.filter(models.AlternateNames.id==nid).one()
					match_to(namerow, matches)
				except sqlalchemy.orm.exc.NoResultFound:
					print("Row merged already?")

	print(len(items))
	print("wat?")


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
