
from flask import render_template, flash, redirect, url_for, g, request
from app import app
from app.models import Watches
from app.models import Series
from app.models import Releases
from app.models import WikiPage
from sqlalchemy import desc
from app import db
from flask.ext.babel import gettext
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import nullslast

from app.utilities import get_latest_release
from app.utilities import get_latest_releases

from flask import render_template_string
from flask import render_template

from slugify import slugify

def get_wiki(slug):

	row = WikiPage                             \
				.query                         \
				.filter(WikiPage.slug == slug) \
				.scalar()
	return row



@app.route('/wiki/<page_slug>/')
def renderWikiPage(page_slug):

	wiki = get_wiki(page_slug)

	is_edit = request.args.get('edit')

	if is_edit:
		return render_template('/wiki/wiki_edit.html',
							   slug  = page_slug,
							   wiki  = wiki,
							   )
	else:
		return render_template('/wiki/wiki_page.html',
							   slug  = page_slug,
							   wiki  = wiki,
							   )


def render_wiki(type, name):
	if type:
		content_title = "{}: {}".format(type, name)
		link_name = "{}:{}".format(type, name)
	else:
		content_title = "{}".format(name)
		link_name = str(name)

	page_slug     = slugify(link_name, to_lower=True)

	wiki = get_wiki(page_slug)
	content = wiki
	# print("Content = ", content)

	return render_template(
			'/wiki/wiki_panel.html',
			content_title = content_title,
			content       = content,
			link_name     = link_name,
			page_slug     = page_slug,
			)