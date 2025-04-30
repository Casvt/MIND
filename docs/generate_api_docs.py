#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# autopep8: off

from os.path import dirname
from subprocess import run
from sys import path
from typing import List, Type, Union

path.insert(0, dirname(dirname(__file__)))

import frontend.api
from backend.base.custom_exceptions import (DatabaseFileNotFound,
                                            NotificationServiceNotFound,
                                            ReminderNotFound, TemplateNotFound)
from backend.base.definitions import MindException, StartType
from backend.base.helpers import folder_path
from backend.internals.server import Server
from frontend.input_validation import API_DOCS, DataSource, InputVariable

# autopep8: on

API_PREFIX = Server.api_prefix
ADMIN_PREFIX = Server.admin_prefix
API_FILE = folder_path('docs', 'src', 'other_docs', 'api.md')

url_var_map = {
    'int:n_id': NotificationServiceNotFound,
    'int:r_id': ReminderNotFound,
    'int:t_id': TemplateNotFound,
    'int:s_id': ReminderNotFound,
    'int:b_idx': DatabaseFileNotFound
}

result = f"""# API
Below is the API documentation. Report an issue on [GitHub](https://github.com/Casvt/MIND/issues).

All endpoints have the `{API_PREFIX}` prefix. That means, for example, that `/auth/login` can be reached at `{API_PREFIX}/auth/login`.

## Authentication

Authentication is done using an API key.
To log in, make a POST request to the [`{API_PREFIX}/auth/login`](#authlogin) endpoint.
You'll receive an API key, which you can then use in your requests to authenticate.
Supply it via the url parameter `api_key`.
This API key is valid for one hour (though the admin can change this duration) after which the key expires, any further requests return 401 'APIKeyExpired' and you are required to log in again.
If no `api_key` is supplied or it is invalid, 401 `APIKeyInvalid` is returned.

For example:
```bash
curl -sSL 'http://192.168.2.15:8080{API_PREFIX}/reminders?api_key=ABCDEFG'
```

## Supplying data

Often, data needs to be supplied with a request:

- If the parameters need to be supplied via `url`, add them to the url as url parameters.
- If the parameters need to be supplied via `body`, add them to the body as a json object and supply the `Content-Type: application/json` header.
- If the parameters need to be supplied via `file`, send them as form data values and supply the `Content-Type: multipart/form-data` header.

For example:
```bash
# URL parameter
curl -sSL 'http://192.168.2.15:8080{API_PREFIX}/reminders/search?api_key=ABCDEFG&query=Fountain&sort_by=time_reversed'

# Body parameter
curl -sSLX POST \\
	-H 'Content-Type: application/json' \\
	-d '{{"title": "Test service", "url": "test://fake/url"}}' \\
	'http://192.168.2.15:8080{API_PREFIX}/notificationservices?api_key=ABCDEFG'

# File parameter
curl -sSLX POST \\
	-H 'Content-Type: multipart/form-data' \\
	-F file=@/backups/MIND_backup.db \\
	'http://192.168.2.15:8080{ADMIN_PREFIX}/database?api_key=ABCDEFG'

```

## Endpoints
The following is automatically generated. Please report any issues on [GitHub](https://github.com/Casvt/MIND/issues).
"""


def make_exception_instance(cls: Type[MindException]) -> MindException:
    for args in (
        (),
        ('1'),
        ('1', '2'),
        ('1', StartType.STARTUP)
    ):
        try:
            inst = cls(*args)
        except (TypeError, AttributeError):
            continue
        else:
            return inst

    raise RuntimeError("Unsupported exception parameter")


def extract_url_var(endpoint: str) -> Union[str, None]:
    split = endpoint.replace('<', '>').split('>')
    return None if len(split) == 1 else split[1]


def rule_header(endpoint: str, requires_auth: bool, description: str) -> str:
    return f"""### `{endpoint}`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| {'Yes' if requires_auth else 'No'} | {description} |
"""


def url_var_note(endpoint: str, url_var: str) -> str:
    return f"""
Replace `<{url_var}>` with the ID of the entry. For example: `{endpoint.replace(f'<{url_var}>', '2')}`.
"""


def method_body(name: str, description: str) -> str:
    r = f"\n??? {name.upper()}\n"

    if description:
        r += f"\n	{description}\n"

    return r


def method_parameters(
    var_type: str,
    variables: List[Type[InputVariable]]
) -> str:
    r = f"""
	**Parameters ({var_type})**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
"""

    for var in variables:
        r += "	| %s | %s | %s | %s | %s |\n" % (
            var.name, 'Yes' if var.required else 'No',
            ','.join(v.value for v in var.data_type), var.description,
            ", ".join(str(v) for v in var.options) or "N/A"
        )

    return r


def return_codes(
    method_name: str,
    exceptions: List[MindException]
) -> str:
    r = f"""
	**Returns**

	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| {201 if method_name == 'post' else 200} | N/A | Success |
"""

    for exception in exceptions:
        r += "	| %d | %s | %s |\n" % (
            exception.api_response['code'], exception.api_response['error'],
            exception.__doc__
        )

    return r


def create_result(base_string: str) -> str:
    for endpoint, data in API_DOCS.items():
        # Add header
        base_string += rule_header(
            endpoint,
            data.requires_auth,
            data.description
        )

        # Add note about url var
        url_var = extract_url_var(endpoint)
        if url_var:
            base_string += url_var_note(endpoint, url_var)

        # Add info for each method
        for m_name, method in (
            (m, data.methods[m])
            for m in data.methods.used_methods()
        ):
            if method is None:
                continue

            # Add basic method info
            base_string += method_body(m_name, method.description)

            # Add input variable info
            var_types = {
                'url': [
                    v for v in method.input_variables if v.source == DataSource.VALUES
                ],
                'body': [
                    v for v in method.input_variables if v.source == DataSource.DATA
                ],
                'file': [
                    v for v in method.input_variables if v.source == DataSource.FILES
                ]
            }
            for var_type, entries in var_types.items():
                if entries:
                    base_string += method_parameters(var_type, entries)

            url_exception = (
                [url_var_map[url_var]]
                if url_var in url_var_map else
                []
            )
            variable_exceptions = [
                e
                for v in method.input_variables
                for e in v.related_exceptions
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
            base_string += return_codes(m_name, related_exceptions)

        base_string += '\n'
    return base_string.strip()


if __name__ == '__main__':
    result = create_result(result)

    with open(API_FILE, 'r') as f:
        current_content = f.read()

    if current_content == result:
        print('Nothing changed')
    else:
        with open(API_FILE, 'w+') as f:
            f.write(result)

        run(["git", "config", "--global", "user.email", '"casvantijn@gmail.com"'])
        run(["git", "config", "--global", "user.name", '"CasVT"'])
        run(["git", "checkout", "Development"])
        run(["git", "add", API_FILE])
        run(["git", "commit", "-m", "Updated API docs"])
        run(["git", "push"])
