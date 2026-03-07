# -*- coding: utf-8 -*-

"""
Process apprise.Apprise().details() output for URL builder.
"""

from itertools import chain
from re import compile
from typing import Any, Dict, List, Tuple, Union

from backend.base.helpers import init_apprise, when_not_none

remove_named_groups = compile(r'(?<=\()\?P<\w+>')
IGNORED_ARGS = {'cto', 'format', 'overflow', 'rto', 'verify'}
CUSTOM_URL_SCHEMA = {
    "service_name": "Custom URL",
    "setup_url": "https://github.com/caronc/apprise#supported-notifications",
    "details": {
        "templates": ("{url}",),
        "tokens": {
            "url": {
                "name": "Apprise URL",
                "type": "string",
                "required": True
            }
        },
        "args": {}
    }
}


def _process_regex(
    regex: Union[Tuple[str, str], None]
) -> Union[Tuple[str, str], None]:
    return when_not_none(
        regex,
        lambda r: (remove_named_groups.sub('', r[0]), r[1])
    )


def _process_list(
    token_name: str,
    token_details: Dict[str, Any],
    all_tokens: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    list_entry = {
        'name': token_details['name'],
        'map_to': token_name,
        'required': token_details['required'],
        'type': 'list',
        'delim': token_details['delim'][0],
        'content': []
    }

    for content in token_details['group']:
        token = all_tokens[content]
        list_entry['content'].append({
            'name': token['name'],
            'required': token['required'],
            'type': token['type'],
            'prefix': token.get('prefix'),
            'regex': _process_regex(token.get('regex'))
        })

    return list_entry


def _process_normal_token(
    token_name: str,
    token_details: Dict[str, Any]
) -> Dict[str, Any]:
    normal_entry = {
        'name': token_details['name'],
        'map_to': token_name,
        'required': token_details['required'],
        'type': token_details['type'].split(':')[0]
    }

    if token_details['type'].startswith('choice'):
        normal_entry.update({
            'options': token_details.get('values'),
            'default': token_details.get('default')
        })

    else:
        normal_entry.update({
            'prefix': token_details.get('prefix'),
            'min': token_details.get('min'),
            'max': token_details.get('max'),
            'regex': _process_regex(token_details.get('regex'))
        })

    return normal_entry


def _process_arg(
    arg_name: str,
    arg_details: Dict[str, Any]
) -> Dict[str, Any]:
    args_entry = {
        'name': arg_details.get('name', arg_name),
        'map_to': arg_name,
        'required': arg_details.get('required', False),
        'type': arg_details['type'].split(':')[0],
    }

    if arg_details['type'].startswith('list'):
        args_entry.update({
            'delim': arg_details['delim'][0],
            'content': []
        })

    elif arg_details['type'].startswith('choice'):
        args_entry.update({
            'options': arg_details['values'],
            'default': arg_details.get('default')
        })

    elif arg_details['type'] == 'bool':
        args_entry.update({
            'default': arg_details['default']
        })

    else:
        args_entry.update({
            'min': arg_details.get('min'),
            'max': arg_details.get('max'),
            'regex': _process_regex(arg_details.get('regex'))
        })

    return args_entry


def _sort_tokens(t: Dict[str, Any]) -> List[int]:
    result = [
        int(not t['required'])
    ]

    if t['name'] == 'Schema':
        result.append(0)

    if t['type'] == 'choice':
        result.append(1)

    elif t['type'] != 'list':
        result.append(2)

    else:
        result.append(3)

    return result


def get_apprise_services() -> List[Dict[str, Any]]:
    """Get a list of all Apprise services, their URL schemas, tokens and
    arguments.

    Returns:
        List[Dict[str, Any]]: The list.
    """
    result: List[Dict[str, Any]] = []

    schemas = init_apprise().details()['schemas']
    for schema in chain((CUSTOM_URL_SCHEMA,), schemas):
        entry = {
            'name': str(schema['service_name']),
            'doc_url': schema['setup_url'],
            'details': {
                'templates': schema['details']['templates'],
                'tokens': [],
                'args': []
            }
        }

        # Process lists and tokens they contain first
        handled_tokens = set()
        for token_name, token_details in schema['details']['tokens'].items():
            if not token_details['type'].startswith('list:'):
                continue

            list_entry = _process_list(
                token_name, token_details, schema['details']['tokens']
            )
            entry['details']['tokens'].append(list_entry)
            handled_tokens.add(token_name)
            handled_tokens.update(token_details['group'])

        # Process all other tokens
        entry['details']['tokens'] += [
            _process_normal_token(token_name, token_details)
            for token_name, token_details in schema['details']['tokens'].items()
            if token_name not in handled_tokens
        ]

        # Process args
        entry['details']['args'] += [
            _process_arg(arg_name, arg_details)
            for arg_name, arg_details in schema['details']['args'].items()
            if not (
                arg_details.get('alias_of') is not None
                or arg_name in IGNORED_ARGS
            )
        ]

        # Sort tokens and args
        entry['details']['tokens'].sort(key=_sort_tokens)
        entry['details']['args'].sort(key=_sort_tokens)
        result.append(entry)

    result.sort(key=lambda s: (
        int(s["name"] != "Custom URL"),
        s["name"].lower()
    ))

    return result
