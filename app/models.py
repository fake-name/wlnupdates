

from hashlib import md5
import re
from app import db
from sqlalchemy.orm import relationship
from flask.ext.bcrypt import generate_password_hash
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy import Table

from citext import CIText
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType

# Some of the metaclass hijinks make pylint confused,
# so disable the warnings for those aspects of things
# pylint: disable=E0213, R0903



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
	__searchable__ = ['genres']
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	weight      = db.Column(db.Float, default=1)
	tag         = db.Column(CIText(), nullable=False, index=True)

class GenresBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	__searchable__ = ['author']
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	genre       = db.Column(CIText(), nullable=False, index=True)


class AuthorBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	__searchable__ = ['illustrators']
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name       = db.Column(CIText(), nullable=False, index=True)


class IllustratorsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	__searchable__ = ['alternatenames']
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name        = db.Column(CIText(), nullable=False, index=True)


class AlternateNamesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	__searchable__ = ['name', 'cleanname']
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name        = db.Column(db.Text(), nullable=False, index=True)
	cleanname   = db.Column(CIText(), nullable=False, index=True)

class TranslatorsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	__searchable__ = ['group_name']
	group_name  = db.Column(db.Text(), nullable=False)
	group_site  = db.Column(db.Text())

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

	@declared_attr
	def lang(cls):
		return db.Column(db.Integer, db.ForeignKey('language.id'))

class LanguageBase(object):
	id              = db.Column(db.Integer, primary_key=True)
	language   = db.Column(CIText(), nullable=False, index=True)

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
	operation      = db.Column(db.Text())


class ModificationInfoMixin(object):

	@declared_attr
	def changetime(cls):
		return db.Column(db.DateTime, nullable=False, index=True)

	@declared_attr
	def changeuser(cls):
		return db.Column(db.Integer, db.ForeignKey('users.id'), index=True)







# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Series(db.Model, SeriesBase, ModificationInfoMixin):
	__tablename__ = 'series'
	__searchable__ = ['title']
	__table_args__ = (
		db.UniqueConstraint('title'),
		)
	tags           = relationship("Tags")
	genres         = relationship("Genres")
	author         = relationship("Author")
	illustrators   = relationship("Illustrators")
	alternatenames = relationship("AlternateNames")


class Tags(db.Model, TagsBase, ModificationInfoMixin):
	__tablename__ = 'tags'

	__table_args__ = (
		db.UniqueConstraint('series', 'tag'),
		)

class Genres(db.Model, GenresBase, ModificationInfoMixin):
	__tablename__ = 'genres'


	__table_args__ = (
		db.UniqueConstraint('series', 'genre'),
		)

class Author(db.Model, AuthorBase, ModificationInfoMixin):
	__tablename__ = 'author'


	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class Illustrators(db.Model, IllustratorsBase, ModificationInfoMixin):
	__tablename__ = 'illustrators'


	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class AlternateNames(db.Model, AlternateNamesBase, ModificationInfoMixin):
	__tablename__ = 'alternatenames'



class Translators(db.Model, TranslatorsBase, ModificationInfoMixin):
	__tablename__ = 'translators'

	__table_args__ = (
		db.UniqueConstraint('group_name'),
		)

class Releases(db.Model, ReleasesBase, ModificationInfoMixin):
	__tablename__ = 'releases'

class Language(db.Model, LanguageBase, ModificationInfoMixin):
	__tablename__ = 'language'
	__table_args__ = (
		db.UniqueConstraint('language'),
		)

class Covers(db.Model, CoversBase, ModificationInfoMixin):
	__tablename__ = 'covers'



class SeriesChanges(db.Model, SeriesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "serieschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('series.id'), index=True)

class TagsChanges(db.Model, TagsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "tagschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('tags.id'), index=True)

class GenresChanges(db.Model, GenresBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "genreschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('genres.id'), index=True)

class AuthorChanges(db.Model, AuthorBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "authorchanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('author.id'), index=True)

class IllustratorsChanges(db.Model, IllustratorsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "illustratorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('illustrators.id'), index=True)

class TranslatorsChanges(db.Model, TranslatorsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "translatorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('translators.id'), index=True)

class ReleasesChanges(db.Model, ReleasesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "releaseschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('releases.id'), index=True)

class CoversChanges(db.Model, CoversBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "coverschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('covers.id'), index=True)

class AlternateNamesChanges(db.Model, AlternateNamesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "alternatenameschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('alternatenames.id'), index=True)

class LanguageChanges(db.Model, LanguageBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "languagechanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('language.id'), index=True)


def create_trigger(cls):
	# get called after mappings are completed
	# http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html#declare-last
	if cls.__tablename__.endswith("changes"):
		print("Not creating triggers on chagetable {name}.".format(name=cls.__tablename__))
		return

	print("Checking triggers exist on table {name}.".format(name=cls.__tablename__))

	# So this is fairly complex. We know that all the local colums (excepting "id") are
	# present in the changes table, however we can't simply say `INSERT INTO changes VALUES SELECT OLD.*`, because
	# we're adding some more cols, and I don't know if I trust any assumptions I make about the ordering anyways.

	colNames = []
	for column in cls.__table__.columns:
		if column.description != "id":
			colNames.append(column.description)

	# id -> srccol, so the backlink works.
	intoCols = ", ".join(colNames+['srccol', 'operation'])
	oldFromCols = ", ".join(["OLD."+item for item in colNames+['id', ]])
	newFromCols = ", ".join(["NEW."+item for item in colNames+['id', ]])


	rawTrigger = """
		CREATE OR REPLACE FUNCTION {name}_update_func() RETURNS TRIGGER AS ${name}changes$
			BEGIN
				--
				-- Create a row in {name}changes to reflect the operation performed on emp,
				-- make use of the special variable TG_OP to work out the operation.
				--
				IF (TG_OP = 'DELETE') THEN
					INSERT INTO {name}changes ({intoCols}) SELECT {oldFromCols}, 'D';
					RETURN OLD;
				ELSIF (TG_OP = 'UPDATE') THEN
					INSERT INTO {name}changes ({intoCols}) SELECT {oldFromCols}, 'U';
					RETURN OLD;
				ELSIF (TG_OP = 'INSERT') THEN
					INSERT INTO {name}changes ({intoCols}) SELECT {newFromCols}, 'I';
					RETURN NEW;
				END IF;
				RETURN NULL; -- result is ignored since this is an AFTER trigger
			END;
		${name}changes$ LANGUAGE plpgsql;

		DROP TRIGGER IF EXISTS {name}_change_trigger ON {name};
		CREATE TRIGGER {name}_change_trigger
		AFTER INSERT OR UPDATE OR DELETE ON {name}
			FOR EACH ROW EXECUTE PROCEDURE {name}_update_func();

		""".format(
				name        = cls.__tablename__,
				intoCols    = intoCols,
				oldFromCols = oldFromCols,
				newFromCols = newFromCols
				)
	db.engine.execute(
		DDL(
			rawTrigger
		)
	)
	# print(rawTrigger)

trigger_on = [
	Series,
	Tags,
	Genres,
	Author,
	Illustrators,
	AlternateNames,
	Translators,
	Releases,
	Language,
	Covers,
]

def install_triggers():
	print("Installing triggers!")
	for classDefinition in trigger_on:
		create_trigger(classDefinition)

def install_tsvector_indices():
	import sys, inspect
	classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__ )
	for classname, classtype in classes:
		if hasattr(classtype, "__searchable__"):
			print(classname, classtype)
'''

DELETE FROM "alembic_version";
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
DROP TABLE "users" CASCADE;
DROP TABLE "language" CASCADE;
DROP TABLE "languagechanges" CASCADE;



python db_migrate.py db init &&

python db_migrate.py db migrate && python db_migrate.py db upgrade

'''


# class PostChanges(Post, ChangeCols):
# 	srccol   = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)

################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################

class Post(db.Model):
	__searchable__ = ['body']

	id          = db.Column(db.Integer, primary_key=True)
	body        = db.Column(db.Text)
	timestamp   = db.Column(db.DateTime)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	seriesTopic = db.Column(db.Integer)


	def __repr__(self):  # pragma: no cover
		return '<Post %r>' % (self.body)

class Watches(db.Model):


	id          = db.Column(db.Integer, primary_key=True)
	body        = db.Column(db.Text)
	timestamp   = db.Column(db.DateTime)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	seriesTopic = db.Column(db.Integer)


	def __repr__(self):  # pragma: no cover
		return '<Post %r>' % (self.body)




class Users(db.Model):
	id        = db.Column(db.Integer, primary_key=True)
	nickname  = db.Column(db.String,  index=True, unique=True)
	password  = db.Column(db.String,  index=True, unique=True)
	email     = db.Column(db.String,  index=True, unique=True)
	verified  = db.Column(db.Integer, nullable=False)

	last_seen = db.Column(db.DateTime)

	posts     = db.relationship('Post')
	# posts     = db.relationship('Post', backref='author', lazy='dynamic')


	@staticmethod
	def make_valid_nickname(nickname):
		return re.sub(r'[^a-zA-Z0-9_\.]', '', nickname)

	@staticmethod
	def make_unique_nickname(nickname):
		if Users.query.filter_by(nickname=nickname).first() is None:
			return nickname
		version = 2
		while True:
			new_nickname = nickname + str(version)
			if Users.query.filter_by(nickname=new_nickname).first() is None:
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


	def __repr__(self):  # pragma: no cover
		return '<User %r>' % (self.nickname)

	def __init__(self, nickname, email, password, verified):
		self.nickname  = nickname
		self.email     = email
		self.password  = generate_password_hash(password)
		self.verified  = verified
