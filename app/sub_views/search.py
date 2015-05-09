
from flask import render_template, flash, redirect, url_for, g


def execute_search():
	print("Search!")
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return render_template('search_results.html',
					   # sequence_item   = series_entries,
					   # page            = page,
					   name_key        = "title",
					   page_url_prefix = 'series-id',
					   searchTarget    = 'Tags',
					   # searchValue     = tag.tag
					   )