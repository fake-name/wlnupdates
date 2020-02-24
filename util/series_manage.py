
import re
import json
import pprint
import tqdm
import sqlalchemy.orm.exc
from sqlalchemy import inspect
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.orm import joinedload_all

import Levenshtein as lv

from app import models
from app import db
from app import app
import app.series_tools
from app import tag_lut

from . import askUser

import app.api_handlers_admin as api_admin

from app.models import CommonTags
from app.models import Tags
from app.models import Genres
from app.models import Series

from app.models import AlternateNames
from app.models import SeriesChanges

import app.series_tools as series_tools
from app import tag_lut




def update_series_metadata_column():
	print("Updating series metadata and latest chap")

	sids = db.session.query(Series.id).all()
	sids = [tmp[0] for tmp in sids]

	sids.sort(reverse=True)


	loops = 0
	for sid in tqdm.tqdm(sids):

		row = Series.query.filter(Series.id == sid).one()
		app.utilities.update_metadata(row)
		app.utilities.update_latest_row(row)
		loops += 1
		if loops % 1000 == 0:
			db.session.flush()

	db.session.commit()