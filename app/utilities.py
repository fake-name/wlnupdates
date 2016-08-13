
import datetime
from app.models import Releases
from sqlalchemy.sql.expression import nullslast
from sqlalchemy import desc

def get_latest_release(series):
	latest = Releases                                         \
				.query                                        \
				.filter(Releases.series==series.id)           \
				.filter(Releases.include==True)               \
				.order_by(nullslast(desc(Releases.volume)))   \
				.order_by(nullslast(desc(Releases.chapter)))  \
				.order_by(nullslast(desc(Releases.fragment))) \
				.limit(1)                                     \
				.scalar()

	return latest


def get_latest_releases(series_ids):

	query = Releases                                                               \
				.query                                                             \
				.with_entities(Releases.series, Releases.volume, Releases.chapter, Releases.fragment, Releases.published) \
				.order_by(Releases.series)                                         \
				.order_by(nullslast(desc(Releases.volume)))                        \
				.order_by(nullslast(desc(Releases.chapter)))                       \
				.order_by(nullslast(desc(Releases.fragment)))                      \
				.distinct(Releases.series)                                         \
				.filter(Releases.series.in_(series_ids))                           \
				.filter(Releases.include==True)

	latest = query.all()



	ret = {}
	for series, vol, chp, frag, pubdate in latest:
		if vol == None:
			vol = -1
		if chp == None:
			chp = -1
		if frag == None:
			frag = -1
		if series in ret:
			if vol > ret[series][0]:
				ret[series][0] = (vol, chp, frag)
			elif vol == ret[series][0] and chp > ret[series][1]:
				ret[series][0] = (vol, chp, frag)

			if ret[series][1] < pubdate:
				ret[series][1] = pubdate

		else:
			ret[series] = [(vol, chp, frag), pubdate]

	# Fill out any items which returned nothing.
	for sid in series_ids:
		if not sid in ret:
			ret[sid] = [(-1, -1, -1), None]

	return ret

