
from app.models import Releases
from sqlalchemy.sql.expression import nullslast
from sqlalchemy import desc

def get_latest_release(series):
	latest = Releases                                        \
				.query                                       \
				.filter(Releases.series==series.id)          \
				.filter(Releases.include==True)              \
				.order_by(nullslast(desc(Releases.volume)))  \
				.order_by(nullslast(desc(Releases.chapter))) \
				.limit(1)                                    \
				.scalar()

	return latest


def get_latest_releases(series_ids):
	query = Releases                                                              \
				.query                                                             \
				.with_entities(Releases.series, Releases.volume, Releases.chapter) \
				.distinct(Releases.series)                                         \
				.filter(Releases.series.in_(series_ids))                           \
				.filter(Releases.include==True)

	latest = query.all()
				# .group_by(Releases.series)                   \
				# .distinct(Releases.series)                   \



	ret = {}
	for series, vol, chp in latest:
		if vol == None:
			vol = -1
		if chp == None:
			chp = -1
		if series in ret:
			if vol > ret[series][0]:
				ret[series] = [vol, chp]
			elif vol == ret[series][0] and chp > ret[series][1]:
				ret[series] = [vol, chp]

		else:
			ret[series] = [vol, chp]

	# Fill out any items which returned nothing.
	for sid in series_ids:
		if not sid in ret:
			ret[sid] = [-1, -1]

	return ret

