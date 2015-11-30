
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
import app.nameTools as nt
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from app import app
from app.models import News_Posts

from app import db

@app.route('/news/<int:page>')
@app.route('/news/')
def renderNews(page=1):

	posts = News_Posts                            \
			.query                           \
			.filter(News_Posts.user_id == 2)      \
			.order_by(desc(News_Posts.timestamp)) \
			.paginate(page, 5, False)

	add_new = None
	add_new_text = None
	if g.user.is_admin():
		add_new = "post"
		add_new_text = "New Post"

	return render_template(
			'news.html',
			posts = posts,
			add_new = add_new,
			add_new_text = add_new_text,
		)