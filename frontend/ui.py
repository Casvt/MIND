# -*- coding: utf-8 -*-

from io import BytesIO
from json import dumps
from typing import Any

from flask import Blueprint, render_template, send_file

from backend.internals.server import Server

ui = Blueprint('ui', __name__)


def render(filename: str, **kwargs: Any) -> str:
    return render_template(filename, url_prefix=Server.url_prefix, **kwargs)


@ui.route('/manifest.json')
def ui_manifest():
    # autopep8: off
    manifest = {
        "name": "MIND",
        "short_name": "MIND",
        "description":
            "MIND is a simple self hosted reminder application that can send "
            "push notifications to your device. Set the reminder and forget "
            "about it!",
        "display": "standalone",
        "orientation": "portrait-primary",
        "start_url": f"{Server.url_prefix}/",
        "scope": f"{Server.url_prefix}/",
        "id": f"{Server.url_prefix}/",
        "background_color": "#1b1b1b",
        "theme_color": "#6b6b6b",
        "icons": [
            {
                "src": f"{Server.url_prefix}/static/img/favicon.svg",
                "type": "image/svg+xml",
                "sizes": "any"
            }
        ]
    }
    # autopep8: on

    return send_file(
        BytesIO(
            dumps(manifest, indent=4).encode('utf-8')
        ),
        mimetype="application/manifest+json",
        download_name="manifest.json"
    ), 200


@ui.route('/')
def ui_login():
    return render('login.html')


@ui.route('/reminders')
def ui_reminders():
    return render('reminders.html')


@ui.route('/admin')
def ui_admin():
    return render('admin.html')
