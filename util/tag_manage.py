
import re
import json
import pprint

from app import models
from app import db
from app import app
import app.series_tools
from app import tag_lut

from . import askUser

import app.api_handlers_admin as api_admin

import sqlalchemy.orm.exc
from sqlalchemy import inspect
from app.models import CommonTags
from app.models import Tags
from app.models import Series

from app.models import AlternateNames
from app.models import SeriesChanges
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.orm import joinedload_all



def replace_tag(oldname, newname):
	print("Replacing: ", (oldname, newname))
	to_fix = Tags.query.filter(Tags.tag == oldname).all()
	matched_series = [tag.series_row for tag in to_fix]

	for series in matched_series:
		tag_taglist = [tag.tag for tag in series.tags]
		changed = False
		if oldname in tag_taglist:
			changed = True
			tag_taglist.remove(oldname)
		if not newname in tag_taglist:
			changed = True
			tag_taglist.append(newname)
		if changed:
			app.series_tools.updateTags(series, tag_taglist)
	print("Committing changes.")
	db.session.commit()


def dedup_tags():
	print("fetching series")
	items = CommonTags.query.all()
	items = [(item.tag, item.tag_instances) for item in items]
	items.sort()
	tag_names = set([item[0] for item in items])

	# I prefer the slash plural option.
	bad_pairs = []
	for tagn in [tmp for tmp in tag_names if "/" in tmp]:
		no_slash    = tagn.replace("/", "")
		slash_trunc = tagn.split("/")[0]
		if no_slash in tag_names:
			bad_pairs.append((no_slash, tagn))
		if slash_trunc in tag_names:
			bad_pairs.append((slash_trunc, tagn))

	for tagn in [tmp for tmp in tag_names if "&amp;" in tmp]:
		fixed_ampersand = tagn.replace("&amp;", "&")
		if fixed_ampersand in tag_names:
			bad_pairs.append((tagn, fixed_ampersand))


	for tagn in tag_names:
		if tagn.endswith("-protagonist"):
			fixed = tagn[:len("-protagonist") * -1] + "-lead"
			bad_pairs.append((tagn, fixed))

	for old, new in bad_pairs:
		replace_tag(old, new)

	for fix_tag in tag_lut.tag_fix_lut.keys():
		to_fix = Tags.query.filter(Tags.tag == fix_tag).all()
		matched_series = [tag.series_row for tag in to_fix]
		print("Doing fixes for fix_tag (%s): %s" % (fix_tag, len(matched_series)))
		for series in matched_series:
			tag_taglist = [tag.tag for tag in series.tags]
			app.series_tools.updateTags(series, tag_taglist)

	for base, dependent in tag_lut.tag_extend_lut.items():
		base_i = Tags.query.filter(Tags.tag == base).all()
		dependent_i = Tags.query.filter(Tags.tag == dependent).all()
		base_t = [tmp.series for tmp in base_i]
		dependent_t = [tmp.series for tmp in dependent_i]

		for sid in base_t:
			if sid not in dependent_t:
				series = Series.query.filter(Series.id == sid).one()
				stags = [tag.tag for tag in series.tags]
				app.series_tools.updateTags(series, stags)
				print("Need to fix: ", sid)

	print("wat?")



