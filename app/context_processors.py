
import datetime
import urllib.parse

from babel.dates import format_datetime
from .models import Users, Translators

from app import app

CACHE_SIZE = 5000
userIdCache = {}
tlGroupIdCache = {}


def getUserId(idNo):
	if idNo in userIdCache:
		return userIdCache[idNo]
	user = Users.query.filter_by(id=idNo).one()
	userIdCache[user.id] = user.nickname

	# Truncate the cache if it's getting too large
	if len(userIdCache) > CACHE_SIZE:
		userIdCache.popitem()

	return userIdCache[user.id]

def getTlGroupId(idNo):
	if idNo in tlGroupIdCache:
		return tlGroupIdCache[idNo]
	group = Translators.query.filter_by(id=idNo).one()
	tlGroupIdCache[group.id] = group.name

	# Truncate the cache if it's getting too large
	if len(tlGroupIdCache) > CACHE_SIZE:
		tlGroupIdCache.popitem()

	return tlGroupIdCache[group.id]


def format_date(value, format='medium'):
	return format_datetime(value, "EE yyyy.MM.dd")

def format_js_date(din):
	return din.strftime("%Y/%m/%d %H:%M")

def date_now():
	return datetime.datetime.today().strftime("%Y/%M/%d %H:%M")

def ago(then):
	now = datetime.datetime.now()
	delta = now - then

	d = delta.days
	h, s = divmod(delta.seconds, 3600)
	m, s = divmod(s, 60)
	labels = ['d', 'h', 'm', 's']
	dhms = ['%s %s' % (i, lbl) for i, lbl in zip([d, h, m, s], labels)]
	for start in range(len(dhms)):
		if not dhms[start].startswith('0'):
			break
	for end in range(len(dhms)-1, -1, -1):
		if not dhms[end].startswith('0'):
			break
	return ', '.join(dhms[start:end+1])

def terse_ago(then):
	if not then:
		return "Never"

	now = datetime.datetime.now()
	delta = now - then

	d = delta.days
	h, s = divmod(delta.seconds, 3600)
	m, s = divmod(s, 60)
	labels = ['d', 'h', 'm', 's']
	dhms = ['%s %s' % (i, lbl) for i, lbl in zip([d, h, m, s], labels)]
	for start in range(len(dhms)):
		if not dhms[start].startswith('0'):
			break
	# for end in range(len(dhms)-1, -1, -1):
	# 	if not dhms[end].startswith('0'):
	# 		break
	if d > 0:
		dhms = dhms[:2]
	elif h > 0:
		dhms = dhms[1:3]
	else:
		dhms = dhms[2:]
	return ', '.join(dhms)

def staleness_factor(then):
	if not then:
		return "updating-never"
	now = datetime.datetime.now()
	delta = now - then
	if delta.days <= 14:
		return "updating-current"
	if delta.days <= 45:
		return "updating-stale"
	if delta.days > 700000:
		return "updating-never"
	return "updating-stalled"

def build_name_qs(keys, items):
	return build_qs(keys, items, lambda x: x.name)

def build_qs(keys, items, accessor=lambda x: x):
	if isinstance(keys, str):
		tmp = keys
		keys = [tmp for x in range(len(items))]
	args = list(zip(keys, [accessor(item) for item in items]))
	qs = urllib.parse.urlencode(args)
	return qs

@app.context_processor
def utility_processor():

	return dict(
			getUserId          = getUserId,
			getTlGroupId       = getTlGroupId,
			format_date        = format_date,
			format_js_date     = format_js_date,
			date_now           = date_now,
			terse_ago          = terse_ago,
			ago                = ago,
			staleness_factor   = staleness_factor,
			build_query_string = build_qs,
			build_name_qs      = build_name_qs,
			min                = min,
			max                = max,
			mode_read_only     = app.config['READ_ONLY'],
			mode_read_only_msg = app.config['READ_ONLY_MSG'],
			)
