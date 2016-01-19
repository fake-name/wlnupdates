
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
import app.nameTools as nt
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from app import app

from app import db

@app.route('/about')
def about_site():
	return render_template('about.html')
@app.route('/help')
def help_site():
	return render_template('help.html')
@app.route('/legal')
def legal_site():
	return render_template('legal.html')
@app.route('/api-docs')
def api_docs_site():
	with open("./app/templates/api-docs.md", "r") as fp:
		return render_template('api-docs.html', markdown_content=fp.read())



