# -*- coding: utf-8 -*-

from re import compile
from typing import Any, Dict, List, Tuple, Union

from apprise import Apprise

from backend.base.helpers import when_not_none

remove_named_groups = compile(r'(?<=\()\?P<\w+>')
IGNORED_ARGS = ('cto', 'format', 'overflow', 'rto', 'verify')


def process_regex(
    regex: Union[Tuple[str, str], None]
) -> Union[Tuple[str, str], None]:
    return when_not_none(
        regex,
        lambda r: (remove_named_groups.sub('', r[0]), r[1])
    )


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
    apprise_services = []

    raw = Apprise().details()['schemas']
    for entry in raw:
        result = {
            'name': str(entry['service_name']),
            'doc_url': entry['setup_url'],
            'details': {
                'templates': entry['details']['templates'],
                'tokens': [],
                'args': []
            }
        }

        handled_tokens = set()
        for k, v in entry['details']['tokens'].items():
            if not v['type'].startswith('list:'):
                continue

            list_entry = {
                'name': v['name'],
                'map_to': k,
                'required': v['required'],
                'type': 'list',
                'delim': v['delim'][0],
                'content': []
            }

            for content in v['group']:
                token = entry['details']['tokens'][content]
                list_entry['content'].append({
                    'name': token['name'],
                    'required': token['required'],
                    'type': token['type'],
                    'prefix': token.get('prefix'),
                    'regex': process_regex(token.get('regex'))
                })
                handled_tokens.add(content)

            result['details']['tokens'].append(list_entry)
            handled_tokens.add(k)

        for k, v in entry['details']['tokens'].items():
            if k in handled_tokens:
                continue

            normal_entry = {
                'name': v['name'],
                'map_to': k,
                'required': v['required'],
                'type': v['type'].split(':')[0]
            }

            if v['type'].startswith('choice'):
                normal_entry.update({
                    'options': v.get('values'),
                    'default': v.get('default')
                })

            else:
                normal_entry.update({
                    'prefix': v.get('prefix'),
                    'min': v.get('min'),
                    'max': v.get('max'),
                    'regex': process_regex(v.get('regex'))
                })

            result['details']['tokens'].append(normal_entry)

        for k, v in entry['details']['args'].items():
            if (
                v.get('alias_of') is not None
                or k in IGNORED_ARGS
            ):
                continue

            args_entry = {
                'name': v.get('name', k),
                'map_to': k,
                'required': v.get('required', False),
                'type': v['type'].split(':')[0],
            }

            if v['type'].startswith('list'):
                args_entry.update({
                    'delim': v['delim'][0],
                    'content': []
                })

            elif v['type'].startswith('choice'):
                args_entry.update({
                    'options': v['values'],
                    'default': v.get('default')
                })

            elif v['type'] == 'bool':
                args_entry.update({
                    'default': v['default']
                })

            else:
                args_entry.update({
                    'min': v.get('min'),
                    'max': v.get('max'),
                    'regex': process_regex(v.get('regex'))
                })

            result['details']['args'].append(args_entry)

        result['details']['tokens'].sort(key=_sort_tokens)
        result['details']['args'].sort(key=_sort_tokens)
        apprise_services.append(result)

    apprise_services.sort(key=lambda s: s['name'].lower())

    apprise_services.insert(0, {
        'name': 'Custom URL',
        'doc_url': 'https://github.com/caronc/apprise#supported-notifications',
        'details': {
            'templates': ['{url}'],
            'tokens': [{
                'name': 'Apprise URL',
                'map_to': 'url',
                'required': True,
                'type': 'string',
                'prefix': None,
                'min': None,
                'max': None,
                'regex': None
            }],
            'args': []
        }
    })

    return apprise_services
