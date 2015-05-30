from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import g
from flask.ext.babel import gettext
from werkzeug.urls import url_fix
# from guess_language import guess_language
from app import app
from app import db
import datetime
import bleach
from sqlalchemy import and_
from app.models import Series
from app.models import Translators
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
from app.models import Releases
import app.nameTools as nt

from app.forms import NewGroupForm, NewSeriesForm, NewReleaseForm
from app.api_handlers import updateAltNames


def add_group(form):
	name = form.name.data.strip()
	have = AlternateTranslatorNames.query.filter(AlternateTranslatorNames.cleanname==nt.prepFilenameForMatching(name)).scalar()
	if have:
		flash(gettext('Group already exists!'))
		return redirect(url_for('renderGroupId', sid=have.group))
	else:
		new = Translators(
			name = name,
			changetime = datetime.datetime.now(),
			changeuser = g.user.id,
			)
		db.session.add(new)
		db.session.commit()
		newname = AlternateTranslatorNames(
				name       = name,
				cleanname  = nt.prepFilenameForMatching(name),
				group      = new.id,
				changetime = datetime.datetime.now(),
				changeuser = g.user.id
			)
		db.session.add(newname)
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

def add_release(form):

	chp = int(form.data['chapter'])   if form.data['chapter']   and int(form.data['chapter'])   >= 0 else None
	vol = int(form.data['volume'])    if form.data['volume']    and int(form.data['volume'])    >= 0 else None
	sid = int(form.data['series_id']) if form.data['series_id'] and int(form.data['series_id']) >= 0 else None
	sub = int(form.data['subChap'])   if form.data['subChap']   and int(form.data['subChap'])   >= 0 else None
	group = int(form.data['group'])

	# Sub-chapters are packed into the chapter value.
	# I /may/ change this
	if sub:
		chp += sub /100

	flt = [(Releases.series == sid)]
	if chp:
		flt.append((Releases.chapter == chp))

	if vol:
		flt.append((Releases.chapter == vol))

	have = Releases.query.filter(and_(*flt)).all()

	itemurl = url_fix(form.data['release_pg'])

	if have:
		flash(gettext('That release appears to already have been added.'))
		return redirect(url_for('renderSeriesId', sid=sid))

	series = Series.query.filter(Series.id==sid).scalar()
	if not series:
		flash(gettext('Invalid series-id in add call? Are you trying something naughty?'))
		return redirect(url_for('index'))

	group = Translators.query.filter(Translators.id==group).scalar()
	if not group:
		flash(gettext('Invalid group-id in add call? Are you trying something naughty?'))
		return redirect(url_for('index'))

	# Everything has validated, add the new item.
	new = Releases(
		tlgroup   = group.id,
		series    = series.id,
		published = datetime.datetime.now(),
		volume    = vol,
		chapter   = chp,
		postfix   = bleach.clean(form.data['postfix'], strip=True),
		srcurl    = itemurl,
		changetime = datetime.datetime.now(),
		changeuser = g.user.id,
		)
	db.session.add(new)
	db.session.commit()
	flash(gettext('New release added. Thanks for contributing!'))
	return redirect(url_for('renderSeriesId', sid=sid))

s_msg = '''
After you have added the series by name, you will be taken to the new
series page where you can fill in the rest of the series information.
'''

def preset(cls):
	return lambda : cls(NewReleaseForm=datetime.datetime.now())

dispatch = {
	'group'   : (NewGroupForm,   add_group,   ''),
	'series'  : (NewSeriesForm,  add_series,  s_msg),
	'release' : (NewReleaseForm, add_release, ''),
}


@app.route('/add/<add_type>/<int:sid>/', methods=('GET', 'POST'))
@app.route('/add/<add_type>/', methods=('GET', 'POST'))
def addNewItem(add_type, sid=None):

	if not add_type in dispatch:
		flash(gettext('Unknown type of content to add!'))
		return redirect(url_for('index'))
	if add_type == 'release' and sid == None:
		flash(gettext('Adding a release must involve a series-id. How did you even do that?'))
		return redirect(url_for('index'))

	form_class, callee, message = dispatch[add_type]
	have_auth = g.user.is_authenticated()

	if add_type == 'release':
		series = Series.query.filter(Series.id==sid).one()

		form = form_class(series_id = series.id)

		altn = AlternateTranslatorNames.query.all()
		altfmt = [(x.group, x.name) for x in altn]
		altfmt.sort(key=lambda x:x[1])
		form.group.choices = altfmt
	else:
		form = form_class()

	if form.validate_on_submit():
		if have_auth:
			print("Validation succeeded!")
			return callee(form)
		else:
			flash(gettext('You must be logged in to make changes!'))

	else:
		if not have_auth:
			flash(gettext('You do not appear to be logged in. Any changes you make will not be saved!'))

	if add_type == 'release':

		altfmt = [(-1, "")] + altfmt
		form.group.choices = altfmt

		if 'Not a valid choice' in form.group.errors:
			form.group.errors.remove('Not a valid choice')

		return render_template(
				'add-release.html',
				form=form,
				add_name = add_type,
				message = message,
				series  = series
				)


	else:
		return render_template(
				'add.html',
				form=form,
				add_name = add_type,
				message = message
				)
