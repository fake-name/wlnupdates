
import re
import json

from app import models
from app import db
from app import app

from . import askUser

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from sqlalchemy import inspect
from app.models import AlternateNames
from app.models import SeriesChanges
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.orm import joinedload_all

def object_as_dict(obj):
	ret = {c.key: getattr(obj, c.key)
			for c in inspect(obj).mapper.column_attrs
}
	ret['row'] = obj
	return ret

def consolidate_seriesid(seriesid):
	print("Fetching rows for SID: ", seriesid)
	srows = SeriesChanges.query                   \
		.filter(SeriesChanges.srccol == seriesid) \
		.order_by(SeriesChanges.id)         \
		.all()

	print("Retreiving rows....")
	srows = [object_as_dict(row) for row in srows]
	print("Fetched %s rows" % len(srows))

	compare_keys = [
		# 'id',   # ID and row are going to be unique per-row, and we don't care.
		# 'row',
		'orig_lang',
		'changetime',
		'website',
		'tot_volume',
		'license_en',
		'tl_type',
		'title',
		'operation',
		'srccol',
		'tot_chapter',
		'region',
		'description',
		'orig_status',
		'pub_date',
		'chapter',
		'demographic',
		'volume',
		'origin_loc',
		'type',
		'changeuser',
		'sort_mode'
	]


	for x in range(1, len(srows)):
		old, new = srows[x-1], srows[x]

		mismatched = False

		for key in compare_keys:
			if old[key] != new[key]:
				mismatched = True

		if not mismatched:
			print("Deleting history id: %s" % new['id'])
			db.session.delete(new['row'])

	print("Done processing series-id %s. Committing." % seriesid)
	db.session.commit()

def flatten_history():
	print("fetching series")
	ret = db.session.execute("""
		SELECT srccol, COUNT(srccol) As cnt
		FROM
			serieschanges
		GROUP BY
			 srccol
		HAVING
			COUNT(srccol) > 10
		ORDER BY
			COUNT(srccol)
		DESC;
		""")

	ret = list(ret)
	print("Fetched %s items" % len(ret))

	for sid, itemcnt in ret:
		consolidate_seriesid(sid)


	# print(ret)


	# items = models.Releases.query.filter(models.Releases.postfix != "").all()

	# mismatch = 0

	# for item in items:
	# 	if re.match(r'^(V\d+)?(C\d+)?( part\d+)?$', item.postfix, re.IGNORECASE):
	# 		item.postfix = ""
	# 		mismatch += 1


	# # for item in items:
	# # 	for name in item.alternatenames:
	# # 		matches = search_for_name(name.name)
	# # 		if matches:
	# # 			try:
	# # 				match_to(name, matches)
	# # 			except sqlalchemy.orm.exc.NoResultFound:
	# # 				print("Row merged already?")

	# db.session.commit()
	# print(len(items))
	# print(mismatch)
	print("wat?")
