
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm

def execute_search():
	# Flatten the passed dicts.
	# This means that multiple identical parameters
	# /WILL/ clobber each other in a non-determinsic manner,
	# but that's not needed for search anyways, so I want
	# to disabiguate.
	search = {}
	search.update(dict(request.args.items()))
	search.update(dict(request.form.items()))

	if 'title' in search:
		print("Title search:", search['title'])
	else:
		print("Search params:", search)
	form = SearchForm()
	if not form.validate_on_submit():
		print("Validation failed, redirecting!")
		return redirect(url_for('index'))
	return render_template('search_results.html',
					   # sequence_item   = series_entries,
					   # page            = page,
					   name_key        = "title",
					   page_url_prefix = 'series-id',
					   searchTarget    = 'Tags',
					   # searchValue     = tag.tag
					   )