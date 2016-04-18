from flask import render_template
# from guess_language import guess_language
from app import app
from app.models import Tags
from app.models import Genres
from app.models import Author
from app.models import Illustrators
from app.models import Translators
from app.models import Feeds
from app.models import Publishers
from app.models import FeedTags

from app.models import Series
from app.models import Ratings
from app.models import Watches

from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy import func



def get_most_watched(page):

	watches = Watches.query \
		.with_entities(func.count().label("watch_count"), func.min(Watches.series_id).label("series_id")) \
		.group_by(Watches.series_id).subquery()


	have = Series.query.join(watches, Series.id == watches.c.series_id) \
		.add_column(watches.c.watch_count) \
		.order_by(desc(watches.c.watch_count), Series.title)


	watch_entries = have.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return watch_entries



def get_highest_rated(page):

	ratings = Ratings.query \
		.with_entities(func.count().label("rating_count"), func.avg(Ratings.rating).label("rating"), func.min(Ratings.series_id).label("series_id")) \
		.group_by(Ratings.series_id).subquery()


	have = Series.query.join(ratings, Series.id == ratings.c.series_id) \
		.add_column(ratings.c.rating) \
		.add_column(ratings.c.rating_count) \
		.filter(ratings.c.rating_count > 1) \
		.order_by(desc(ratings.c.rating), Series.title)


	watch_entries = have.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return watch_entries



def get_most_rated(page):

	ratings = Ratings.query \
		.with_entities(func.count().label("rating_count"), func.avg(Ratings.rating).label("rating"), func.min(Ratings.series_id).label("series_id")) \
		.group_by(Ratings.series_id).subquery()


	have = Series.query.join(ratings, Series.id == ratings.c.series_id) \
		.add_column(ratings.c.rating) \
		.add_column(ratings.c.rating_count) \
		.filter(ratings.c.rating_count > 1) \
		.order_by(desc(ratings.c.rating_count), Series.title)


	watch_entries = have.paginate(page, app.config['SERIES_PER_PAGE'], False)
	return watch_entries





@app.route('/most-watched/<page>')
@app.route('/most-watched/<int:page>')
@app.route('/most-watched/')
def renderMostWatched(page=1):
	return render_template('popular.html',
						   sequence_item   = get_most_watched(page),
						   page_mode       = "watches",
						   page            = page,
						   title           = 'Most Watched Series',
						   footnote        = None,
						   )






@app.route('/most-rated/<page>')
@app.route('/most-rated/<int:page>')
@app.route('/most-rated/')
def renderMostRated(page=1):
	return render_template('popular.html',
						   sequence_item   = get_most_rated(page),
						   page_mode       = "ratings",
						   page            = page,
						   title           = 'Most Watched Series',
						   footnote        = None,
						   )



@app.route('/highest-rated/<page>')
@app.route('/highest-rated/<int:page>')
@app.route('/highest-rated/')
def renderHighestRated(page=1):

	return render_template('popular.html',
						   sequence_item   = get_highest_rated(page),
						   page_mode       = "ratings",
						   page            = page,
						   title           = 'Highest Rated Series',
						   footnote        = 'Series only rated by one person are excluded from this list.',
						   )

