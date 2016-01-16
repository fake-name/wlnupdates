
from app.api_common import getResponse
from app.api_common import getDataResponse
import app.sub_views.sequence_views as sequence_view_items

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
	return getDataResponse(data=unpack_paginator(seq))

def get_cover_img(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_feeds(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_oel_releases(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_oel_series(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_releases(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_search(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_series(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_translated_releases(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_translated_series(data):
	data = check_validate_range(data)
	return getResponse(error=True, message="Not yet implemented")

def get_watches(data):
	return getResponse(error=True, message="Not yet implemented")




def get_artist_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_author_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_genre_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_group_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_publisher_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_series_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")

def get_tag_id(data):
	assert "id" in data, "You must specify a id to query for."
	return getResponse(error=True, message="Not yet implemented")


