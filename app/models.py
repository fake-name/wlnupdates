

import re
import tqdm
from hashlib import md5
from app import db
from app import app

from sqlalchemy.orm import relationship
from flask_bcrypt import generate_password_hash
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy import Table
from sqlalchemy.orm import joinedload

from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType
import sqlalchemy.exc
import datetime
from settings import DATABASE_DB_NAME
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM
from citext import CIText
from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import PrimaryKeyConstraint

import util.materialized_view_factory

# Some of the metaclass hijinks make pylint confused,
# so disable the warnings for those aspects of things
# pylint: disable=E0213, R0903


class ChangeLogMixin(object):
	@declared_attr
	def operation(cls):
		return db.Column(db.Text())


class ModificationInfoMixin(object):

	@declared_attr
	def changetime(cls):
		return db.Column(db.DateTime, nullable=False, index=True, default=datetime.datetime.utcnow)

	@declared_attr
	def changeuser(cls):
		return db.Column(db.Integer, db.ForeignKey('users.id'), index=True)



###################################################################################################
# New tags stuff:
###################################################################################################


class TagEntries(db.Model):
	__tablename__ = 'db_tag_entries'
	id          = db.Column(db.Integer, primary_key=True)
	tag_str     = db.Column(CIText(), nullable=False, index=True)

	__table_args__ = (
			UniqueConstraint('tag_str'),
		)

class TagsLinkBase(object):

	@declared_attr
	def series_id(cls):
		return Column(Integer, ForeignKey('series.id'),             nullable=False)
	@declared_attr
	def tag_id(cls):
		return Column(Integer, ForeignKey('db_tag_entries.id'),     nullable=False)
	@declared_attr
	def link_weight(cls):
		return Column(Float, nullable=False, default=1)


class TagsLink(db.Model, TagsLinkBase, ModificationInfoMixin):
	__tablename__ = 'db_tags_link'

	__table_args__ = (
			PrimaryKeyConstraint('series_id', 'tag_id'),
			UniqueConstraint('series_id', 'tag_id'),
		)

class TagsLinkChanges(db.Model, TagsLinkBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "db_tags_link_changes"

	srccol   = db.Column(db.Integer, db.ForeignKey('series.id', ondelete="SET NULL"))

	__table_args__ = (
		PrimaryKeyConstraint('series_id', 'tag_id', 'srccol', 'operation', 'changetime', 'changeuser'),
	)



def tag_creator(tag_txt):

	tmp = db.session.query(TagEntries)         \
		.filter(TagEntries.tag_str == tag_txt) \
		.scalar()
	if tmp:
		return tmp

	return TagEntries(tag_str=tag_txt)


###################################################################################################
# Old
###################################################################################################


region_enum      = ENUM('western', 'eastern', 'unknown',             name='region_enum')
tl_type_enum     = ENUM('oel', 'translated',                         name='tl_type_enum')
series_sort_enum = ENUM('parsed_title_order', 'chronological_order', name='series_sort_mode_enum')

class SeriesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(CIText())
	description = db.Column(db.Text())
	type        = db.Column(db.Text())
	origin_loc  = db.Column(db.Text())
	demographic = db.Column(db.Text())
	orig_lang   = db.Column(db.Text())

	website     = db.Column(db.Text())

	orig_status = db.Column(db.Text())

	region      = db.Column(region_enum, default='unknown')
	sort_mode   = db.Column(series_sort_enum, default='parsed_title_order')
	tl_type     = db.Column(tl_type_enum, nullable=False, index=True)
	# tl_complete = db.Column(db.Boolean, nullable=False, default=False)
	license_en  = db.Column(db.Boolean)

	pub_date    = db.Column(db.DateTime)

	latest_published   = db.Column(db.DateTime)

	latest_volume      = db.Column(db.Float())
	latest_chapter     = db.Column(db.Float())
	latest_fragment    = db.Column(db.Float())

	release_count      = db.Column(db.Integer())

	rating             = db.Column(db.Float())
	rating_count       = db.Column(db.Integer())

	__table_args__ = (
		CheckConstraint('''(rating >= 0 and rating <= 10) or rating IS NULL'''),
		)


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
	name        = db.Column(CIText(), nullable=False, index=True)
	cleanname   = db.Column(CIText(), nullable=False, index=True)

class AlternateTranslatorNamesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def group(cls):
		return db.Column(db.Integer, db.ForeignKey('translators.id'))
	name        = db.Column(db.Text(), nullable=False, index=True)
	cleanname   = db.Column(CIText(), nullable=False, index=True)

class TranslatorsBase(object):
	id    = db.Column(db.Integer, primary_key=True)
	name  = db.Column(CIText(), nullable=False)
	site  = db.Column(db.Text())

class PublishersBase(object):
	id    = db.Column(db.Integer, primary_key=True)

	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'))

	name  = db.Column(CIText(), nullable=False)
	site  = db.Column(db.Text())

class ReleasesBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	@declared_attr
	def series(cls):
		return db.Column(db.Integer, db.ForeignKey('series.id'), index=True)

	published   = db.Column(db.DateTime, index=True, nullable=False)

	volume      = db.Column(db.Float(), index=True)
	chapter     = db.Column(db.Float(), index=True)
	fragment    = db.Column(db.Float(), index=True)
	postfix     = db.Column(db.Text())

	# We need to be able to filter the chapters to include in the logic for
	# determining the translation progress, because some annoying people
	# release things massively out of order. As such, we don't want someone
	# translating chapter 200 first to prevent the release of 0 - 199 from
	# showing up as progress.
	# As such, if include is false, the release is just ignored when looking for
	# the furthest chapter.
	include     = db.Column(db.Boolean, nullable=False, index=True, default=False)

	srcurl      = db.Column(db.Text(), index=True)

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
	fragment    = db.Column(db.Float())
	description = db.Column(db.Text)
	fspath      = db.Column(db.Text)
	hash        = db.Column(db.Text, nullable=False)



class WikiBase(object):
	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(CIText())
	slug        = db.Column(CIText())

	content     = db.Column(db.Text())


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Series(db.Model, SeriesBase, ModificationInfoMixin):
	__tablename__ = 'series'

	__table_args__ = (
			UniqueConstraint('title'),
		)
	tags           = relationship("Tags",           backref='Series', order_by="Tags.tag")
	genres         = relationship("Genres",         backref='Series')
	author         = relationship("Author",         backref='Series')
	illustrators   = relationship("Illustrators",   backref='Series')
	alternatenames = relationship("AlternateNames", backref='Series')
	covers         = relationship("Covers",         backref='Series')
	releases       = relationship("Releases",       backref='Series')
	publishers     = relationship("Publishers",     backref='Series')

	@declared_attr
	def tags_rel(cls):
		return relationship('TagEntries', secondary="db_tags_link")

	tags_prox     = association_proxy('tags_rel', 'tag_str', creator=tag_creator)


class WikiPage(db.Model, WikiBase, ModificationInfoMixin):
	__tablename__ = 'wiki_page'

	__searchable__ = ['title']

	__table_args__ = (
			UniqueConstraint('title'),
			UniqueConstraint('slug'),
		)




class Tags(db.Model, TagsBase, ModificationInfoMixin):
	__tablename__ = 'tags'
	__searchable__ = ['tag']

	__table_args__ = (
			UniqueConstraint('series', 'tag'),
		)
	series_row     = relationship("Series",         backref='Tags')

class Genres(db.Model, GenresBase, ModificationInfoMixin):
	__tablename__ = 'genres'
	__searchable__ = ['genre']

	__table_args__ = (
			UniqueConstraint('series', 'genre'),
		)
	series_row     = relationship("Series",         backref='Genres')

class Author(db.Model, AuthorBase, ModificationInfoMixin):
	__tablename__ = 'author'
	__searchable__ = ['name']

	__table_args__ = (
			UniqueConstraint('series', 'name'),
		)

	series_row       = relationship("Series",         backref='Author')

class Illustrators(db.Model, IllustratorsBase, ModificationInfoMixin):
	__tablename__ = 'illustrators'
	__searchable__ = ['name']

	__table_args__ = (
			UniqueConstraint('series', 'name'),
		)
	series_row       = relationship("Series",         backref='Illustrators')

class AlternateNames(db.Model, AlternateNamesBase, ModificationInfoMixin):
	__tablename__ = 'alternatenames'
	__searchable__ = ['name', 'cleanname']

	__table_args__ = (
			UniqueConstraint('series', 'name'),
		)
	series_row       = relationship("Series",         backref='AlternateNames', lazy='joined')


class AlternateTranslatorNames(db.Model, AlternateTranslatorNamesBase, ModificationInfoMixin):
	__tablename__ = 'alternatetranslatornames'
	__searchable__ = ['name', 'cleanname']

	__table_args__ = (
			UniqueConstraint('group', 'name'),
		)
	group_row       = relationship("Translators",         backref='AlternateTranslatorNames')


class Translators(db.Model, TranslatorsBase, ModificationInfoMixin):
	__tablename__ = 'translators'
	__searchable__ = ['name']

	__table_args__ = (
			UniqueConstraint('name'),
		)

	releases        = relationship("Releases",                 backref='Translators')
	alt_names       = relationship("AlternateTranslatorNames", backref='Translators')


class Publishers(db.Model, PublishersBase, ModificationInfoMixin):
	__tablename__ = 'publishers'
	__searchable__ = ['name']

	__table_args__ = (
			UniqueConstraint('series', 'name'),
		)

	series_row     = relationship("Series",         backref='Publisher')

class Releases(db.Model, ReleasesBase, ModificationInfoMixin):
	__tablename__ = 'releases'
	translators      = relationship("Translators",         backref='Releases')
	series_row       = relationship("Series",              backref='Releases')




class Language(db.Model, LanguageBase, ModificationInfoMixin):
	__tablename__ = 'language'
	__table_args__ = (
			UniqueConstraint('language'),
		)

class Covers(db.Model, CoversBase, ModificationInfoMixin):
	__tablename__ = 'covers'


class SeriesChanges(db.Model, SeriesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "serieschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('series.id', ondelete="SET NULL"))

class WikiChanges(db.Model, WikiBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "wiki_pagechanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('wiki_page.id', ondelete="SET NULL"), index=True)

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

class PublishersChanges(db.Model, PublishersBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "publisherschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('publishers.id', ondelete="SET NULL"), index=True)


class AlternateTranslatorNamesChanges(db.Model, AlternateTranslatorNamesBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "alternatetranslatornameschanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('alternatetranslatornames.id', ondelete="SET NULL"), index=True)

class LanguageChanges(db.Model, LanguageBase, ModificationInfoMixin, ChangeLogMixin):
	__tablename__ = "languagechanges"
	srccol   = db.Column(db.Integer, db.ForeignKey('language.id', ondelete="SET NULL"), index=True)


def create_trigger(cls):
	if cls.__tablename__.endswith("changes"):
		print("Not creating triggers on chagetable {name}.".format(name=cls.__tablename__))
		return

	print("Checking triggers exist on table {name}.".format(name=cls.__tablename__))

	# So this is fairly complex. We know that all the local colums (excepting "id") are
	# present in the changes table, however we can't simply say `INSERT INTO changes VALUES SELECT OLD.*`, because
	# the history table has additional columns, and I don't know if I trust any assumptions I make about the ordering anyways.

	colNames = []
	for column in cls.__table__.columns:
		if column.description != "id":
			colNames.append(column.description)

	# id -> srccol, so the backlink works.
	# The names have to be quoted, because some of them are keywords (ex: "group"), and therefore
	# were producing syntax issues
	intoCols = ", ".join(['"{}"'.format(name) for name in colNames+['srccol', 'operation']])

	# The Foreign key is null when we delete
	deleteFromCols = ", ".join(["OLD."+item for item in colNames]+['NULL', ])

	# Otherwise, mirror the new changes into the log table.
	oldFromCols    = ", ".join(["NEW."+item for item in colNames+['id', ]])
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
	AlternateTranslatorNames,
	Publishers,
	WikiPage,
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

def update_chp_info():

	series = db.engine.execute('''
		SELECT
			 id,
			 title
		FROM series;
		''')

	series = list(series)

	print("Have %s series" % len(series))


	for sid, title in tqdm.tqdm(series):
		releases = db.engine.execute('''
			SELECT
					series,
					published,
					volume,
					chapter,
					fragment,
					include
			FROM releases
			WHERE series = %s
			;
			''', (sid, ))

		releases = list(releases)
		if not releases:
			continue


		most_recent = max([tmp[1] for tmp in releases])
		relinfo = [(
				tmp[2] if tmp[2] is not None else 0,
				tmp[3] if tmp[3] is not None else 0,
				tmp[4] if tmp[4] is not None else 0
			) for tmp in releases if tmp[5]]
		relinfo.sort()
		reltop = max(relinfo)

		res = db.engine.execute('''
			UPDATE
				series
			SET
				latest_published = %s,
				latest_volume    = %s,
				latest_chapter   = %s,
				latest_fragment  = %s
			WHERE
				id = %s;
			''', (
				most_recent,
				reltop[0] if reltop[0] else None,
				reltop[1] if reltop[1] else None,
				reltop[2] if reltop[2] else None,
				sid
				))

	print("")
	print("Committing")
	db.engine.execute("COMMIT")
	print("Done!")

def resynchronize_ratings():
	import app.series_tools as app_series_tools
	ratings = db.engine.execute('''
		SELECT
			distinct(series_id)
		FROM ratings;
		''')

	ratings = list(ratings)

	print("Have %s ratings with ratings" % len(ratings))

	for seriesid, in tqdm.tqdm(ratings):
		with app.app_context():
			app_series_tools.set_rating(seriesid, new_rating=None)


	print("")
	print("Committing")
	db.engine.execute("COMMIT")
	print("Done!")

def resynchronize_latest_counts():
	import app.utilities as app_utilities
	import app.series_tools as app_series_tools
	with app.app_context():
		print("Loading all series")
		all_series = Series.query.all()
		print("Doing updates.")
		done = 0
		for series in tqdm.tqdm(all_series):
			app_utilities.update_latest_row(series)
			done += 1

			if done % 100 == 0:
				db.session.commit()

def install_triggers():
	print("Installing triggers!")
	for classDefinition in trigger_on:
		create_trigger(classDefinition)


def install_region_enum(conn):
	print("Installing region enum type!")
	region_enum.create(bind=conn, checkfirst=True)

def install_tl_type_enum(conn):
	print("Installing tl_type enum type!")
	tl_type_enum.create(bind=conn, checkfirst=True)



def install_trigram_indices():
	import sys, inspect
	classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__ )
	for classname, classtype in classes:
		if hasattr(classtype, "__searchable__") and issubclass(classtype, db.Model):
			for column in classtype.__searchable__:

				install_trigram_indice_on_column(classtype, column)


tags_mv_name = "common_tags_mv"
tags_mv_selectable = db.select(
						[
							db.func.min(Tags.id).label('id'),
							Tags.tag.label('tag'),
							db.func.count(Tags.tag).label('tag_instances'),
						]
					).group_by(Tags.tag)

genre_mv_name = "common_genre_mv"
genre_mv_selectable = db.select(
						[
							db.func.min(Genres.id).label('id'),
							Genres.genre.label('genre'),
							db.func.count(Genres.genre).label('genre_instances'),
						]
					).group_by(Genres.genre)

class CommonTags(util.materialized_view_factory.MaterializedView):
	__table__ = util.materialized_view_factory.create_mat_view(
					tags_mv_name,
					tags_mv_selectable)

class CommonGenres(util.materialized_view_factory.MaterializedView):
	__table__ = util.materialized_view_factory.create_mat_view(
					genre_mv_name,
					genre_mv_selectable)

def refresh_materialized_view():
	print("Trying to refresh materialized views")
	util.materialized_view_factory.refresh_mat_view(tags_mv_name, False)
	util.materialized_view_factory.refresh_mat_view(genre_mv_name, False)
	print("View refreshed.")

def recreate_materialized_view():
	# View not created yet, or changed
	print("Materialized view missing or damaged.")
	db.engine.execute("""DROP MATERIALIZED VIEW IF EXISTS common_tags_mv""", )
	db.engine.execute("""DROP MATERIALIZED VIEW IF EXISTS common_genre_mv""", )
	print("Recreating.")
	t2 = util.materialized_view_factory.CreateMaterializedView(tags_mv_name, tags_mv_selectable)
	db.engine.execute(t2)
	t3 = util.materialized_view_factory.CreateMaterializedView(genre_mv_name, genre_mv_selectable)
	db.engine.execute(t3)


try:
	refresh_materialized_view()
except sqlalchemy.exc.ProgrammingError:
	recreate_materialized_view()


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
			UniqueConstraint('article_id', 'name'),
		)

class FeedTags(db.Model):
	id          = db.Column(db.Integer, primary_key=True)
	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
	tag         = db.Column(CIText(), index=True, nullable=False)

	__table_args__ = (
			UniqueConstraint('article_id', 'tag'),
		)


class News_Posts(db.Model):
	__searchable__ = ['body']

	id          = db.Column(db.Integer, primary_key=True)
	title       = db.Column(db.Text)
	body        = db.Column(db.Text)
	timestamp   = db.Column(db.DateTime, index=True)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	seriesTopic = db.Column(db.Integer)


	def __repr__(self):  # pragma: no cover
		return '<Post %r (body size: %s)>' % (self.title, len(self.body))


class Watches(db.Model):
	id            = db.Column(db.Integer, primary_key=True)
	user_id       = db.Column(db.Integer, db.ForeignKey('users.id'))
	series_id     = db.Column(db.Integer, db.ForeignKey('series.id'))
	listname      = db.Column(db.Text, nullable=False, default='', server_default='')

	watch_as_name = db.Column(db.Text)

	volume        = db.Column(db.Float(), default=-1)
	chapter       = db.Column(db.Float(), default=-1)
	fragment      = db.Column(db.Float(), default=-1)

	__table_args__ = (
			UniqueConstraint('user_id', 'series_id'),
		)

	series_row       = relationship("Series",         backref='Watches')



class Ratings(db.Model):
	id          = db.Column(db.Integer, primary_key=True)
	user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
	series_id   = db.Column(db.Integer, db.ForeignKey('series.id'), index=True)
	source_ip   = db.Column(db.Text, index=True)

	rating      = db.Column(db.Float(), default=-1)

	__table_args__ = (
			UniqueConstraint('user_id', 'source_ip', 'series_id'),
		db.CheckConstraint('rating >=  0', name='rating_min'),
		db.CheckConstraint('rating <= 10', name='rating_max'),
		db.CheckConstraint('''(user_id IS NOT NULL AND source_ip IS NULL) OR (user_id IS NULL AND source_ip IS NOT NULL)''', name='rating_src'),
	)


	series_row       = relationship("Series",         backref='Ratings')


class Users(db.Model):
	id         = db.Column(db.Integer, primary_key=True)
	nickname   = db.Column(CIText(),  index=True, unique=True)
	password   = db.Column(db.String,  index=True, unique=True)
	email      = db.Column(db.String,  index=True, unique=True)
	verified   = db.Column(db.Integer, nullable=False)

	last_seen  = db.Column(db.DateTime)

	has_admin  = db.Column(db.Boolean, default=False)
	has_mod    = db.Column(db.Boolean, default=False)

	news_posts = db.relationship('News_Posts')
	ratings    = db.relationship('Ratings')
	watches    = db.relationship('Watches')
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

	def is_admin(self):
		return self.has_admin

	def is_mod(self):
		return self.has_mod

	def is_anonymous(self):
		return False

	def get_id(self):
		return str(self.id)  # python 3

	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
			(md5(self.email.encode('utf-8')).hexdigest(), size)


	def __repr__(self):  # pragma: no cover
		return '<User -- %r>' % (self.nickname)

	def __init__(self, nickname, email, password, verified):
		self.nickname  = nickname
		self.email     = email
		self.password  = generate_password_hash(password)
		self.verified  = verified

class HttpRequestLog(db.Model):
	id             = db.Column(db.Integer, primary_key=True)
	access_time    = db.Column(db.DateTime, nullable=False, index=True, default=datetime.datetime.utcnow)
	path           = db.Column(db.String)
	user_agent     = db.Column(db.String)
	referer        = db.Column(db.String)
	forwarded_for  = db.Column(db.String)
	originating_ip = db.Column(db.String)
