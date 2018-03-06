
import ast
import json

import tqdm
import Levenshtein as lv

from app import models
from app import db
from app import app

from app.sub_views import search

from sqlalchemy.sql.expression import nullslast
from app.models import AlternateNames
from app.models import CommonTags
from app.models import CommonGenres
from app.models import Tags
from app.models import Genres
from app.models import Series
from app.models import Releases
from app.models import Watches
import app.nameTools as nt
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc, distinct


def title_search(searchterm):
	query, searchtermprocessed = search.generate_similarity_query(searchterm)
	results = db.session.execute(query).fetchall()



	return results[0][2] if results else None

def do_search():
	with open("dotted.pyson") as rb:
		content = rb.read()

	cont = ast.literal_eval(content)

	name_map = {}
	with app.app_context():
		for name in tqdm.tqdm(cont):
			match = title_search(name)
			if match:
				shortened = name[:-3]
				dist = lv.distance(shortened.lower(), match[:len(shortened)].lower())
				if dist <= 10:
					name_map[name] = match
				else:
					print("What?", (dist, name, match))
			else:
				print("Missing:", (name, ))

	with open("fix_map.json", "w") as fp:
		fp.write(json.dumps(name_map, indent=4))

