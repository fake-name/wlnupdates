

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
import sqlalchemy.exc
from settings import DATABASE_DB_NAME
from sqlalchemy.dialects.postgresql import ENUM

# Some of the metaclass hijinks make pylint confused,
# so disable the warnings for those aspects of things
# pylint: disable=E0213, R0903

region_enum = ENUM('western', 'eastern', 'unknown', name='region_enum')

class SeriesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(CIText())
	description = db.Column(db.Text())
	type        = db.Column(db.Text())
	origin_loc  = db.Column(db.Text())
	demographic = db.Column(db.Text())
	orig_lang   = db.Column(db.Text())

	volume      = db.Column(db.Float(), default=-1)
	chapter     = db.Column(db.Float(), default=-1)

	region      = db.Column(region_enum, default='unknown')

class TagsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	weight      = db.Column(db.Float, default=1)
	tag         = db.Column(CIText(), nullable=False, index=True)

class GenresBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	genre       = db.Column(CIText(), nullable=False, index=True)


class AuthorBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name       = db.Column(CIText(), nullable=False, index=True)


class IllustratorsBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))
	name        = db.Column(CIText(), nullable=False, index=True)


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

class ReleasesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))

	published   = db.Column(db.DateTime, index=True, nullable=False)

	volume      = db.Column(db.Float(), nullable=False, index=True)
	chapter     = db.Column(db.Float(), nullable=False, index=True)

	# We need to be able to filter the chapters to include in the logic for
	# determining the translation progress, because some annoying people
	# release things massively out of order. As such, we don't want someone
	# translating chapter 200 first to prevent the release of 0 - 199 from
	# showing up as progress.
	# As such, if include is false, the release is just ignored when looking for
	# the furthest chapter.
	include     = db.Column(db.Boolean, nullable=False, index=True, default=False)

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

	__table_args__ = (
		db.UniqueConstraint('title'),
		)
	tags           = relationship("Tags",           backref='Series')
	genres         = relationship("Genres",         backref='Series')
	author         = relationship("Author",         backref='Series')
	illustrators   = relationship("Illustrators",   backref='Series')
	alternatenames = relationship("AlternateNames", backref='Series')
	covers         = relationship("Covers",         backref='Series')




class Tags(db.Model, TagsBase, ModificationInfoMixin):
	__tablename__ = 'tags'
	__searchable__ = ['tag']

	__table_args__ = (
		db.UniqueConstraint('series', 'tag'),
		)

class Genres(db.Model, GenresBase, ModificationInfoMixin):
	__tablename__ = 'genres'
	__searchable__ = ['genre']

	__table_args__ = (
		db.UniqueConstraint('series', 'genre'),
		)

class Author(db.Model, AuthorBase, ModificationInfoMixin):
	__tablename__ = 'author'
	__searchable__ = ['name']

	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class Illustrators(db.Model, IllustratorsBase, ModificationInfoMixin):
	__tablename__ = 'illustrators'
	__searchable__ = ['name']

	__table_args__ = (
		db.UniqueConstraint('series', 'name'),
		)

class AlternateNames(db.Model, AlternateNamesBase, ModificationInfoMixin):
	__tablename__ = 'alternatenames'
	__searchable__ = ['name', 'cleanname']


class Translators(db.Model, TranslatorsBase, ModificationInfoMixin):
	__tablename__ = 'translators'
	__searchable__ = ['group_name']

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
	srccol   = db.Column(db.Integer, db.ForeignKey('series.id', ondelete="SET NULL"), index=True)

class TagsChanges(db.Model, TagsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "tagschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('tags.id', ondelete="SET NULL"), index=True)

class GenresChanges(db.Model, GenresBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "genreschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('genres.id', ondelete="SET NULL"), index=True)

class AuthorChanges(db.Model, AuthorBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "authorchanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('author.id', ondelete="SET NULL"), index=True)

class IllustratorsChanges(db.Model, IllustratorsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "illustratorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('illustrators.id', ondelete="SET NULL"), index=True)

class TranslatorsChanges(db.Model, TranslatorsBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "translatorschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('translators.id', ondelete="SET NULL"), index=True)

class ReleasesChanges(db.Model, ReleasesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "releaseschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('releases.id', ondelete="SET NULL"), index=True)

class CoversChanges(db.Model, CoversBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "coverschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('covers.id', ondelete="SET NULL"), index=True)

class AlternateNamesChanges(db.Model, AlternateNamesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "alternatenameschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('alternatenames.id', ondelete="SET NULL"), index=True)

class LanguageChanges(db.Model, LanguageBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "languagechanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('language.id', ondelete="SET NULL"), index=True)


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

	# The Foreign key is null when we delete
	deleteFromCols = ", ".join(["OLD."+item for item in colNames]+['NULL', ])
	oldFromCols    = ", ".join(["OLD."+item for item in colNames+['id', ]])
	newFromCols    = ", ".join(["NEW."+item for item in colNames+['id', ]])


	rawTrigger = """
		CREATE OR REPLACE FUNCTION {name}_update_func() RETURNS TRIGGER AS ${name}changes$
			BEGIN
				--
				-- Create a row in {name}changes to reflect the operation performed on emp,
				-- make use of the special variable TG_OP to work out the operation.
				--
				IF (TG_OP = 'DELETE') THEN
					INSERT INTO {name}changes ({intoCols}) SELECT {deleteFromCols}, 'D';
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
				name           = cls.__tablename__,
				intoCols       = intoCols,
				deleteFromCols = deleteFromCols,
				oldFromCols    = oldFromCols,
				newFromCols    = newFromCols
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

def install_trigram_indice_on_column(table, column):

	idx_name = '{table}_{column}_trigram_idx'.format(table = table.__tablename__, column = column)
	create_idx_sql = '''
	CREATE INDEX
		{idx_name}
	ON
		{table}
	USING
		gin ({column} gin_trgm_ops)'''.format(idx_name=idx_name, table=table.__tablename__, column=column)

	try:
		db.engine.execute('''SELECT '{schema}.{idx}'::regclass;'''.format(schema='public', idx=idx_name))
		print("Do not need to create index", idx_name)
	except sqlalchemy.exc.ProgrammingError:
		# index doesn't exist, need to create it.
		print("Creating index {idx} on table {tbl}".format(idx=idx_name, tbl=table.__tablename__))
		db.engine.execute(
				DDL(
					create_idx_sql
				)
			)

def install_triggers():
	print("Installing triggers!")
	for classDefinition in trigger_on:
		create_trigger(classDefinition)


def install_enum():
	print("Installing enum type!")
	region_enum.create(bind=db.engine)



def install_trigram_indices():
	import sys, inspect
	classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__ )
	for classname, classtype in classes:
		if hasattr(classtype, "__searchable__") and issubclass(classtype, db.Model):
			for column in classtype.__searchable__:

				install_trigram_indice_on_column(classtype, column)



################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################
################################################################################################################################################################

class Feeds(db.Model):

	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(db.Text, nullable=False)
	contents    = db.Column(db.Text, nullable=False)
	guid        = db.Column(db.Text, unique=True)
	linkurl     = db.Column(db.Text, nullable=False)
	published   = db.Column(db.DateTime, index=True, nullable=False)
	updated     = db.Column(db.DateTime, index=True)

	srcname     = db.Column(db.Text, nullable=False)
	region      = db.Column(region_enum, default='unknown')

	tags        = db.relationship('FeedTags',    backref='Feeds')
	authors     = db.relationship('FeedAuthors', backref='Feeds')

class FeedAuthors(db.Model):
	id          = db.Column(db.Integer, primary_key=True)
	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
	name        = db.Column(CIText(), index=True, nullable=False)

	__table_args__ = (
		db.UniqueConstraint('article_id', 'name'),
		)

class FeedTags(db.Model):
	id          = db.Column(db.Integer, primary_key=True)
	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
	tag         = db.Column(CIText(), index=True, nullable=False)

	__table_args__ = (
		db.UniqueConstraint('article_id', 'tag'),
		)


class Posts(db.Model):
	__searchable__ = ['body']

	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(db.Text)
	body        = db.Column(db.Text)
	timestamp   = db.Column(db.DateTime, index=True)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	seriesTopic = db.Column(db.Integer)


	def __repr__(self):  # pragma: no cover
		return '<Post %r>' % (self.body)


class Watches(db.Model):
	id          = db.Column(db.Integer, primary_key=True)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	series_id   = db.Column(db.Integer, db.ForeignKey('series.id'))
	listname    = db.Column(db.Text, nullable=False, default='', server_default='')


	volume      = db.Column(db.Float(), default=-1)
	chapter     = db.Column(db.Float(), default=-1)

	__table_args__ = (
		db.UniqueConstraint('user_id', 'series_id'),
		)



class Users(db.Model):
	id        = db.Column(db.Integer, primary_key=True)
	nickname  = db.Column(db.String,  index=True, unique=True)
	password  = db.Column(db.String,  index=True, unique=True)
	email     = db.Column(db.String,  index=True, unique=True)
	verified  = db.Column(db.Integer, nullable=False)

	last_seen = db.Column(db.DateTime)

	has_admin = db.Column(db.Boolean, default=False)
	has_mod   = db.Column(db.Boolean, default=False)

	posts     = db.relationship('Posts')
	# posts     = db.relationship('Post', backref='author', lazy='dynamic')


	@staticmethod
	def make_valid_nickname(nickname):
		return re.sub(r'[^a-zA-Z0-9_\.\-]', '', nickname)

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
		return self.verified

	def is_active(self):
		return self.verified

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
