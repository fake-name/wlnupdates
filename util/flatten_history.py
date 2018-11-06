
import re
import json
import tqdm

from app import models
from app import db
from app import app

from . import askUser

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from sqlalchemy import inspect
from app.models import AlternateNames
from app.models import Series
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

def purge_dup_oel_author_tags(seriesid):
	srow = Series.query                   \
		.filter(Series.id == seriesid) \
		.scalar()

	if srow.tl_type == 'oel' and srow.website and 'royalroad' in srow.website:
		if "\n" in srow.website.strip():
			return
		popauth = len(list(srow.author))
		if popauth > 2:
			print(seriesid, srow.tl_type, [tmp.name for tmp in srow.author], srow.website)
			while popauth > 1:
				print("Popping")
				popauth -= 1
				db.session.delete(srow.author[0])
			srow.tags.clear()
			for release in srow.releases:
				db.session.delete(release)

			for altname in srow.alternatenames:
				if altname.name != srow.title:
					db.session.delete(altname)

def consolidate_seriesid(seriesid, purge_dup_oel_authors=False):
	if purge_dup_oel_authors:
		purge_dup_oel_author_tags(seriesid)

	print("Fetching rows for SID: ", seriesid)
	srows = SeriesChanges.query                   \
		.filter(SeriesChanges.srccol == seriesid) \
		.order_by(SeriesChanges.id)         \
		.all()

	print("Retreiving rows....")
	srows = [object_as_dict(row) for row in srows]
	print("Fetched %s rows" % len(srows))


	compare_keys = [
		# ID and row are going to be unique per-row, and we don't care.
		# 'id',
		# 'row',

		# We specifically want to ignore changes to the latest xxx cols.
		# 'latest_volume',
		# 'latest_chapter',
		# 'latest_fragment',

		# And the count of releases
		# 'release_count',
		# 'latest_published',

		# Also ignore rating changes
		# 'rating',
		# 'rating_count',

		# 'operation',
		# 'srccol',
		# 'changeuser',
		# 'changetime',

		'orig_lang',
		'website',
		'license_en',
		'tl_type',
		'title',
		'region',
		'description',
		'orig_status',
		'pub_date',
		'demographic',
		'origin_loc',
		'type',
		'sort_mode'
	]


	all_keys = [

		# We specifically want to ignore changes to the latest xxx cols.
		'latest_volume',
		'latest_chapter',
		'latest_fragment',

		# And the count of releases
		'release_count',
		'latest_published',

		# Also ignore rating changes
		'rating',
		'rating_count',
		'operation',
		'srccol',
		'changeuser',
		'changetime',

		'orig_lang',
		'website',
		'license_en',
		'tl_type',
		'title',
		'region',
		'description',
		'orig_status',
		'pub_date',
		'demographic',
		'origin_loc',
		'type',
		'sort_mode'
	]
	fixes = 0
	deletes = 0
	for x in tqdm.tqdm(range(1, len(srows))):
		old, new = srows[x-1], srows[x]

		mismatched = False

		for key in compare_keys:
			if old[key] != new[key]:
				mismatched = True
				print("Mismatch", (old[key],  new[key]))


		diff = {(key, old[key], new[key]) for key in all_keys if old[key] != new[key]}

		if not mismatched:
			if diff:
				print("Deleting history for %s, id: %s (%s)" % (seriesid, new['id'], diff))
			db.session.delete(new['row'])
			fixes += 1
			deletes += 1
			if fixes > 10:
				fixes = 0
				db.session.flush()

		# print("Diff", diff)

	print("Done processing series-id %s, deleting %s change rows. Committing." % (seriesid, deletes))
	db.session.commit()

def flatten_history(purge_dup_oel_authors):
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
		consolidate_seriesid(sid, purge_dup_oel_authors=purge_dup_oel_authors)


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

if __name__ == '__main__':
	flatten_history(True)
