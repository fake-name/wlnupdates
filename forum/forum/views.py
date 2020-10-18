
import traceback

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


from app.models import SeriesChanges
from app.models import WikiChanges
from app.models import TagsChanges
from app.models import GenresChanges
from app.models import AuthorChanges
from app.models import IllustratorsChanges
from app.models import TranslatorsChanges
from app.models import ReleasesChanges
from app.models import CoversChanges
from app.models import AlternateNamesChanges
from app.models import PublishersChanges
from app.models import AlternateTranslatorNamesChanges
from app.models import LanguageChanges

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

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))

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
				print("Deleting user %s (%s) because they had a single-word thread name on their first post." % (
					g.user.id, g.user.nickname))
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

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))

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

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))

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


def delete_all_altnames(series_obj):
	'''
	Handle cases where the name cleanup system has added altnames that
	have a different change user then the spammer.
	'''
	badlists = [
			AlternateNames       .query.filter(AlternateNames       .series == series_obj.id).all(),
			AlternateNamesChanges.query.filter(AlternateNamesChanges.series == series_obj.id).all(),
			Covers               .query.filter(Covers               .series == series_obj.id).all(),
			CoversChanges        .query.filter(CoversChanges        .series == series_obj.id).all(),
			Releases             .query.filter(Releases             .series == series_obj.id).all(),
			ReleasesChanges      .query.filter(ReleasesChanges      .series == series_obj.id).all(),
		]

	for badlist in badlists:
		for bad in badlist:
			db.session.delete(bad)
			db.session.commit()

def delete_translator(translator):

	badlists = [
			Releases                       .query.filter(Releases                       .tlgroup == translator.id).all(),
			AlternateTranslatorNames       .query.filter(AlternateTranslatorNames       .group == translator.id).all(),
			AlternateTranslatorNamesChanges.query.filter(AlternateTranslatorNamesChanges.group == translator.id).all(),
		]

	for badlist in badlists:
		for bad in badlist:
			db.session.delete(bad)
			db.session.commit()

	db.session.delete(translator)


def delete_id_internal(del_id):

	user    = Users .query.filter(Users.id         == del_id).one()
	threads = Thread.query.filter(Thread.author_id == del_id).all()
	posts   = Post  .query.filter(Post.author_id   == del_id).all()

	print("Delete id internal for user %s (%s)" % (user.id, user.nickname, ))
	traceback.print_stack()

	# Delete dependent series and their properties first
	for spam_series in Series.query.filter(Series.changeuser == del_id).all():
		flash("Spam series: %s -> %s deleted" % (spam_series, spam_series.title))
		print("Spam series:", spam_series, spam_series.title)
		delete_all_altnames(spam_series)

	db.session.commit()

	for spam_tl in Translators.query.filter(Translators.changeuser == del_id).all():
		delete_translator(spam_tl)
	db.session.commit()

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

	for x in range(3):
		SeriesChanges                  .query.filter(SeriesChanges                  .changeuser == del_id).delete()
		db.session.commit()
		AlternateNamesChanges          .query.filter(AlternateNamesChanges          .changeuser == del_id).delete()
		db.session.commit()
		AlternateTranslatorNamesChanges.query.filter(AlternateTranslatorNamesChanges.changeuser == del_id).delete()
		db.session.commit()
		TagsLinkChanges                .query.filter(TagsLinkChanges                .changeuser == del_id).delete()
		db.session.commit()
		GenresChanges                  .query.filter(GenresChanges                  .changeuser == del_id).delete()
		db.session.commit()
		AuthorChanges                  .query.filter(AuthorChanges                  .changeuser == del_id).delete()
		db.session.commit()
		IllustratorsChanges            .query.filter(IllustratorsChanges            .changeuser == del_id).delete()
		db.session.commit()
		TranslatorsChanges             .query.filter(TranslatorsChanges             .changeuser == del_id).delete()
		db.session.commit()
		PublishersChanges              .query.filter(PublishersChanges              .changeuser == del_id).delete()
		db.session.commit()
		ReleasesChanges                .query.filter(ReleasesChanges                .changeuser == del_id).delete()
		db.session.commit()
		LanguageChanges                .query.filter(LanguageChanges                .changeuser == del_id).delete()
		db.session.commit()
		CoversChanges                  .query.filter(CoversChanges                  .changeuser == del_id).delete()
		db.session.commit()
		SeriesChanges                  .query.filter(SeriesChanges                  .changeuser == del_id).delete()
		db.session.commit()
		AlternateNames                 .query.filter(AlternateNames                 .changeuser == del_id).delete()
		db.session.commit()
		AlternateNamesChanges          .query.filter(AlternateNamesChanges          .changeuser == del_id).delete()
		db.session.commit()
		AlternateTranslatorNames       .query.filter(AlternateTranslatorNames       .changeuser == del_id).delete()
		db.session.commit()
		AlternateTranslatorNamesChanges.query.filter(AlternateTranslatorNamesChanges.changeuser == del_id).delete()
		db.session.commit()
		TagsLink                       .query.filter(TagsLink                       .changeuser == del_id).delete()
		db.session.commit()
		WikiPage                       .query.filter(WikiPage                       .changeuser == del_id).delete()
		db.session.commit()
		WikiChanges                    .query.filter(WikiChanges                    .changeuser == del_id).delete()
		db.session.commit()
		Tags                           .query.filter(Tags                           .changeuser == del_id).delete()
		db.session.commit()
		TagsChanges                    .query.filter(TagsChanges                    .changeuser == del_id).delete()
		db.session.commit()
		TagsLinkChanges                .query.filter(TagsLinkChanges                .changeuser == del_id).delete()
		db.session.commit()
		Genres                         .query.filter(Genres                         .changeuser == del_id).delete()
		db.session.commit()
		GenresChanges                  .query.filter(GenresChanges                  .changeuser == del_id).delete()
		db.session.commit()
		Author                         .query.filter(Author                         .changeuser == del_id).delete()
		db.session.commit()
		AuthorChanges                  .query.filter(AuthorChanges                  .changeuser == del_id).delete()
		db.session.commit()
		Illustrators                   .query.filter(Illustrators                   .changeuser == del_id).delete()
		db.session.commit()
		IllustratorsChanges            .query.filter(IllustratorsChanges            .changeuser == del_id).delete()
		db.session.commit()
		Translators                    .query.filter(Translators                    .changeuser == del_id).delete()
		db.session.commit()
		TranslatorsChanges             .query.filter(TranslatorsChanges             .changeuser == del_id).delete()
		db.session.commit()
		Publishers                     .query.filter(Publishers                     .changeuser == del_id).delete()
		db.session.commit()
		PublishersChanges              .query.filter(PublishersChanges              .changeuser == del_id).delete()
		db.session.commit()
		Releases                       .query.filter(Releases                       .changeuser == del_id).delete()
		db.session.commit()
		ReleasesChanges                .query.filter(ReleasesChanges                .changeuser == del_id).delete()
		db.session.commit()
		Language                       .query.filter(Language                       .changeuser == del_id).delete()
		db.session.commit()
		LanguageChanges                .query.filter(LanguageChanges                .changeuser == del_id).delete()
		db.session.commit()
		Covers                         .query.filter(Covers                         .changeuser == del_id).delete()
		db.session.commit()
		CoversChanges                  .query.filter(CoversChanges                  .changeuser == del_id).delete()
		db.session.commit()
		Series                         .query.filter(Series                         .changeuser == del_id).delete()
		db.session.commit()
		SeriesChanges                  .query.filter(SeriesChanges                  .changeuser == del_id).delete()
		db.session.commit()



	db.session.commit()
	db.session.delete(user)
	db.session.commit()
	return True


@app.route('/delete_spammer/<int:user_id>', methods=GET_POST)
@login_required
def user_is_spammer(user_id):

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))

	if not g.user.is_admin():
		flash(gettext('You need to be an admin to do that.'))
		return redirect(url_for('index'))

	print("Deleting spammer user ID %s" % (user_id, ))
	ok = delete_id_internal(user_id)
	if not ok:
		return redirect(url_for('.index'))


	flash(gettext('User %s deleted' % user_id))
	return redirect(url_for('.index'))

@app.route('/delete_spam_series/<int:spam_series_id>', methods=GET_POST)
@login_required
def series_is_spam(spam_series_id):

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))


	if not g.user.is_admin():
		flash(gettext('You need to be an admin to do that.'))
		return redirect(url_for('index'))

	print("Deleting spam series ID %s" % (spam_series_id, ))
	clean_item = Series.query.filter(Series.id==spam_series_id).scalar()
	if not clean_item:
		flash(gettext('Series %s not found' % (spam_series_id, )))
		return redirect(url_for('.index'))


	print("Should delete series: ", clean_item, clean_item.title)

	changeuser = clean_item.changeuser
	print("ChangeUser: ", changeuser)

	assert changeuser > 3, "Spam series added by automatic feeder! Not deleting all relations!"

	data = SeriesChanges                                   \
			.query                                 \
			.filter((SeriesChanges.srccol==spam_series_id))                   \
			.all()

	print("Series changes:", data)

	print("Change users:", [tmp.changeuser for tmp in data])
	if not all([tmp.changeuser == changeuser for tmp in data]):
		flash(gettext('More then one user edit item %s. Editing User-IDs %s.' % (spam_series_id, [tmp.changeuser for tmp in data])))
		return redirect(url_for('.'))

	delete_all_altnames(clean_item)
	ok = delete_id_internal(changeuser)
	if not ok:
		flash(gettext('Error deleting series %s and associated user %s deleted' % (spam_series_id, changeuser)))
		return redirect(url_for('.index'))


	flash(gettext('Series %s and associated user %s deleted' % (spam_series_id, changeuser)))
	return redirect(url_for('index'))
