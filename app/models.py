

from citext import CIText
from hashlib import md5
import re
from app import db
from app import app
from sqlalchemy.orm import relationship
from flask.ext.bcrypt import generate_password_hash
from sqlalchemy.ext.declarative import declared_attr

followers = db.Table(
	'followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class SeriesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(CIText())
	description = db.Column(db.Text())
	type        = db.Column(db.Text())
	origin_loc  = db.Column(db.Text())
	demographic = db.Column(db.Text())
	orig_lang   = db.Column(db.Text())


class TagsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	weight      = db.Column(db.Float, default=1)
	tag         = db.Column(CIText(), nullable=False, index=True)
	__table_args__ = (
		db.UniqueConstraint('series', 'tag'),
		)

class GenresBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	genre       = db.Column(CIText(), nullable=False, index=True)

	__table_args__ = (
		db.UniqueConstraint('series', 'genre'),
		)

class AuthorBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	author      = db.Column(CIText(), nullable=False, index=True)


class IllustratorsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name        = db.Column(CIText(), nullable=False, index=True)

	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class AlternateNamesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name        = db.Column(db.Text(), nullable=False, index=True)
	cleanname   = db.Column(CIText(), nullable=False, index=True)

class TranslatorsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	group_name  = db.Column(db.Text(), nullable=False)
	group_site  = db.Column(db.Text())
	__table_args__ = (
		db.UniqueConstraint('group_name'),
		)

class ReleasesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	volume      = db.Column(db.Float(), nullable=False)
	chapter     = db.Column(db.Float(), nullable=False)
	@declared_attr
	def tlgroup(cls):
		return db.Column(db.Integer, db.ForeignKey('translators.id'))



class CoversBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	srcfname    = db.Column(db.Text)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	volume      = db.Column(db.Float())
	chapter     = db.Column(db.Float())
	description = db.Column(db.Text)
	fspath      = db.Column(db.Text)
	hash        = db.Column(db.Text, nullable=False)



class ChangeLogMixin(object):
	@declared_attr
	def changetime(cls):
		return db.Column(db.DateTime, nullable=False, index=True)

	@declared_attr
	def changeuser(cls):
		return db.Column(db.Integer, db.ForeignKey('user.id'), index=True)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Series(db.Model, SeriesBase):
	__tablename__ = 'series'
	__table_args__ = (
		db.UniqueConstraint('title'),
		)
	tags           = relationship("tags")
	genres         = relationship("genres")
	author         = relationship("author")
	illustrators   = relationship("illustrators")
	alternatenames = relationship("alternatenames")


class Tags(db.Model, TagsBase):
	__tablename__ = 'tags'
	__table_args__ = (
		db.UniqueConstraint('series', 'tag'),
		)

class Genres(db.Model, GenresBase):
	__tablename__ = 'genres'

	__table_args__ = (
		db.UniqueConstraint('series', 'genre'),
		)

class Author(db.Model, AuthorBase):
	__tablename__ = 'author'

	__table_args__ = (
		db.UniqueConstraint('series', 'author'),
		)

class Illustrators(db.Model, IllustratorsBase):
	__tablename__ = 'illustrators'

	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class AlternateNames(db.Model, AlternateNamesBase):
	__tablename__ = 'alternatenames'


class Translators(db.Model, TranslatorsBase):
	__tablename__ = 'translators'

	__table_args__ = (
		db.UniqueConstraint('group_name'),
		)

class Releases(db.Model, ReleasesBase):
	__tablename__ = 'releases'


class Covers(db.Model, CoversBase):
	__tablename__ = 'covers'



class SeriesChanges(db.Model, SeriesBase, ChangeLogMixin):
	__tablename__ = "serieschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('series.id'), index=True)

class TagsChanges(db.Model, TagsBase, ChangeLogMixin):
	__tablename__ = "tagschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('tags.id'), index=True)

class GenresChanges(db.Model, GenresBase, ChangeLogMixin):
	__tablename__ = "genreschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('genres.id'), index=True)

class AuthorChanges(db.Model, AuthorBase, ChangeLogMixin):
	__tablename__ = "authorchanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('author.id'), index=True)

class IllustratorsChanges(db.Model, IllustratorsBase, ChangeLogMixin):
	__tablename__ = "illustratorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('illustrators.id'), index=True)

class TranslatorsChanges(db.Model, TranslatorsBase, ChangeLogMixin):
	__tablename__ = "translatorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('translators.id'), index=True)

class ReleasesChanges(db.Model, ReleasesBase, ChangeLogMixin):
	__tablename__ = "releaseschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('releases.id'), index=True)

class CoversChanges(db.Model, CoversBase, ChangeLogMixin):
	__tablename__ = "coverschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('covers.id'), index=True)

class AlternateNamesChanges(db.Model, AlternateNamesBase, ChangeLogMixin):
	__tablename__ = "alternatenameschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('alternatenames.id'), index=True)


'''

DROP TABLE "alembic_version" CASCADE;
DROP TABLE "alternatenames" CASCADE;
DROP TABLE "alternatenameschanges" CASCADE;
DROP TABLE "author" CASCADE;
DROP TABLE "authorchanges" CASCADE;
DROP TABLE "covers" CASCADE;
DROP TABLE "coverschanges" CASCADE;
DROP TABLE "followers" CASCADE;
DROP TABLE "genres" CASCADE;
DROP TABLE "genreschanges" CASCADE;
DROP TABLE "illustrators" CASCADE;
DROP TABLE "illustratorschanges" CASCADE;
DROP TABLE "post" CASCADE;
DROP TABLE "releases" CASCADE;
DROP TABLE "releaseschanges" CASCADE;
DROP TABLE "series" CASCADE;
DROP TABLE "serieschanges" CASCADE;
DROP TABLE "tags" CASCADE;
DROP TABLE "tagschanges" CASCADE;
DROP TABLE "translators" CASCADE;
DROP TABLE "translatorschanges" CASCADE;
DROP TABLE "user" CASCADE;

'''


# class PostChanges(Post, ChangeCols):
# 	srccol   = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)



class Post(db.Model):
	__searchable__ = ['body']

	id          = db.Column(db.Integer, primary_key=True)
	body        = db.Column(db.Text)
	timestamp   = db.Column(db.DateTime)
	user_id     = db.Column(db.Integer, db.ForeignKey('user.id'))

	seriesTopic = db.Column(db.Integer)


	def __repr__(self):  # pragma: no cover
		return '<Post %r>' % (self.body)




class User(db.Model):
	id        = db.Column(db.Integer, primary_key=True)
	nickname  = db.Column(db.String,  index=True, unique=True)
	password  = db.Column(db.String,  index=True, unique=True)
	email     = db.Column(db.String,  index=True, unique=True)
	verified  = db.Column(db.Integer, nullable=False)

	last_seen = db.Column(db.DateTime)

	posts     = db.relationship('Post', backref='author', lazy='dynamic')
	followed  = db.relationship('User',
							   secondary=followers,
							   primaryjoin=(followers.c.follower_id == id),
							   secondaryjoin=(followers.c.followed_id == id),
							   backref=db.backref('followers', lazy='dynamic'),
							   lazy='dynamic')

	@staticmethod
	def make_valid_nickname(nickname):
		return re.sub(r'[^a-zA-Z0-9_\.]', '', nickname)

	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname=nickname).first() is None:
			return nickname
		version = 2
		while True:
			new_nickname = nickname + str(version)
			if User.query.filter_by(nickname=new_nickname).first() is None:
				break
			version += 1
		return new_nickname

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return str(self.id)  # python 3

	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
			(md5(self.email.encode('utf-8')).hexdigest(), size)

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(
			followers.c.followed_id == user.id).count() > 0

	def followed_posts(self):
		return Post.query.join(
			followers, (followers.c.followed_id == Post.user_id)).filter(
				followers.c.follower_id == self.id).order_by(
					Post.timestamp.desc())

	def __repr__(self):  # pragma: no cover
		return '<User %r>' % (self.nickname)

	def __init__(self, nickname, email, password, verified):
		self.nickname  = nickname
		self.email     = email
		self.password  = generate_password_hash(password)
		self.verified  = verified
