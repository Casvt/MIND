# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO, StringIO
from os import remove, urandom
from os.path import exists
from time import time as epoch_time
from typing import Any, Callable, Dict, Tuple, Union

from flask import Response, g, request, send_file

from backend.base.custom_exceptions import (APIKeyExpired, APIKeyInvalid,
                                            LogFileNotFound)
from backend.base.definitions import (ApiKeyEntry, MindException,
                                      SendResult, Serialisable, StartType)
from backend.base.helpers import folder_path
from backend.base.logging import LOGGER, get_log_filepath
from backend.features.reminders import Reminders
from backend.features.static_reminders import StaticReminders
from backend.features.templates import Templates
from backend.implementations.apprise_parser import get_apprise_services
from backend.implementations.notification_services import NotificationServices
from backend.implementations.users import Users
from backend.internals.db import get_db, import_db
from backend.internals.server import Server, diffuse_timers
from backend.internals.settings import Settings, get_about_data
from frontend.input_validation import (AboutData, AuthLoginData,
                                       AuthLogoutData, AuthStatusData,
                                       AvailableNotificationServicesData,
                                       DatabaseData, LogfileData,
                                       NotificationServiceData,
                                       NotificationServicesData,
                                       PublicSettingsData, ReminderData,
                                       RemindersData, RestartData,
                                       SearchRemindersData,
                                       SearchStaticRemindersData,
                                       SearchTemplatesData, SettingsData,
                                       ShutdownData, StaticReminderData,
                                       StaticRemindersData, TemplateData,
                                       TemplatesData,
                                       TestNotificationServiceURLData,
                                       TestRemindersData, UserManagementData,
                                       UsersAddData, UsersData,
                                       UsersManagementData, admin_api, api,
                                       get_api_docs, input_validation)

# ===================
# region General variables and functions
# ===================
users = Users()
api_key_map: Dict[int, ApiKeyEntry] = {}


def return_api(
    result: Serialisable,
    error: Union[str, None] = None,
    code: int = 200
) -> Tuple[Dict[str, Any], int]:
    return {'error': error, 'result': result}, code


def auth() -> None:
    """Checks if the client is logged in.

    Raises:
        APIKeyInvalid: The api key supplied is invalid.
        APIKeyExpired: The api key supplied has expired.
    """
    api_key = request.values.get('api_key', '')
    hashed_api_key = hash(api_key)

    if hashed_api_key not in api_key_map:
        raise APIKeyInvalid(api_key)

    map_entry = api_key_map[hashed_api_key]
    user_data = map_entry.user_data.get()

    if (
        user_data.admin
        and not request.path.startswith(
            (Server.admin_prefix, Server.api_prefix + '/auth')
        )
    ):
        raise APIKeyInvalid(api_key)

    if (
        not user_data.admin
        and
        request.path.startswith(Server.admin_prefix)
    ):
        raise APIKeyInvalid(api_key)

    if map_entry.exp <= epoch_time():
        raise APIKeyExpired(api_key)

    # Api key valid
    sv = Settings().get_settings()
    if sv.login_time_reset:
        g.exp = map_entry.exp = (
            int(epoch_time()) + sv.login_time
        )
    else:
        g.exp = map_entry.exp

    g.hashed_api_key = hashed_api_key
    g.user_data = map_entry.user_data

    return


def endpoint_wrapper(
    method: Union[
        Callable[[Dict[str, Any]], Union[Tuple[Union[Dict[str, Any], Response], int], None]],
        Callable[[Dict[str, Any], int], Union[Tuple[Union[Dict[str, Any], Response], int], None]]
    ]
) -> Callable:
    def wrapper(*args, **kwargs):
        requires_auth = get_api_docs(request).requires_auth

        try:
            if requires_auth:
                auth()

            inputs = input_validation()
            result = method(inputs, *args, **kwargs)

        except MindException as e:
            result = return_api(**e.api_response)

        return result

    wrapper.__name__ = method.__name__
    return wrapper


# ===================
# region General Handling
# ===================
@api.errorhandler(404)
def api_not_found(e):
    return {'error': "NotFound", "result": {}}, 404


# ===================
# region Auth
# ===================
@api.route('/auth/login', AuthLoginData)
@endpoint_wrapper
def api_login(inputs: Dict[str, Any]):
    user = users.login(inputs['username'], inputs['password'])

    # Login successful

    diffuse_timers()

    # Generate an API key until one
    # is generated that isn't used already
    while True:
        api_key = urandom(16).hex() # <- length api key / 2
        hashed_api_key = hash(api_key)
        if hashed_api_key not in api_key_map:
            break

    login_time = Settings().sv.login_time
    exp = int(epoch_time()) + login_time
    api_key_map[hashed_api_key] = ApiKeyEntry(exp, user)

    result = {
        'api_key': api_key,
        'expires': exp,
        'admin': user.get().admin
    }
    return return_api(result, code=201)


@api.route('/auth/logout', AuthLogoutData)
@endpoint_wrapper
def api_logout(inputs: Dict[str, Any]):
    api_key_map.pop(g.hashed_api_key)
    return return_api({}, code=201)


@api.route('/auth/status', AuthStatusData)
@endpoint_wrapper
def api_status(inputs: Dict[str, Any]):
    map_entry = api_key_map[g.hashed_api_key]
    user_data = map_entry.user_data.get()
    result = {
        'expires': map_entry.exp,
        'username': user_data.username,
        'admin': user_data.admin
    }
    return return_api(result)


# ===================
# region User
# ===================
@api.route('/user/add', UsersAddData)
@endpoint_wrapper
def api_add_user(inputs: Dict[str, str]):
    users.add(inputs['username'], inputs['password'])
    return return_api({}, code=201)


@api.route('/user', UsersData)
@endpoint_wrapper
def api_manage_user(inputs: Dict[str, Any]):
    user = api_key_map[g.hashed_api_key].user_data
    if request.method == 'PUT':
        user.update(inputs['new_username'], inputs['new_password'])
        return return_api({})

    elif request.method == 'DELETE':
        user.delete()
        api_key_map.pop(g.hashed_api_key)
        return return_api({})


# ===================
# region Notification Service
# ===================
@api.route('/notificationservices', NotificationServicesData)
@endpoint_wrapper
def api_notification_services_list(inputs: Dict[str, str]):
    services = NotificationServices(
        api_key_map[g.hashed_api_key].user_data.user_id
    )

    if request.method == 'GET':
        result = services.fetchall()
        return return_api(result=[r.todict() for r in result])

    elif request.method == 'POST':
        result = services.add(
            title=inputs['title'],
            url=inputs['url']
        ).get()
        return return_api(result.todict(), code=201)


@api.route('/notificationservices/available', AvailableNotificationServicesData)
@endpoint_wrapper
def api_notification_service_available(inputs: Dict[str, str]):
    result = get_apprise_services()
    return return_api(result) # type: ignore


@api.route('/notificationservices/test', TestNotificationServiceURLData)
@endpoint_wrapper
def api_test_service(inputs: Dict[str, Any]):
    user_id = api_key_map[g.hashed_api_key].user_data.user_id

    success = NotificationServices(user_id).test(inputs['url'])
    return return_api(
        {
            'success': success == SendResult.SUCCESS,
            'description': success.value
        },
        code=201
    )


@api.route('/notificationservices/<int:n_id>', NotificationServiceData)
@endpoint_wrapper
def api_notification_service(inputs: Dict[str, Any], n_id: int):
    user_id = api_key_map[g.hashed_api_key].user_data.user_id
    service = NotificationServices(user_id).fetchone(n_id)

    if request.method == 'GET':
        result = service.get()
        return return_api(result.todict())

    elif request.method == 'PUT':
        result = service.update(
            title=inputs['title'],
            url=inputs['url']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        service.delete(
            inputs['delete_reminders_using']
        )
        return return_api({})


# ===================
# region Library
# ===================
@api.route('/reminders', RemindersData)
@endpoint_wrapper
def api_reminders_list(inputs: Dict[str, Any]):
    reminders = Reminders(api_key_map[g.hashed_api_key].user_data.user_id)

    if request.method == 'GET':
        result = reminders.fetchall(inputs['sort_by'])
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        result = reminders.add(
            title=inputs['title'],
            time=inputs['time'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            repeat_quantity=inputs['repeat_quantity'],
            repeat_interval=inputs['repeat_interval'],
            weekdays=inputs['weekdays'],
            color=inputs['color'],
            enabled=inputs['enabled']
        )
        return return_api(result.get().todict(), code=201)


@api.route('/reminders/search', SearchRemindersData)
@endpoint_wrapper
def api_reminders_query(inputs: Dict[str, Any]):
    reminders = Reminders(api_key_map[g.hashed_api_key].user_data.user_id)
    result = reminders.search(inputs['query'], inputs['sort_by'])
    return return_api([r.todict() for r in result])


@api.route('/reminders/test', TestRemindersData)
@endpoint_wrapper
def api_test_reminder(inputs: Dict[str, Any]):
    Reminders(
        api_key_map[g.hashed_api_key].user_data.user_id
    ).test_reminder(
        inputs['title'],
        inputs['notification_services'],
        inputs['text']
    )
    return return_api({}, code=201)


@api.route('/reminders/<int:r_id>', ReminderData)
@endpoint_wrapper
def api_get_reminder(inputs: Dict[str, Any], r_id: int):
    reminders = Reminders(
        api_key_map[g.hashed_api_key].user_data.user_id
    )

    if request.method == 'GET':
        result = reminders.fetchone(r_id).get()
        return return_api(result.todict())

    elif request.method == 'PUT':
        print(inputs)
        result = reminders.fetchone(r_id).update(
            title=inputs['title'],
            time=inputs['time'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            repeat_quantity=inputs['repeat_quantity'],
            repeat_interval=inputs['repeat_interval'],
            weekdays=inputs['weekdays'],
            color=inputs['color'],
            enabled=inputs['enabled']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        reminders.fetchone(r_id).delete()
        return return_api({})


# ===================
# region Template
# ===================
@api.route('/templates', TemplatesData)
@endpoint_wrapper
def api_get_templates(inputs: Dict[str, Any]):
    templates = Templates(
        api_key_map[g.hashed_api_key].user_data.user_id
    )

    if request.method == 'GET':
        result = templates.fetchall(inputs['sort_by'])
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        result = templates.add(
            title=inputs['title'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            color=inputs['color']
        )
        return return_api(result.get().todict(), code=201)


@api.route('/templates/search', SearchTemplatesData)
@endpoint_wrapper
def api_templates_query(inputs: Dict[str, Any]):
    templates = Templates(
        api_key_map[g.hashed_api_key].user_data.user_id
    )
    result = templates.search(inputs['query'], inputs['sort_by'])
    return return_api([r.todict() for r in result])


@api.route('/templates/<int:t_id>', TemplateData)
@endpoint_wrapper
def api_get_template(inputs: Dict[str, Any], t_id: int):
    template = Templates(
        api_key_map[g.hashed_api_key].user_data.user_id
    ).fetchone(t_id)

    if request.method == 'GET':
        result = template.get()
        return return_api(result.todict())

    elif request.method == 'PUT':
        result = template.update(
            title=inputs['title'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            color=inputs['color']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        template.delete()
        return return_api({})


# ===================
# region Static Reminder
# ===================
@api.route('/staticreminders', StaticRemindersData)
@endpoint_wrapper
def api_static_reminders_list(inputs: Dict[str, Any]):
    reminders = StaticReminders(
        api_key_map[g.hashed_api_key].user_data.user_id
    )

    if request.method == 'GET':
        result = reminders.fetchall(inputs['sort_by'])
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        result = reminders.add(
            title=inputs['title'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            color=inputs['color']
        )
        return return_api(result.get().todict(), code=201)


@api.route('/staticreminders/search', SearchStaticRemindersData)
@endpoint_wrapper
def api_static_reminders_query(inputs: Dict[str, Any]):
    result = StaticReminders(
        api_key_map[g.hashed_api_key].user_data.user_id
    ).search(inputs['query'], inputs['sort_by'])
    return return_api([r.todict() for r in result])


@api.route('/staticreminders/<int:s_id>', StaticReminderData)
@endpoint_wrapper
def api_get_static_reminder(inputs: Dict[str, Any], s_id: int):
    reminders = StaticReminders(
        api_key_map[g.hashed_api_key].user_data.user_id
    )

    if request.method == 'GET':
        result = reminders.fetchone(s_id).get()
        return return_api(result.todict())

    elif request.method == 'POST':
        reminders.fetchone(s_id).trigger_reminder()
        return return_api({}, code=201)

    elif request.method == 'PUT':
        result = reminders.fetchone(s_id).update(
            title=inputs['title'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            color=inputs['color']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        reminders.fetchone(s_id).delete()
        return return_api({})


# ===================
# region Admin Panel
# ===================
@admin_api.route('/shutdown', ShutdownData)
@endpoint_wrapper
def api_shutdown(inputs: Dict[str, Any]):
    Server().shutdown()
    return return_api({})


@admin_api.route('/restart', RestartData)
@endpoint_wrapper
def api_restart(inputs: Dict[str, Any]):
    Server().restart()
    return return_api({})


@api.route('/settings', PublicSettingsData)
@endpoint_wrapper
def api_settings(inputs: Dict[str, Any]):
    return return_api(Settings().get_settings().todict())


@api.route('/about', AboutData)
@endpoint_wrapper
def api_about(inputs: Dict[str, Any]):
    return return_api(get_about_data())


@admin_api.route('/settings', SettingsData)
@endpoint_wrapper
def api_admin_settings(inputs: Dict[str, Any]):
    settings = Settings()

    if request.method == 'GET':
        return return_api(settings.get_settings().todict())

    elif request.method == 'PUT':
        LOGGER.info(f'Submitting admin settings: {inputs}')

        hosting_changes = any(
            inputs[s] is not None
            for s in ('host', 'port', 'url_prefix')
        )

        if hosting_changes:
            settings.backup_hosting_settings()

        settings.update({
            k: v
            for k, v in inputs.items()
            if v is not None
        })

        if hosting_changes:
            Server().restart(StartType.RESTART_HOSTING_CHANGES)

        return return_api({})


@admin_api.route('/logs', LogfileData)
@endpoint_wrapper
def api_admin_logs(inputs: Dict[str, Any]):
    file = get_log_filepath()
    if not exists(file):
        raise LogFileNotFound(file)

    sio = StringIO()
    for ext in ('.1', ''):
        lf = file + ext
        if not exists(lf):
            continue
        with open(lf, 'r') as f:
            sio.writelines(f)

    return send_file(
        BytesIO(sio.getvalue().encode('utf-8')),
        mimetype="application/octet-stream",
        download_name=f'MIND_log_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.txt'
    ), 200


@admin_api.route('/users', UsersManagementData)
@endpoint_wrapper
def api_admin_users(inputs: Dict[str, Any]):
    if request.method == 'GET':
        result = users.get_all()
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        users.add(inputs['username'], inputs['password'], True)
        return return_api({}, code=201)


@admin_api.route('/users/<int:u_id>', UserManagementData)
@endpoint_wrapper
def api_admin_user(inputs: Dict[str, Any], u_id: int):
    user = users.get_one(u_id)
    if request.method == 'PUT':
        user.update(inputs['new_username'], inputs['new_password'])
        return return_api({})

    elif request.method == 'DELETE':
        user.delete()
        for key, value in api_key_map.items():
            if value.user_data.user_id == u_id:
                del api_key_map[key]
                break
        return return_api({})


@admin_api.route('/database', DatabaseData)
@endpoint_wrapper
def api_admin_database(inputs: Dict[str, Any]):
    if request.method == "GET":
        current_date = datetime.now().strftime(r"%Y_%m_%d_%H_%M")
        filename = folder_path(
            'db', f'MIND_{current_date}.db'
        )
        get_db().execute(
            "VACUUM INTO ?;",
            (filename,)
        )

        with open(filename, 'rb') as database_file:
            bi = BytesIO(database_file.read())

        remove(filename)
        return send_file(
            bi,
            mimetype="application/x-sqlite3",
            download_name=f'MIND_{current_date}.db'
        ), 200

    elif request.method == "POST":
        import_db(inputs['file'], inputs['copy_hosting_settings'])
        return return_api({})
