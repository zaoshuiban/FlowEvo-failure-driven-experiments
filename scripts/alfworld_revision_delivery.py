"""Lossless delivery parsing for the bounded ALFWorld revision experiment.

This module neither executes nor repairs source. Static permissions and Worker
checks remain the caller's existing authorities. Only a single complete JSON
document with an unambiguous, nonempty top-level ``code`` string is admissible.
"""
import hashlib
import json
import math


class _Object(list):
    """JSON object pairs, retaining duplicate code keys for conflict detection."""


def _plain(value):
    if isinstance(value, _Object):
        return {key: _plain(item) for key, item in value}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _source_fields(value, path='$'):
    found = []
    if isinstance(value, _Object):
        for index, (key, item) in enumerate(value):
            child_path = path + '.' + key
            if key == 'code':
                found.append(dict(path=child_path, object_pair_index=index, value=_plain(item)))
            found.extend(_source_fields(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_source_fields(item, path+'['+str(index)+']'))
    return found


def _constant(value):
    raise ValueError('Non-JSON numeric constant: ' + value)


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Non-finite JSON number: ' + value)
    return result


def extract_candidate(raw):
    """Parse raw model text without source stripping, normalization or repair.

    ``passed`` means delivery extraction only. ``code`` is None when a source
    cannot be identified uniquely; complete raw text and all parsed code fields
    remain available even on rejection. Metadata is retained but never executed.
    Missing/non-string descriptions do not invalidate an otherwise unique source.
    """
    result = dict(passed=False, code=None, code_sha256=None, description='', applicability='',
                  ignored_metadata={}, metadata_fields=[], source_fields=[], raw=None,
                  raw_text=raw, errors=[])
    if not isinstance(raw, str):
        result['errors'].append(dict(code='RAW_TEXT_REQUIRED', message='Model content must be a JSON text string.'))
        return result
    try:
        parsed = json.loads(raw, object_pairs_hook=_Object,
                            parse_constant=_constant, parse_float=_float)
    except json.JSONDecodeError as error:
        result['errors'].append(dict(code='INVALID_JSON', message=error.msg,
                                     line=error.lineno, column=error.colno, position=error.pos))
        return result
    except ValueError as error:
        result['errors'].append(dict(code='INVALID_JSON', message=str(error)))
        return result
    result['raw'] = _plain(parsed)
    result['source_fields'] = _source_fields(parsed)
    if not isinstance(parsed, _Object):
        result['errors'].append(dict(code='TOP_LEVEL_OBJECT_REQUIRED', message='Expected exactly one JSON object.'))
        return result
    payload = result['raw']
    result['description'] = payload.get('description', '')
    result['applicability'] = payload.get('applicability', '')
    result['ignored_metadata'] = {key: value for key, value in payload.items()
                                  if key not in ('code', 'description', 'applicability')}
    result['metadata_fields'] = [dict(key=key, value=_plain(value)) for key, value in parsed if key != 'code']
    top = [value for key, value in parsed if key == 'code']
    if not top:
        result['errors'].append(dict(code='MISSING_TOP_LEVEL_CODE', message='No top-level code field was supplied.'))
        return result
    first = top[0]
    if any(field['value'] != _plain(first) for field in result['source_fields']):
        result['errors'].append(dict(code='CONFLICTING_CODE_FIELDS',
            message='Different code fields were submitted; no source was selected.',
            paths=[field['path'] for field in result['source_fields']]))
        return result
    if not isinstance(first, str):
        result['errors'].append(dict(code='CODE_NOT_STRING', message='The unique code field is not a string.'))
        return result
    result['code'] = first  # Preserve the decoded Python string exactly, including newlines/whitespace.
    if not first.strip():
        result['errors'].append(dict(code='EMPTY_CODE', message='The code string is empty or whitespace-only.'))
        return result
    try:
        result['code_sha256'] = hashlib.sha256(first.encode('utf-8')).hexdigest()
    except UnicodeEncodeError as error:
        result['errors'].append(dict(code='SOURCE_ENCODING_ERROR', message=str(error)))
        return result
    result['passed'] = True
    return result
