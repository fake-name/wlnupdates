
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
import app.nameTools as nt
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from app import app
from app.models import Posts

from app import db

@app.route('/news/<page>/')
@app.route('/news/')
def renderNews(page=1):

	posts = Posts                            \
			.query                           \
			.filter(Posts.user_id == 2)      \
			.order_by(desc(Posts.timestamp)) \
			.paginate(page, 5, False)
	print(posts)
	print(posts.total)
	print(dir(posts))
	return render_template(
			'news.html',
			posts = posts,
		)