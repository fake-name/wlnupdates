from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask.ext.babel import gettext
# from guess_language import guess_language
from app import app
from app import db
import datetime

from app.models import Series
from app.models import Translators
from app.models import AlternateNames
# from app.models import Users
# from app.models import Posts
# from app.models import Tags
# from app.models import Genres
# from app.models import Author
# from app.models import Illustrators
# from app.models import Releases
# from app.models import Covers
# from app.models import Watches
# from app.models import Feeds
# from app.models import Releases
import app.nameTools as nt

from app.forms import NewGroupForm, NewSeriesForm, updateAltNames


def add_group(form):
	name = form.name.data.strip()
	have = Translators.query.filter(Translators.name==name).scalar()
	if have:
		flash(gettext('Group already exists!'))
		return redirect(url_for('renderGroupId', sid=have.id))
	else:
		new = Translators(
			name = name,
			changetime = datetime.datetime.now(),
			changeuser = g.user.id,
			)
		db.session.add(new)
		db.session.commit()
		flash(gettext('Group Created!'))
		return redirect(url_for('renderGroupId', sid=new.id))

def add_series(form):

	name = form.name.data.strip()

	stripped = nt.prepFilenameForMatching(name)
	have = AlternateNames.query.filter(AlternateNames.cleanname==stripped).all()

	if len(have) == 1:
		flash(gettext('Series exists under a different name!'))
		return redirect(url_for('renderSeriesId', sid=have[0].series))

	elif have:
		flash(gettext('Have multiple candidate series that look like that name!'))
		return redirect(url_for('search', title=name))

	else:
		new = Series(
			title      = name,
			changetime = datetime.datetime.now(),
			changeuser = g.user.id,
			)
		db.session.add(new)
		db.session.commit()

		# session must be committed before adding alternate names,
		# or the primary key links will fail.
		updateAltNames(new, [name])

		flash(gettext('Series Created!'))
		# return redirect(url_for('index'))
		return redirect(url_for('renderSeriesId', sid=new.id))


dispatch = {
	'group'  : (NewGroupForm,  add_group),
	'series' : (NewSeriesForm, add_series),
}


@app.route('/add/<add_type>/', methods=('GET', 'POST'))
def addNewItem(add_type):

	if not add_type in dispatch:
		flash(gettext('Unknown type of content to add!.'))
		return redirect(url_for('index'))

	form_class, callee = dispatch[add_type]
	form = form_class()
	have_auth = g.user.is_authenticated()

	if form.validate_on_submit():
		if have_auth:
			return callee(form)
		else:
			flash(gettext('You must be logged in to make changes!'))

	else:
		if not have_auth:
			flash(gettext('You do not appear to be logged in. Any changes you make will not be saved!'))

	return render_template(
			'add.html',
			form=form,
			add_name = add_type
			)
