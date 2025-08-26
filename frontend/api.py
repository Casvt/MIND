# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO
from os import remove
from os.path import basename
from time import time as epoch_time
from typing import TYPE_CHECKING, Any, Dict, cast

from flask import after_this_request, g as flask_g, request, send_file

from backend.base.custom_exceptions import APIKeyExpired, APIKeyInvalid
from backend.base.definitions import (ApiKeyEntry, Constants,
                                      SendResult, StartType, UserData)
from backend.base.helpers import (folder_path, generate_api_key,
                                  hash_api_key, return_api)
from backend.base.logging import LOGGER, get_log_file_contents
from backend.implementations.apprise_parser import get_apprise_services
from backend.implementations.notification_services import NotificationServices
from backend.implementations.reminders import Reminders
from backend.implementations.static_reminders import StaticReminders
from backend.implementations.templates import Templates
from backend.implementations.users import Users
from backend.internals.db_backup_import import (create_database_copy,
                                                get_backup, get_backups,
                                                import_db, import_db_backup)
from backend.internals.server import Server, StartTypeHandlers
from backend.internals.settings import Settings, get_about_data
from frontend.input_validation import (AboutData, AuthLoginData,
                                       AuthLogoutData, AuthStatusData,
                                       AvailableNotificationServicesData,
                                       BackupData, BackupsData, DatabaseData,
                                       LogfileData, NotificationServiceData,
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

# region Auth and input
users = Users()
api_key_map: Dict[str, ApiKeyEntry] = {}


class ApiKeyMapping:
    _next_run: int = 0

    @classmethod
    def cleanup(cls) -> None:
        """Cleans up expired API keys from the mapping."""
        now = int(epoch_time())
        if now < cls._next_run:
            return
        cls._next_run = now + Constants.API_KEY_CLEANUP_INTERVAL

        to_delete = [
            k
            for k, v in api_key_map.items()
            if v.exp + 86400 <= now
        ]
        for k in to_delete:
            del api_key_map[k]

        return

    @staticmethod
    def remove_user(user_id: int) -> None:
        for key, value in api_key_map.items():
            if value.user_data.id == user_id:
                del api_key_map[key]
                break
        return


if TYPE_CHECKING:
    class TypedAppCtxGlobals:
        hashed_api_key: str
        exp: int
        user_data: UserData
        inputs: Dict[str, Any]

    g = cast(TypedAppCtxGlobals, flask_g)
else:
    g = flask_g


def auth() -> None:
    """Checks if the client is logged in.

    Raises:
        APIKeyInvalid: The api key supplied is invalid.
        APIKeyExpired: The api key supplied has expired.
    """
    api_key = request.values.get('api_key', '')
    hashed_api_key = hash_api_key(api_key)

    if hashed_api_key not in api_key_map:
        raise APIKeyInvalid(api_key)

    map_entry = api_key_map[hashed_api_key]
    user_data = map_entry.user_data

    if (
        user_data.admin
        and not request.path.startswith(
            (Constants.ADMIN_PREFIX, Constants.API_PREFIX + '/auth')
        )
    ):
        raise APIKeyInvalid(api_key)

    if (
        not user_data.admin
        and
        request.path.startswith(Constants.ADMIN_PREFIX)
    ):
        raise APIKeyInvalid(api_key)

    if map_entry.exp <= epoch_time():
        del api_key_map[hashed_api_key]
        raise APIKeyExpired(api_key)

    # Api key valid
    sv = Settings().get_settings()
    if sv.login_time_reset:
        map_entry.exp = (
            int(epoch_time()) + sv.login_time
        )

    g.hashed_api_key = hashed_api_key
    g.user_data = user_data
    g.exp = map_entry.exp

    return


@api.before_request
@admin_api.before_request
def api_auth_and_input_validation() -> None:
    requires_auth = get_api_docs(request).requires_auth

    if requires_auth:
        auth()

    g.inputs = input_validation()
    return


# region Auth
@api.route('/auth/login', AuthLoginData)
def api_login():
    user_data = users.login(g.inputs['username'], g.inputs['password']).get()

    # Login successful

    StartTypeHandlers.diffuse_timer(StartType.RESTART_DB_CHANGES)
    StartTypeHandlers.diffuse_timer(StartType.RESTART_HOSTING_CHANGES)
    ApiKeyMapping.cleanup()

    # Generate an API key until one is generated that isn't used already
    while True:
        api_key = generate_api_key()
        hashed_api_key = hash_api_key(api_key)
        if hashed_api_key not in api_key_map:
            break

    login_time = Settings().sv.login_time
    exp = int(epoch_time()) + login_time
    api_key_map[hashed_api_key] = ApiKeyEntry(exp, user_data)

    result = {
        'api_key': api_key,
        'expires': exp,
        'admin': user_data.admin
    }
    return return_api(result, code=201)


@api.route('/auth/logout', AuthLogoutData)
def api_logout():
    del api_key_map[g.hashed_api_key]
    return return_api({}, code=201)


@api.route('/auth/status', AuthStatusData)
def api_status():
    result = {
        'expires': g.exp,
        'username': g.user_data.username,
        'admin': g.user_data.admin
    }
    return return_api(result)


# region Users
@api.route('/user/add', UsersAddData)
def api_add_user():
    inputs = g.inputs
    users.add(inputs['username'], inputs['password'])
    return return_api({}, code=201)


@api.route('/user', UsersData)
def api_manage_user():
    user = users.get_one(g.user_data.id)

    if request.method == 'PUT':
        new_username = g.inputs['new_username']
        new_password = g.inputs['new_password']

        if new_username:
            user.update_username(new_username)
        if new_password:
            user.update_password(new_password)

        return return_api({})

    elif request.method == 'DELETE':
        user.delete()
        del api_key_map[g.hashed_api_key]
        return return_api({})


# region Notification Services
@api.route('/notificationservices', NotificationServicesData)
def api_notification_services_list():
    services = NotificationServices(g.user_data.id)

    if request.method == 'GET':
        result = services.get_all()
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        inputs = g.inputs
        result = services.add(
            title=inputs['title'],
            url=inputs['url']
        ).get()
        return return_api(result.todict(), code=201)


@api.route('/notificationservices/available', AvailableNotificationServicesData)
def api_notification_service_available():
    result = get_apprise_services()
    return return_api(result)


@api.route('/notificationservices/test', TestNotificationServiceURLData)
def api_test_service():
    success = NotificationServices.test(g.inputs['url'])
    return return_api(
        {
            'success': success == SendResult.SUCCESS,
            'description': success.value
        },
        code=201
    )


@api.route('/notificationservices/<int:n_id>', NotificationServiceData)
def api_notification_service(n_id: int):
    inputs = g.inputs
    service = NotificationServices(g.user_data.id).get_one(n_id)

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


# region Reminders
@api.route('/reminders', RemindersData)
def api_reminders_list():
    inputs = g.inputs
    reminders = Reminders(g.user_data.id)

    if request.method == 'GET':
        result = reminders.get_all(inputs['sort_by'])
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
            cron_schedule=inputs['cron_schedule'],
            color=inputs['color'],
            enabled=inputs['enabled']
        )
        return return_api(result.get().todict(), code=201)


@api.route('/reminders/search', SearchRemindersData)
def api_reminders_query():
    inputs = g.inputs
    reminders = Reminders(g.user_data.id)
    result = reminders.search(inputs['query'], inputs['sort_by'])
    return return_api([r.todict() for r in result])


@api.route('/reminders/test', TestRemindersData)
def api_test_reminder():
    inputs = g.inputs
    success = Reminders(g.user_data.id).test_reminder(
        inputs['title'],
        inputs['notification_services'],
        inputs['text']
    )
    return return_api(
        {
            'success': success == SendResult.SUCCESS,
            'description': success.value
        },
        code=201
    )


@api.route('/reminders/<int:r_id>', ReminderData)
def api_get_reminder(r_id: int):
    reminder = Reminders(g.user_data.id).get_one(r_id)

    if request.method == 'GET':
        result = reminder.get()
        return return_api(result.todict())

    elif request.method == 'PUT':
        inputs = g.inputs
        result = reminder.update(
            title=inputs['title'],
            time=inputs['time'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            repeat_quantity=inputs['repeat_quantity'],
            repeat_interval=inputs['repeat_interval'],
            weekdays=inputs['weekdays'],
            cron_schedule=inputs['cron_schedule'],
            color=inputs['color'],
            enabled=inputs['enabled']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        reminder.delete()
        return return_api({})


# region Templates
@api.route('/templates', TemplatesData)
def api_get_templates():
    inputs = g.inputs
    templates = Templates(g.user_data.id)

    if request.method == 'GET':
        result = templates.get_all(inputs['sort_by'])
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
def api_templates_query():
    inputs = g.inputs
    templates = Templates(g.user_data.id)
    result = templates.search(inputs['query'], inputs['sort_by'])
    return return_api([r.todict() for r in result])


@api.route('/templates/<int:t_id>', TemplateData)
def api_get_template(t_id: int):
    template = Templates(g.user_data.id).get_one(t_id)

    if request.method == 'GET':
        result = template.get()
        return return_api(result.todict())

    elif request.method == 'PUT':
        inputs = g.inputs
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


# region Static Reminders
@api.route('/staticreminders', StaticRemindersData)
def api_static_reminders_list():
    inputs = g.inputs
    reminders = StaticReminders(g.user_data.id)

    if request.method == 'GET':
        result = reminders.get_all(inputs['sort_by'])
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
def api_static_reminders_query():
    inputs = g.inputs
    result = StaticReminders(g.user_data.id).search(
        inputs['query'], inputs['sort_by']
    )
    return return_api([r.todict() for r in result])


@api.route('/staticreminders/<int:s_id>', StaticReminderData)
def api_get_static_reminder(s_id: int):
    reminder = StaticReminders(g.user_data.id).get_one(s_id)

    if request.method == 'GET':
        result = reminder.get()
        return return_api(result.todict())

    elif request.method == 'POST':
        success = reminder.trigger_reminder()
        return return_api(
            {
                'success': success == SendResult.SUCCESS,
                'description': success.value
            },
            code=201
        )

    elif request.method == 'PUT':
        inputs = g.inputs
        result = reminder.update(
            title=inputs['title'],
            notification_services=inputs['notification_services'],
            text=inputs['text'],
            color=inputs['color']
        )
        return return_api(result.todict())

    elif request.method == 'DELETE':
        reminder.delete()
        return return_api({})


# region Admin Settings
@admin_api.route('/shutdown', ShutdownData)
def api_shutdown():
    Server().shutdown()
    return return_api({})


@admin_api.route('/restart', RestartData)
def api_restart():
    Server().restart()
    return return_api({})


@api.route('/settings', PublicSettingsData)
def api_settings():
    return return_api(Settings().get_public_settings().todict())


@api.route('/about', AboutData)
def api_about():
    return return_api(get_about_data())


@admin_api.route('/settings', SettingsData)
def api_admin_settings():
    inputs = g.inputs
    settings = Settings()

    if request.method == 'GET':
        return return_api(settings.get_public_settings().todict())

    elif request.method == 'PUT':
        LOGGER.info(f'Submitting admin settings: {inputs}')

        hosting_changes = any(
            inputs[s] is not None
            and inputs[s] != getattr(settings.sv, s)
            for s in ('host', 'port', 'url_prefix')
        )

        if hosting_changes:
            settings.backup_hosting_settings()

        settings.update(
            {
                k: v
                for k, v in inputs.items()
                if v is not None
            },
            from_public=True
        )

        if hosting_changes:
            Server().restart(StartType.RESTART_HOSTING_CHANGES)

        return return_api({})

    elif request.method == 'DELETE':
        hosting_changes = any(
            s in inputs["setting_keys"]
            and settings.get_default_value(s) != getattr(settings.sv, s)
            for s in ('host', 'port', 'url_prefix')
        )

        if hosting_changes:
            settings.backup_hosting_settings()

        for setting in inputs["setting_keys"]:
            settings.reset(setting, from_public=True)

        if hosting_changes:
            Server().restart(StartType.RESTART_HOSTING_CHANGES)

        return return_api({})


@admin_api.route('/logs', LogfileData)
def api_admin_logs():
    sio = get_log_file_contents()

    return send_file(
        BytesIO(sio.getvalue().encode('utf-8')),
        mimetype="application/octet-stream",
        download_name=f'MIND_log_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.txt'
    ), 200


# region Admin Users
@admin_api.route('/users', UsersManagementData)
def api_admin_users():
    if request.method == 'GET':
        result = users.get_all()
        return return_api([r.todict() for r in result])

    elif request.method == 'POST':
        inputs = g.inputs
        users.add(
            inputs['username'], inputs['password'],
            force=True
        )
        return return_api({}, code=201)


@admin_api.route('/users/<int:u_id>', UserManagementData)
def api_admin_user(u_id: int):
    user = users.get_one(u_id)
    if request.method == 'PUT':
        new_username = g.inputs['new_username']
        new_password = g.inputs['new_password']

        if new_username:
            user.update_username(new_username)
        if new_password:
            user.update_password(new_password)

        return return_api({})

    elif request.method == 'DELETE':
        user.delete()
        ApiKeyMapping.remove_user(u_id)
        return return_api({})


# region Admin Database
@admin_api.route('/database', DatabaseData)
def api_admin_database():
    if request.method == "GET":
        filepath = create_database_copy(folder_path('db'))

        @after_this_request
        def remove_file(response):
            remove(filepath)
            return response

        return send_file(
            filepath,
            mimetype="application/x-sqlite3",
            download_name=basename(filepath)
        ), 200

    elif request.method == "POST":
        inputs = g.inputs
        import_db(inputs['file'], inputs['copy_hosting_settings'])
        return return_api({})


@admin_api.route('/database/backups', BackupsData)
def api_admin_backups():
    return return_api(get_backups())


@admin_api.route('/database/backups/<int:b_idx>', BackupData)
def api_admin_backup(b_idx: int):
    if request.method == "GET":
        filepath = get_backup(b_idx)['filepath']
        return send_file(
            filepath,
            mimetype="application/x-sqlite3",
            download_name=basename(filepath)
        ), 200

    elif request.method == "POST":
        import_db_backup(b_idx, g.inputs['copy_hosting_settings'])
        return return_api({})
