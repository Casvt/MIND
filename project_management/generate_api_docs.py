#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# autopep8: off

from os.path import dirname
from subprocess import run
from sys import path
from typing import Type

path.insert(0, dirname(dirname(__file__)))

import frontend.api
from backend.base.custom_exceptions import (NotificationServiceNotFound,
                                            ReminderNotFound, TemplateNotFound)
from backend.base.definitions import MindException, StartType
from backend.base.helpers import folder_path
from backend.internals.server import Server
from frontend.input_validation import DataSource, api_docs

# autopep8: on

api_prefix = Server.api_prefix
admin_prefix = Server.admin_prefix
api_file = folder_path('docs', 'other_docs', 'api.md')

url_var_map = {
    'int:n_id': NotificationServiceNotFound,
    'int:r_id': ReminderNotFound,
    'int:t_id': TemplateNotFound,
    'int:s_id': ReminderNotFound
}


def make_exception_instance(cls: Type[MindException]) -> MindException:
    try:
        return cls()
    except TypeError:
        try:
            return cls('1')
        except TypeError:
            try:
                return cls('1', '2')
            except AttributeError:
                return cls('1', StartType.STARTUP)


result = f"""# API
Below is the API documentation. Report an issue on [GitHub](https://github.com/Casvt/MIND/issues).

All endpoints have the `{api_prefix}` prefix. That means, for example, that `/auth/login` can be reached at `{api_prefix}/auth/login`.

## Authentication

Authentication is done using an API key.
To log in, make a POST request to the [`{api_prefix}/auth/login`](#authlogin) endpoint.
You'll receive an API key, which you can then use in your requests to authenticate.
Supply it via the url parameter `api_key`.
This API key is valid for one hour (though the admin can change this duration) after which the key expires, any further requests return 401 'APIKeyExpired' and you are required to log in again.
If no `api_key` is supplied or it is invalid, 401 `APIKeyInvalid` is returned.

For example:
```bash
curl -sSL 'http://192.168.2.15:8080{api_prefix}/reminders?api_key=ABCDEFG'
```

## Supplying data

Often, data needs to be supplied with a request:

- If the parameters need to be supplied via `url`, add them to the url as url parameters.
- If the parameters need to be supplied via `body`, add them to the body as a json object and supply the `Content-Type: application/json` header.
- If the parameters need to be supplied via `file`, send them as form data values and supply the `Content-Type: multipart/form-data` header.

For example:
```bash
# URL parameter
curl -sSL 'http://192.168.2.15:8080{api_prefix}/reminders/search?api_key=ABCDEFG&query=Fountain&sort_by=time_reversed'

# Body parameter
curl -sSLX POST \\
	-H 'Content-Type: application/json' \\
	-d '{{"title": "Test service", "url": "test://fake/url"}}' \\
	'http://192.168.2.15:8080{api_prefix}/notificationservices?api_key=ABCDEFG'

# File parameter
curl -sSLX POST \\
	-H 'Content-Type: multipart/form-data' \\
	-F file=@/backups/MIND_backup.db \\
	'http://192.168.2.15:8080{admin_prefix}/database?api_key=ABCDEFG'

```

## Endpoints
The following is automatically generated. Please report any issues on [GitHub](https://github.com/Casvt/MIND/issues).
"""

for rule, data in api_docs.items():
    result += f"""### `{rule}`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| {'Yes' if data.requires_auth else 'No'} | {data.description} |
"""

    url_var = rule.replace('<', '>').split('>')
    url_var = None if len(url_var) == 1 else url_var[1]

    if url_var:
        result += f"""
Replace `<{url_var}>` with the ID of the entry. For example: `{rule.replace(f'<{url_var}>', '2')}`.
"""

    for m_name, method in ((m, data.methods[m])
                           for m in data.methods.used_methods()):
        if method is None:
            continue

        result += f"\n??? {m_name}\n"

        if method.description:
            result += f"\n	{method.description}\n"

        var_types = {
            'url': [
                v for v in method.vars if v.source == DataSource.VALUES
            ],
            'body': [
                v for v in method.vars if v.source == DataSource.DATA
            ],
            'file': [
                v for v in method.vars if v.source == DataSource.FILES
            ]
        }

        for var_type, entries in var_types.items():
            if entries:
                result += f"""
	**Parameters ({var_type})**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
"""
                for entry in entries:
                    result += f"	{super(entry, entry('', entry.name, entry.description)).__repr__()}\n"

        result += f"""
	**Returns**

	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| {201 if m_name == 'POST' else 200} | N/A | Success |
"""

        url_exception = [url_var_map[url_var]] if url_var in url_var_map else []
        variable_exceptions = [
            e
            for v in method.vars
            for e in v('t', v.name, v.description).related_exceptions
        ]
        related_exceptions = sorted(
            (
                make_exception_instance(e)
                for e in set(variable_exceptions + url_exception)
            ),
            key=lambda e: (
                e.api_response["code"],
                e.api_response["error"]
            )
        )
        for related_exception in related_exceptions:
            ar = related_exception.api_response
            result += f"	| {ar['code']} | {ar['error']} | {related_exception.__doc__} |\n"

    result += '\n'

with open(api_file, 'r') as f:
    current_content = f.read()

if current_content == result:
    print('Nothing changed')
else:
    with open(api_file, 'w+') as f:
        f.write(result)

    run(["git", "config", "--global", "user.email", '"casvantijn@gmail.com"'])
    run(["git", "config", "--global", "user.name", '"CasVT"'])
    run(["git", "checkout", "Development"])
    run(["git", "add", api_file])
    run(["git", "commit", "-m", "Updated API docs"])
    run(["git", "push"])
