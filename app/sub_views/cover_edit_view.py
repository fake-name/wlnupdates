
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
import app.nameTools as nt
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from app import app

from app import db

@app.route('/series-id/<sid>/edit-covers/')
def renderEditCovers(sid):
	series       =       Series.query.filter(Series.id==sid).first()
	return render_template('not-implemented-yet.html')