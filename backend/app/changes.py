import json
import time
import uuid
from contextlib import nullcontext
from decimal import Decimal
from .db import db
from .portal import PortalUnavailable


def validate_snapshot(snapshot: dict):
    courses = snapshot.get('courses', [])
    if snapshot.get('complete') is not True or not courses:
        raise PortalUnavailable('Incomplete result; previous snapshot preserved')
    if len({c['code'] for c in courses}) != len(courses):
        raise PortalUnavailable('Duplicate courses')
    for course in courses:
        if not course.get('code') or not isinstance(course.get('marks'), dict):
            raise PortalUnavailable('Invalid course record')
        for value in course['marks'].values():
            if value is not None and (not Decimal(str(value)).is_finite() or Decimal(str(value)) < 0):
                raise PortalUnavailable('Invalid mark')


def equivalent(left, right):
    if left is None or right is None:
        return left is right
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except Exception:
        return left == right


def diff(old: dict, new: dict) -> list[dict]:
    changes = []
    previous = {c['code']: c for c in old['courses']}
    current = {c['code']: c for c in new['courses']}
    # Deletions often indicate incomplete portal responses. Require investigation.
    if previous.keys() - current.keys():
        raise PortalUnavailable('Courses disappeared; previous snapshot preserved')
    for code, course in current.items():
        before = previous.get(code)
        if before is None:
            changes.append({'course': code, 'field': 'Course added', 'old': None, 'new': course['name']})
            continue
        if before['marks'].keys() - course['marks'].keys():
            raise PortalUnavailable('Assessment columns disappeared')
        for field, value in course['marks'].items():
            prior = before['marks'].get(field)
            if prior is not None and value is None:
                raise PortalUnavailable('Published mark disappeared; previous snapshot preserved')
            if not equivalent(prior, value):
                changes.append({'course': code, 'field': field, 'old': prior, 'new': value})
        if before.get('grade') is not None and course.get('grade') is None:
            raise PortalUnavailable('Published grade disappeared')
        if before.get('grade') != course.get('grade'):
            changes.append({'course': code, 'field': 'Grade', 'old': before.get('grade'), 'new': course.get('grade')})
        if before.get('credits') is not None and course.get('credits') is None:
            raise PortalUnavailable('Published credits disappeared')
        if not equivalent(before.get('credits'), course.get('credits')):
            changes.append({'course': code, 'field': 'Credits', 'old': before.get('credits'), 'new': course.get('credits')})
    if old.get('official_sgpa') is not None and new.get('official_sgpa') is None:
        raise PortalUnavailable('Published SGPA disappeared')
    if not equivalent(old.get('official_sgpa'), new.get('official_sgpa')):
        changes.append({'course': 'Semester', 'field': 'Official SGPA', 'old': old.get('official_sgpa'), 'new': new.get('official_sgpa')})
    return changes


def save_snapshot(user_id: str, semester: int, snapshot: dict, require_account=False, connection=None) -> list[dict]:
    validate_snapshot(snapshot)
    now = time.time()
    with (nullcontext(connection) if connection is not None else db()) as conn:
        if connection is None:
            conn.execute('BEGIN IMMEDIATE')
        if require_account:
            account = conn.execute('SELECT semester FROM accounts WHERE user_id=?', (user_id,)).fetchone()
            if not account or account['semester'] != semester:
                return []  # Disconnected or changed semester while the request was in flight.
        old = conn.execute('SELECT payload FROM snapshots WHERE user_id=? AND semester=?', (user_id, semester)).fetchone()
        changes = diff(json.loads(old['payload']), snapshot) if old else []
        conn.execute('INSERT INTO snapshots VALUES(?,?,?,?) ON CONFLICT(user_id,semester) DO UPDATE SET payload=excluded.payload,updated=excluded.updated', (user_id, semester, json.dumps(snapshot), now))
        if changes:
            event_id = uuid.uuid4().hex
            conn.execute('INSERT INTO events VALUES(?,?,?,?,?)', (event_id, user_id, semester, json.dumps(changes), now))
            for sub in conn.execute('SELECT id FROM subscriptions WHERE user_id=?', (user_id,)):
                conn.execute('INSERT INTO deliveries(id,event_id,subscription_id,next_attempt) VALUES(?,?,?,?)', (uuid.uuid4().hex, event_id, sub['id'], now))
    return changes
