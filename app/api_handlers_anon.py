import datetime
import werkzeug.exceptions
from app import app
from app.api_common import getResponse
from app.api_common import getDataResponse
import app.sub_views.sequence_views as sequence_view_items
import app.sub_views.release_views  as release_view_items
import app.sub_views.series_views   as series_view_items
import app.sub_views.item_views     as item_view_items
import app.sub_views.search         as search_views

def check_validate_range(data):
	if "offset" in data:
		data['offset'] = int(data['offset'])
		assert data['offset'] > 0, "Offset must be greater then 0"
	else:
		data['offset'] = 1
	if "prefix" in data:
		assert isinstance(data['prefix'], str), "Prefix entry must be a string."
		assert data['prefix'].lower() in "abcdefghijklmnopqrstuvwxyz0123456789", "Prefix must be a single letter or number in a string. Allowable characters: 'abcdefghijklmnopqrstuvwxyz0123456789'."
	else:
		data['prefix'] = None

	data['items'] = 50

	return data

def unpack_paginator(paginator):
	ret_data = {
		'items'    : paginator.items,
		'pages'    : paginator.pages,
		'has_next' : paginator.has_next,
		'has_prev' : paginator.has_prev,
		'per_page' : paginator.per_page,
		'prev_num' : paginator.prev_num,
		'next_num' : paginator.next_num,
		'total'    : paginator.total,
	}
	return ret_data

def is_integer(in_str):
	try:
		int(in_str)
		return True
	except ValueError:
		return False

############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################
def get_artists(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_artist_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'name' : row.name,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)
def get_authors(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_author_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'name' : row.name,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)
def get_genres(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_genre_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'name' : row.genre,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)
def get_groups(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_groups_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'name' : row.name,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)
def get_publishers(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_publisher_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'name' : row.name,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)
def get_tags(data):
	data = check_validate_range(data)
	seq = sequence_view_items.get_tag_entries(data['prefix'], data['offset'])
	tmp = unpack_paginator(seq)
	rows = tmp['items']
	tmp['items'] = [{
		'tag' : row.tag,
		'id'   : row.id,
	} for row in rows]
	return getDataResponse(tmp)

############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################

def unpack_releases(release_items):
	release_items = [{
		'series'    : {
				"name" : row.series_row.title,
				"id"   : row.series_row.id,
			},
		'published' : row.published,
		'volume'    : row.volume,
		'chapter'   : row.chapter,
		'fragment'  : None,
		'postfix'   : row.postfix,
		'srcurl'    : row.srcurl,
		'tlgroup'   : {
				"name" : row.translators.name,
				"id"   : row.translators.id,
			},

	} for row in release_items]

	return release_items
def get_oel_releases(data):
	data = check_validate_range(data)
	releases = release_view_items.get_releases(page = data['offset'])
	tmp = unpack_paginator(releases)

	tmp['items'] = unpack_releases(tmp['items'])
	return getDataResponse(tmp)
def get_releases(data):
	data = check_validate_range(data)
	releases = release_view_items.get_releases(page = data['offset'], srctype='oel')
	tmp = unpack_paginator(releases)

	tmp['items'] = unpack_releases(tmp['items'])
	return getDataResponse(tmp)
def get_translated_releases(data):
	data = check_validate_range(data)
	releases = release_view_items.get_releases(page = data['offset'], srctype='translated')
	tmp = unpack_paginator(releases)

	tmp['items'] = unpack_releases(tmp['items'])
	return getDataResponse(tmp)

############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################


def unpack_series(release_items):
	# Sequence views only get the id and title.
	release_items = [{

		'id'          : row.id,
		'title'       : row.title,
		'type'        : row.type,

	} for row in release_items]

	return release_items
def get_oel_series(data):
	data = check_validate_range(data)
	seq = series_view_items.getSeries(letter=data['prefix'], page=data['offset'], type='oel')
	tmp = unpack_paginator(seq)
	tmp['items'] = unpack_series(tmp['items'])
	return getDataResponse(tmp)

def get_series(data):
	data = check_validate_range(data)
	seq = series_view_items.getSeries(letter=data['prefix'], page=data['offset'])
	tmp = unpack_paginator(seq)
	tmp['items'] = unpack_series(tmp['items'])
	return getDataResponse(tmp)

def get_translated_series(data):
	data = check_validate_range(data)
	seq = series_view_items.getSeries(letter=data['prefix'], page=data['offset'], type='translated')
	tmp = unpack_paginator(seq)
	tmp['items'] = unpack_series(tmp['items'])
	return getDataResponse(tmp)


############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################

def unpack_series_page(row):
	# This is rather inelegant.

	# Primary attributes
	# 	id
	# 	title
	# 	description
	# 	type
	# 	origin_loc
	# 	demographic
	# 	orig_lang
	# 	website
	# 	volume
	# 	chapter
	# 	orig_status
	# 	tot_volume
	# 	tot_chapter
	# 	region
	# 	tl_type
	# 	license_en
	# 	pub_date

	# Links:
	# 	tags
	# 	genres
	# 	author
	# 	illustrators
	# 	alternatenames
	# 	covers
	# 	releases
	# 	publishers

	ret = {

		'id'          : row.id,
		'title'       : row.title,
		'description' : row.description,
		'type'        : row.type,
		'origin_loc'  : row.origin_loc,
		'demographic' : row.demographic,
		'orig_lang'   : row.orig_lang,
		'website'     : row.website,
		'orig_status' : row.orig_status,
		'region'      : row.region,
		'tl_type'     : row.tl_type,
		'license_en'  : row.license_en,
		'pub_date'    : row.pub_date,

		'latest_published' : row.latest_published,
		'latest_volume'    : row.latest_volume,
		'latest_chapter'   : row.latest_chapter,
		'latest_fragment'  : row.latest_fragment,
		'rating'           : row.rating,
		'rating_count'     : row.rating_count,

		'tags'           : [
			{
				'id'  : tag.id,
				'tag' : tag.tag,
			}
			for tag in row.tags
		],

		'genres'           : [
			{
				'id'    : genre.id,
				'genre' : genre.genre,
			}
			for genre in row.genres
		],

		'authors'           : [
			{
				'id'     : author.id,
				'author' : author.name,
			}
			for author in row.author
		],

		'illustrators'           : [
			{
				'id'           : illustrators.id,
				'illustrators' : illustrators.name,
			}
			for illustrators in row.illustrators
		],

		'alternatenames'           : [
			alternatename.name for alternatename in row.alternatenames
		],

		'covers'           : [
			{
				'id'          : cover.id,
				'srcfname'    : cover.srcfname,
				'volume'      : cover.volume,
				'chapter'     : cover.chapter,
				'description' : cover.description,
				'url'         : 'https://www.wlnupdates.com/cover-img/{}'.format(cover.id)
			}
			for cover in row.covers
		],

		'publishers'           : [
			{
				'id'        : publisher.id,
				'publisher' : publisher.name,
			}
			for publisher in row.publishers
		],

		# Hurrah for function reuse
		'releases'           : unpack_releases(row.releases)

	}

	return ret
def get_series_id(data):
	assert "id" in data, "You must specify a id to query for."

	series, releases, watch, watchlists, progress, latest, latest_dict, most_recent, latest_str, rating, total_watches, similar_series = item_view_items.load_series_data(data['id'])


	ret                  = unpack_series_page(series)
	ret['releases']      = unpack_releases(releases)
	ret['watch']         = watch
	ret['watchlists']    = watchlists
	ret['progress']      = progress
	ret['latest']        = latest_dict
	ret['most_recent']   = most_recent
	ret['latest_str']    = latest_str
	ret['rating']        = rating
	ret['total_watches'] = total_watches
	ret['similar_series'] = [
			{
				'id'        : sid,
				'title' : sname,
			}
			for sname, sid in similar_series
		]

	return getDataResponse(ret)



############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################


def unpack_artist_or_illustrator(row_item, series):
	ret = {
		"name" : row_item.name,
		"series" : [
						{
							"title" : series_row.title,
							"id"   : series_row.id
						}
						for
							series_row
						in
							series.all()
					],
	}

	return ret

def unpack_tag_genre_publisher(row_item, series):

	row_keys = row_item.__table__.columns.keys()

	if "tag" in row_keys:
		name = "tag"
		val  = row_item.tag

	if "genre" in row_keys:
		name = "genre"
		val  = row_item.genre
	if "name" in row_keys:
		name = "name"
		val  = row_item.name

	ret = {
		name     : val,
		"series" : [
						{
							"title" : series_row.title,
							"id"   : series_row.id
						}
						for
							series_row
						in
							series.all()
					],
	}
	if "site" in row_keys:
		ret['site'] = row_item.site

	return ret

def get_artist_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	a_id = int(data['id'])
	artist, series = item_view_items.get_artist(a_id)
	if not artist:
		return getResponse(error=True, message='No item found for that ID!')
	data = unpack_artist_or_illustrator(artist, series)
	return getDataResponse(data)

def get_author_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	a_id = int(data['id'])
	author, series = item_view_items.get_author(a_id)
	if not author:
		return getResponse(error=True, message='No item found for that ID!')
	data = unpack_artist_or_illustrator(author, series)
	return getDataResponse(data)



def get_genre_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	a_id = int(data['id'])
	tag, series = item_view_items.get_genre_id(a_id)
	if not tag:
		return getResponse(error=True, message='No item found for that ID!')
	data = unpack_tag_genre_publisher(tag, series)
	return getDataResponse(data)

def get_tag_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	a_id = int(data['id'])
	genre, series = item_view_items.get_tag_id(a_id)
	if not genre:
		return getResponse(error=True, message='No item found for that ID!')
	data = unpack_tag_genre_publisher(genre, series)
	return getDataResponse(data)


def get_publisher_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	a_id = int(data['id'])
	pub, series = item_view_items.get_publisher_id(a_id)
	if not pub:
		return getResponse(error=True, message='No item found for that ID!')
	data = unpack_tag_genre_publisher(pub, series)
	return getDataResponse(data)


def get_group_id(data):
	assert "id" in data, "You must specify a id to query for."
	assert is_integer(data['id']), "The 'id' member must be an integer, or a string that can cleanly cast to one."
	if 'page' in data:
		assert is_integer(data['page']), "The 'page' member must be an integer, or a string that can cleanly cast to one if it is present."
	s_id = int(data['id'])
	page = int(data.get('page', '1'))

	group, names, feeds, items_raw, series_items = item_view_items.get_group_id(s_id, page)

	if not group:
		return getResponse(error=True, message="Group with id %s not found!" % s_id)

	try:
		feed_entries = feeds.paginate(page, app.config['SERIES_PER_PAGE'])
	except werkzeug.exceptions.NotFound:
		feed_entries = None
	try:
		release_entries = items_raw.paginate(page, app.config['SERIES_PER_PAGE'])
	except werkzeug.exceptions.NotFound:
		release_entries = None


	feed_tmp = unpack_paginator(feed_entries)
	feed_items = [{
		'title'     : row.title,
		'contents'  : row.contents,
		'guid'      : row.guid,
		'linkurl'   : row.linkurl,
		'published' : row.published,
		'updated'   : row.updated,
		'srcname'   : row.srcname,
		'region'    : row.region,
		'tags'      : [tag.tag for tag in row.tags],
	} for row in feed_tmp['items']]

	release_tmp = unpack_paginator(release_entries)
	release_items = [{
		'published' : row.published,
		'volume'    : row.volume,
		'chapter'   : row.chapter,
		'fragment'  : row.fragment,
		'postfix'   : row.postfix,
		'include'   : row.include,
		'srcurl'    : row.srcurl,

	} for row in release_tmp['items']]


	ret = {
		'group' : group.name,
		'id'    : group.id,
		'site'  : group.site,
		'alternate-names' : names,
		'active-series'   : {
			series.id : series.title
			for series in series_items
		},
		'releases-paginated' : release_items,
		'feed-paginated' : feed_items,
	}

	return getDataResponse(ret)


def get_search_title(data):
	assert "title" in data, "You must specify a title to query for."
	assert isinstance(data['title'], str), "The 'title' member must be a string."
	assert len(data['title']) > 1, "You must specify a non-empty title to query for."

	data, searchtermclean = search_views.title_search(data['title'])

	ret = {
		'cleaned_search' : searchtermclean,
		'results'        : [
			{
				'sid' : sid,
				'match' : [
						(match[3], match[2])
					for
						match in results['results']
					]
			}
			for
				sid, results in data.items()
		],
	}

	return getDataResponse(ret)



def enumerate_search_tags(data):
	tags = search_views.get_tags()
	resp = [(tag.id, tag.tag, tag.tag_instances) for tag in tags]
	return getDataResponse(resp)

def get_search_advanced(data):
	if not search_views.search_check_ok(data):
		return getResponse(error=True, message="Insufficent filter parameters!")
	series_query = search_views.do_advanced_search(data)
	series_query = series_query.limit(100)
	series = series_query.all()

	ret = [
		(tmp[0], tmp[1], tmp[2].timestamp(), tmp[3]) for tmp in series
	]
	return getDataResponse(ret)



def get_watches(data):
	return getResponse(error=True, message="Not yet implemented")

def get_feeds(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")
