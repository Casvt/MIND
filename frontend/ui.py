# -*- coding: utf-8 -*-

from typing import Any

from flask import Blueprint, render_template

from backend.internals.server import Server

ui = Blueprint('ui', __name__)
methods = ['GET']
SERVER = Server()


def render(filename: str, **kwargs: Any) -> str:
    return render_template(filename, url_prefix=SERVER.url_prefix, **kwargs)


@ui.errorhandler(404)
def ui_not_found(e):
    return render('page_not_found.html')


@ui.route('/', methods=methods)
def ui_login():
    return render('login.html')


@ui.route('/reminders', methods=methods)
def ui_reminders():
    return render('reminders.html')


@ui.route('/admin', methods=methods)
def ui_admin():
    return render('admin.html')
