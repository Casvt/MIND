#-*- coding: utf-8 -*-

import logging
from flask import Blueprint, render_template

ui = Blueprint('ui', __name__)

methods = ['GET']

@ui.route('/', methods=methods)
def ui_login():
	return render_template('login.html', url_prefix=logging.URL_PREFIX)

@ui.route('/reminders', methods=methods)
def ui_reminders():
	return render_template('reminders.html', url_prefix=logging.URL_PREFIX)

@ui.route('/admin', methods=methods)
def ui_admin():
	return render_template('admin.html', url_prefixx=logging.URL_PREFIX)
