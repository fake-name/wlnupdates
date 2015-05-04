from flask import render_template, flash, redirect, session, url_for, request, g, jsonify, send_file, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask.ext.sqlalchemy import get_debug_queries
from flask.ext.babel import gettext
from datetime import datetime
# from guess_language import guess_language
from app import app, db, lm, oid, babel
from .forms import LoginForm, EditForm, PostForm, SearchForm, SignupForm
from .models import Users, Post, SeriesChanges, TagsChanges, GenresChanges, AuthorChanges, IllustratorsChanges, TranslatorsChanges, ReleasesChanges, Covers

from .confirm import send_email

from .apiview import handleApiPost, handleApiGet

import config
import os.path
from sqlalchemy.sql.expression import func


dispatch_table = {
	'description'  : SeriesChanges,
	'demographic'  : SeriesChanges,
	'type'         : SeriesChanges,
	'origin_loc'   : SeriesChanges,
	'orig_lang'    : SeriesChanges,
	'author'       : AuthorChanges,
	'illustrators' : IllustratorsChanges,
	'tag'          : TagsChanges,
	'genre'        : GenresChanges,
}




def renderHistory(histType, contentId):
	if histType not in dispatch_table:
		return render_template('not-implemented-yet.html', message='Error! Invalid history type.')

	table = dispatch_table[histType]

	if table == SeriesChanges:
		conditional = (table.srccol==contentId)
	else:
		conditional = (table.series==contentId)

	data = table                                   \
			.query                                 \
			.filter(conditional)                   \
			.order_by(table.changetime).all()


	seriesHist = None
	authorHist = None
	illustHist = None
	tagHist    = None
	genreHist  = None

	if table == SeriesChanges:
		seriesHist = data
	if table == AuthorChanges:
		authorHist = data
	if table == IllustratorsChanges:
		illustHist = data
	if table == TagsChanges:
		tagHist = data
	if table == GenresChanges:
		genreHist = data

	print(data)

	return render_template('history.html',
			seriesHist = seriesHist,
			authorHist = authorHist,
			illustHist = illustHist,
			tagHist    = tagHist,
			genreHist  = genreHist)
