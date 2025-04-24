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


@ui.route('/manifest.json', methods=methods)
def ui_manifest():
    from io import BytesIO
    from json import dumps

    from flask import send_file

    return send_file(
        BytesIO(dumps(
            {
                "name": "MIND",
                "short_name": "MIND",
                "description": "MIND is a simple self hosted reminder application that can send push notifications to your device. Set the reminder and forget about it!",
                "display": "standalone",
                "orientation": "portrait-primary",
                "start_url": f"{SERVER.url_prefix}/",
                "scope": f"{SERVER.url_prefix}/",
                "id": f"{SERVER.url_prefix}/",
                "background_color": "#1b1b1b",
                "theme_color": "#6b6b6b",
                "icons": [
                    {
                        "src": f"{SERVER.url_prefix}/static/img/favicon.svg",
                        "type": "image/svg+xml",
                        "sizes": "any"
                    }
                ]
            },
            indent=4
        ).encode('utf-8')),
        mimetype="application/manifest+json",
        download_name="manifest.json"
    ), 200


@ui.route('/', methods=methods)
def ui_login():
    return render('login.html')


@ui.route('/reminders', methods=methods)
def ui_reminders():
    return render('reminders.html')


@ui.route('/admin', methods=methods)
def ui_admin():
    return render('admin.html')
