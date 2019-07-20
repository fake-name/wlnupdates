
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask import g
from flask import flash
from flask_babel import gettext
from flask_security import current_user
from flask_security import login_required

from app import db
from app import app
from forum.models import Board
from forum.models import Thread
from forum.models import Post

from app.models import Users
from app.models import TagsLink
from app.models import TagsLinkChanges
from app.models import Series
from app.models import WikiPage
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
from app.models import Translators
from app.models import Publishers
from app.models import Releases
from app.models import Language
from app.models import Covers


from . import forms

GET_POST = ['GET', 'POST']

bp = Blueprint('forum', __name__)


@bp.route('/')
def index():
	boards = Board.query.all()
	return render_template('forum/index.html', boards=boards)


@bp.route('/<slug>/')
def board(slug):
	try:
		board = Board.query.filter(Board.slug == slug).one()
		threads = Thread.query.filter(Thread.board_id == board.id) \
						.order_by(Thread.updated.desc()).all()
	except SQLAlchemyError:
		return redirect(url_for('.index'))

	return render_template('forum/board.html', board=board,
						   threads=threads)


@bp.route('/<slug>/<int:id>')
@bp.route('/<slug>/<int:id>-<title>')
def thread(slug, id, title=None):
	try:
		board = Board.query.filter(Board.slug == slug).one()
	except SQLAlchemyError:
		return redirect(url_for('.index'))

	try:
		thread = Thread.query.filter(Thread.id == id).one()
	except SQLAlchemyError:
		return redirect(url_for('.board', slug=slug))

	return render_template('forum/thread.html', board=board, thread=thread,
						   posts=thread.posts)


@bp.route('/users/<int:id>')
def user(id):
	try:
		user = Users.query.filter(Users.id == id).one()
	except SQLAlchemyError:
		return redirect(url_for('.index'))

	return render_template('forum/user.html', user=user)


@bp.route('/<slug>/create/', methods=GET_POST)
@login_required
def create_thread(slug):

	if not g.user.is_authenticated():
		flash(gettext('You need to log in to post in the forums.'))
		return redirect(url_for('index'))

	try:
		board = Board.query.filter(Board.slug == slug).one()
	except SQLAlchemyError:
		return redirect(url_for('.index'))

	pcnt,  = db.session.query(func.count(Post.id)).filter(Post.author_id == g.user.id).one()

	form = forms.CreateThreadForm()
	if form.validate_on_submit():
		tname = form.name.data
		if pcnt == 0:
			if len(tname.strip().split(" ")) == 1:
				flash(gettext("Your account has been deleted due to failure to follow instructions about post titles!"
					'Try not behaving like a spammer (or failing to read) next time.'))
				delete_id_internal(g.user.id)
				return redirect(url_for('index'))

		t = Thread( name=tname, board=board, author=current_user)
		db.session.add(t)
		db.session.flush()

		p = Post(content=form.content.data, author=current_user)
		t.posts.append(p)
		db.session.commit()

		return redirect(url_for('.board', slug=slug))

	if pcnt == 0:

		flash(gettext('This seems to be your first post. <br>'
			'<strong><font size="+2">Your first thread MUST have more then one word in it\'s thread title.</font></strong>'
			'<br>If you do not have more then one word in the thread title, your account will be immediately deleted!'
			'<br>Unfortunately, this is a required anti-spam measure.'))

	return render_template('forum/create_thread.html',
							board=board,
							form=form)


@bp.route('/<slug>/<int:id>/create', methods=GET_POST)
@login_required
def create_post(slug, id):

	if not g.user.is_authenticated():
		flash(gettext('You need to log in to post in the forums.'))
		return redirect(url_for('index'))

	try:
		board = Board.query.filter(Board.slug == slug).one()
	except SQLAlchemyError:
		return redirect(url_for('.index'))
	try:
		thread = Thread.query.filter(Thread.id == id).one()
	except SQLAlchemyError:
		return redirect(url_for('.board', slug=slug))

	form = forms.CreatePostForm()
	if form.validate_on_submit():
		p = Post(content=form.content.data, author=current_user)
		thread.posts.append(p)
		db.session.flush()
		thread.updated = p.created
		db.session.commit()

		return redirect(url_for('.thread', slug=slug, id=id))

	return render_template('forum/create_post.html',
						board=board,
						thread=thread,
						form=form)


@bp.route('/<slug>/<int:thread_id>/<int:post_id>/edit', methods=GET_POST)
@login_required
def edit_post(slug, thread_id, post_id):

	if not g.user.is_authenticated():
		flash(gettext('You need to log in to post in the forums.'))
		return redirect(url_for('index'))

	try:
		board = Board.query.filter(Board.slug == slug).one()
	except SQLAlchemyError:
		return redirect(url_for('.index'))
	try:
		thread = Thread.query.filter(Thread.id == thread_id).one()
	except SQLAlchemyError:
		return redirect(url_for('.board', slug=slug))

	thread_redirect = redirect(url_for('.thread', slug=slug, id=thread_id))
	try:
		post = Post.query.filter(Post.id == post_id).one()
	except SQLAlchemyError:
		return thread_redirect
	if post.author_id != current_user.id:
		return thread_redirect

	form = forms.EditPostForm()
	if form.validate_on_submit():
		post.content = form.content.data
		db.session.commit()
		return thread_redirect
	else:
		form.content.data = post.content

	return render_template('forum/edit_post.html',
						board=board,
						thread=thread,
						form=form,
						edit_post=post)


def delete_id_internal(del_id):
	try:
		user    = Users.query.filter(Users.id == del_id).one()
		threads = Thread.query.filter(Thread.author_id == del_id).all()
		posts   = Post.query.filter(Post.author_id == del_id).all()

		del_items = [
				Post.query.filter(AlternateNames          .changeuser == del_id).all(),
				Post.query.filter(AlternateTranslatorNames.changeuser == del_id).all(),
				Post.query.filter(TagsLink                .changeuser == del_id).all(),
				Post.query.filter(TagsLinkChanges         .changeuser == del_id).all(),
				Post.query.filter(Series                  .changeuser == del_id).all(),
				Post.query.filter(WikiPage                .changeuser == del_id).all(),
				Post.query.filter(Tags                    .changeuser == del_id).all(),
				Post.query.filter(Genres                  .changeuser == del_id).all(),
				Post.query.filter(Author                  .changeuser == del_id).all(),
				Post.query.filter(Illustrators            .changeuser == del_id).all(),
				Post.query.filter(Translators             .changeuser == del_id).all(),
				Post.query.filter(Publishers              .changeuser == del_id).all(),
				Post.query.filter(Releases                .changeuser == del_id).all(),
				Post.query.filter(Language                .changeuser == del_id).all(),
				Post.query.filter(Covers                  .changeuser == del_id).all(),
			]

	except SQLAlchemyError:
		return False

	print("User:", user)

	for itemlist in del_items:
		for item in itemlist:
			db.session.delete(item)

	print("posts:", posts)
	for thread in threads:
		for post in thread.posts:
			db.session.delete(post)
		db.session.delete(thread)
	for post in posts:
		db.session.delete(post)

	for rating in user.ratings:
		db.session.delete(rating)
	for watch in user.watches:
		db.session.delete(watch)

	db.session.delete(user)
	db.session.commit()
	return True

@app.route('/delete_spammer/<int:user_id>', methods=GET_POST)
@login_required
def user_is_spammer(user_id):

	if not g.user.is_admin():
		flash(gettext('You need to be an admin to do that.'))
		return redirect(url_for('index'))

	ok = delete_id_internal(user_id)
	if not ok:
		return redirect(url_for('.index'))


	flash(gettext('User %s deleted' % user_id))
	return redirect(url_for('.index'))
