
from flask import render_template, flash, redirect, url_for, g, request
from app.forms import SearchForm
import bleach
from app.models import AlternateNames
import app.nameTools as nt
from sqlalchemy.sql.functions import Function
from sqlalchemy.sql.expression import select, desc
from app import app

from app import db


from app.historyController import renderHistory

@app.route('/history/<topic>/<int:srcId>')
def history_route(topic, srcId):
	return renderHistory(topic, srcId)
