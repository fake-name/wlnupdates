# -*- coding: utf-8 -*-
"""
    flaskbb.user.views
    ~~~~~~~~~~~~~~~~~~~~

    The user view handles the user profile
    and the user settings from a signed in user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import Blueprint, flash, request
from flask_login import login_required, current_user
from flask_themes2 import get_themes_list
from flask_babelex import gettext as _

from app import babel
from flaskbb.utils.helpers import render_template
from flaskbb.user.models import Users
from flaskbb.user.forms import (ChangePasswordForm, ChangeEmailForm,
                                ChangeUserDetailsForm, GeneralSettingsForm)


user = Blueprint("user", __name__)


@user.route("/<nickname>")
def profile(nickname):
    user = Users.query.filter_by(nickname=nickname).first_or_404()

    return render_template("user/profile.html", user=user)


@user.route("/<nickname>/topics")
def view_all_topics(nickname):
    page = request.args.get("page", 1, type=int)
    user = Users.query.filter_by(nickname=nickname).first_or_404()
    topics = user.all_topics(page)
    return render_template("user/all_topics.html", user=user, topics=topics)


@user.route("/<nickname>/posts")
def view_all_posts(nickname):
    page = request.args.get("page", 1, type=int)
    user = Users.query.filter_by(nickname=nickname).first_or_404()
    posts = user.all_posts(page)
    return render_template("user/all_posts.html", user=user, posts=posts)


@user.route("/settings/general", methods=["POST", "GET"])
@login_required
def settings():
    form = GeneralSettingsForm()

    form.theme.choices = [(theme.identifier, theme.name)
                          for theme in get_themes_list()]

    form.language.choices = [(locale.language, locale.display_name)
                             for locale in babel.list_translations()]

    if form.validate_on_submit():
        current_user.theme = form.theme.data
        current_user.language = form.language.data
        current_user.save()

        flash(_("Settings updated."), "success")
    else:
        form.theme.data = current_user.theme
        form.language.data = current_user.language

    return render_template("user/general_settings.html", form=form)


@user.route("/settings/password", methods=["POST", "GET"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        current_user.save()

        flash(_("Password updated."), "success")
    return render_template("user/change_password.html", form=form)


@user.route("/settings/email", methods=["POST", "GET"])
@login_required
def change_email():
    form = ChangeEmailForm(current_user)
    if form.validate_on_submit():
        current_user.email = form.new_email.data
        current_user.save()

        flash(_("E-Mail Address updated."), "success")
    return render_template("user/change_email.html", form=form)


@user.route("/settings/user-details", methods=["POST", "GET"])
@login_required
def change_user_details():
    form = ChangeUserDetailsForm(obj=current_user)

    if form.validate_on_submit():
        form.populate_obj(current_user)
        current_user.save()

        flash(_("Details updated."), "success")

    return render_template("user/change_user_details.html", form=form)
