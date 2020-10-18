
import util.text_tools as text_tools

from flask import render_template
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from flask import g
from flask_babel import gettext
from werkzeug.urls import url_fix
# from guess_language import guess_language
from app import db
import app.utilities as app_utilities
import datetime
import bleach
import markdown
from sqlalchemy import and_
from app.models import Series
from app.models import Translators
from app.models import AlternateNames
from app.models import AlternateTranslatorNames
from app.models import Releases
from app.models import News_Posts
import app.nameTools as nt
from app.forms import NewGroupForm
from app.forms import NewSeriesForm
from app.forms import NewReleaseForm
from app.forms import PostForm
import app.series_tools as series_tools
from app import app
import datetime
from forum.forum.views import delete_id_internal

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

	name = text_tools.fix_string(name, recase=False)


	if "UHB949" in name or "KBR777" in name or "K B R 7 7 7 .COM" in name:
		flash(gettext("Your account has been deleted."
			'Try not behaving like a spammer (or failing to read) next time.'))
		print("Delete id internal from add_series dialog for user %s (%s)" % (g.user.id, g.user.nickname))
		delete_id_internal(g.user.id)
		return redirect(url_for('index'))

	stripped = nt.prepFilenameForMatching(name)
	have = AlternateNames.query.filter(AlternateNames.cleanname==stripped).all()

	rel_type = form.type.data.strip()

	if len(have) == 1:
		flash(gettext('Series exists under a different name!'))
		return redirect(url_for('renderSeriesIdWithoutSlug', sid=have[0].series))

	elif have:
		flash(gettext('Have multiple candidate series that look like that name!'))
		return redirect(url_for('search', title=name))

	else:
		new = Series(
			title      = name,
			tl_type    = rel_type,
			changetime = datetime.datetime.now(),
			changeuser = g.user.id,
			)
		db.session.add(new)
		db.session.commit()

		# session must be committed before adding alternate names,
		# or the primary key links will fail.
		series_tools.updateAltNames(new, [name])

		flash(gettext('Series Created!'))
		# return redirect(url_for('index'))
		return redirect(url_for('renderSeriesIdWithoutSlug', sid=new.id))

def add_release(form):
	chp = int(form.data['chapter'])   if form.data['chapter']   and int(form.data['chapter'])   >= 0 else None
	vol = int(form.data['volume'])    if form.data['volume']    and int(form.data['volume'])    >= 0 else None
	sid = int(form.data['series_id']) if form.data['series_id'] and int(form.data['series_id']) >= 0 else None
	sub = int(form.data['subChap'])   if form.data['subChap']   and int(form.data['subChap'])   >= 0 else None
	group = int(form.data['group'])

	itemurl = url_fix(form.data['release_pg'])

	oel = False
	if form.data['is_oel'] == 'oel':
		oel = True
		group = None

	pubdate = form.data['releasetime']
	postfix = bleach.clean(form.data['postfix'], strip=True) if form.data['postfix'] else ""

	# Limit publication dates to now to prevent post-dating.
	if pubdate > datetime.datetime.now():
		pubdate = datetime.datetime.now()

	# Sub-chapters are packed into the chapter value.
	# I /may/ change this

	assert form.data['is_oel'] in ['oel', 'translated']

	flt = [(Releases.series == sid), (Releases.srcurl == itemurl)]
	if sub:
		flt.append((Releases.fragment == sub))
	if chp:
		flt.append((Releases.chapter == chp))
	if vol:
		flt.append((Releases.chapter == vol))

	if not any((vol, chp, postfix)):
		flash(gettext('Releases without content in any of the chapter, volume or postfix fields are not valid.'))
		return redirect(url_for('renderSeriesIdWithoutSlug', sid=sid))

	have = Releases.query.filter(and_(*flt)).all()

	if have:
		flash(gettext('That release appears to already have been added.'))
		return redirect(url_for('renderSeriesIdWithoutSlug', sid=sid))

	series = Series.query.filter(Series.id==sid).scalar()
	if not series:
		flash(gettext('Invalid series-id in add call? Are you trying something naughty?'))
		return redirect(url_for('index'))

	group = Translators.query.filter(Translators.id==group).scalar()
	if oel:
		groupid = None
	elif group:
		groupid = group.id
	else:
		flash(gettext('Invalid group-id in add call? Are you trying something naughty?'))
		return redirect(url_for('index'))

	# Everything has validated, add the new item.
	new = Releases(
		tlgroup   = groupid,
		series    = series.id,
		published = pubdate,
		volume    = vol,
		chapter   = chp,
		fragment  = sub,
		postfix   = postfix,
		srcurl    = itemurl,
		changetime = datetime.datetime.now(),
		changeuser = g.user.id,
		include    = True,
		)
	db.session.add(new)
	app_utilities.update_latest_row(series)
	db.session.commit()

	flash(gettext('New release added. Thanks for contributing!'))
	flash(gettext('If the release you\'re adding has a RSS feed, you can ask for it to be added to the automatic feed system on the forum!'))
	return redirect(url_for('renderSeriesIdWithoutSlug', sid=sid))

def add_post(form):
	title   = bleach.clean(form.data['title'], tags=[], strip=True)
	content = markdown.markdown(bleach.clean(form.data['content'], strip=True))
	new = News_Posts(
			title     = title,
			body      = content,
			timestamp = datetime.datetime.now(),
			user_id   = g.user.id,
		)
	db.session.add(new)
	db.session.commit()
	flash(gettext('New post added.'))
	return redirect(url_for('renderNews'))


def preset(cls):
	return lambda : cls(NewReleaseForm=datetime.datetime.now())

dispatch = {
	'group'   : (NewGroupForm,   add_group,   ''),
	'series'  : (NewSeriesForm,  add_series,  ''),
	'release' : (NewReleaseForm, add_release, ''),
	'post'    : (PostForm,       add_post,    ''),
}


@app.route('/add/<add_type>/<int:sid>/', methods=('GET', 'POST'))
@app.route('/add/<add_type>/', methods=('GET', 'POST'))
def addNewItem(add_type, sid=None):

	if app.config['READ_ONLY']:
		flash(gettext('Site is in read-only mode!'))
		return redirect(url_for('index'))

	if not add_type in dispatch:
		flash(gettext('Unknown type of content to add!'))
		return redirect(url_for('index'))
	if add_type == 'release' and sid == None:
		flash(gettext('Adding a release must involve a series-id. How did you even do that?'))
		return redirect(url_for('index'))

	form_class, callee, message = dispatch[add_type]
	have_auth = g.user.is_authenticated()

	if add_type == 'release':
		series = Series.query.filter(Series.id==sid).scalar()

		if not series:
			return render_template(
					'not-implemented-yet.html',
					message = "Trying to add a release for series sid: '%s' that doesn't exist? Wat? This shouldn't happen. Are you abusing something?" % sid
					)


		form = form_class(
				series_id = series.id,
				is_oel    = series.tl_type
			)

		altn = AlternateTranslatorNames.query.all()
		altfmt = [(x.group, x.name) for x in altn if x.group]
		altfmt.sort(key=lambda x:x[1])
		form.group.choices = altfmt
	else:
		form = form_class()

	print("Trying to validate:", (form, request.form, request.args, request.headers.get('User-Agent')))
	# print(form.validate_on_submit())
	if form.validate_on_submit():
		print("Post request by uid %s. Validating" % g.user.id)
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
				message  = message,
				series   = series
				)

	if add_type == 'post':
		return render_template(
				'add-post.html',
				form=form,
				)

	if add_type == 'series':
		return render_template(
				'add-series.html',
				form=form,
				add_name = add_type,
				message  = message
				)


	else:
		return render_template(
				'add.html',
				form=form,
				add_name = add_type,
				message  = message
				)
