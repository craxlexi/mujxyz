"""SLCM transport and parsing. Live polling stays gated until authenticated verification."""
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit
import httpx
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from . import config

class PortalUnavailable(Exception):
    pass

class PortalAuthenticationError(PortalUnavailable):
    pass


class SLCMSession:
    """Short-lived cookie session; never persist or log portal responses/cookies.

    Student login fields verified against a successful browser login on 2026-11-13.
    Redirects are followed manually so credentials cannot cross origins.
    """
    origin = 'https://mujslcm.jaipur.manipal.edu'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'

    def __init__(self, transport=None):
        self.mock_transport = transport is not None
        if self.mock_transport:
            self.client = httpx.Client(
                headers={'User-Agent': self.user_agent},
                timeout=httpx.Timeout(20, connect=10), verify=True,
                follow_redirects=False, transport=transport,
            )
        else:
            # SLCM rejects the same valid login over HTTPX but accepts Chrome's
            # network fingerprint. Keep browser-like transport for live requests.
            self.client = curl_requests.Session(impersonate='chrome',
                                                headers={'User-Agent': self.user_agent})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def url(self, target):
        url = urljoin(self.origin + '/', str(target))
        parts = urlsplit(url)
        if (parts.scheme != 'https' or parts.hostname != 'mujslcm.jaipur.manipal.edu'
                or parts.port not in (None, 443) or parts.username or parts.password):
            raise PortalUnavailable('Unexpected portal destination')
        return url

    def request(self, method, target, data=None, headers=None):
        url = self.url(target)
        try:
            for _ in range(6):
                options = {} if self.mock_transport else {'allow_redirects': False, 'timeout': 20, 'verify': True}
                with self.client.stream(method, url, data=data, headers=headers, **options) as response:
                    body = bytearray()
                    chunks = response.iter_bytes() if self.mock_transport else response.iter_content()
                    for chunk in chunks:
                        body.extend(chunk)
                        if len(body) > 2_000_000:
                            raise PortalUnavailable('Portal response too large')
                    result = httpx.Response(response.status_code, headers=response.headers,
                                            content=bytes(body), request=httpx.Request(method, url))
                if result.status_code in (301, 302, 303, 307, 308):
                    location = result.headers.get('location')
                    if not location:
                        raise PortalUnavailable('Portal redirect missing destination')
                    url = self.url(urljoin(url, location))
                    if result.status_code == 303 or (method == 'POST' and result.status_code in (301, 302)):
                        method, data = 'GET', None
                    continue
                if result.status_code in (401, 403):
                    raise PortalAuthenticationError('Portal access denied; sign in through SLCM to check your account')
                result.raise_for_status()
                return result
        except (httpx.HTTPError, curl_requests.exceptions.RequestException):
            raise PortalUnavailable('Portal request failed; try again later') from None
        raise PortalUnavailable('Portal redirect limit reached')

    def json(self, target, data, referer):
        # The inspected pages send form-encoded jQuery POSTs, not JSON bodies.
        headers = {'Origin': self.origin, 'Referer': self.url(referer),
                   'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
        response = self.request('POST', target, data=data, headers=headers)
        if 'application/json' not in response.headers.get('content-type', '').lower():
            raise PortalAuthenticationError('SLCM session expired or returned an unexpected page')
        try:
            payload = response.json()
        except ValueError:
            raise PortalUnavailable('Invalid portal response; saved results preserved') from None
        if not isinstance(payload, dict):
            raise PortalUnavailable('Unexpected portal response format')
        return payload

    def login(self, credentials):
        username = credentials.get('email', '').strip()
        if username.lower().endswith('@muj.manipal.edu'):
            username = username[:-len('@muj.manipal.edu')]
        if not username or '@' in username or not credentials.get('password'):
            raise PortalAuthenticationError('Use your MUJ student username or @muj.manipal.edu address')
        page = self.request('GET', '/')
        soup = BeautifulSoup(page.text, 'html.parser')
        form = soup.find('form', id='kt_login_form')
        if not form or form.get('method', '').lower() != 'post':
            raise PortalUnavailable('SLCM login form changed')
        action = self.url(urljoin(str(page.url), form.get('action', '')))
        if urlsplit(action).path != '/':
            raise PortalUnavailable('SLCM login action changed')
        if soup.select('[name*="captcha" i], [name*="otp" i], .g-recaptcha, .h-captcha'):
            raise PortalAuthenticationError('Complete the authentication challenge on SLCM')
        fields = {field['name']: field.get('value', '') for field in form.select('input[type="hidden"][name]')}
        if not fields.get('__RequestVerificationToken') or not form.select_one('input[name="UserName"]') or not form.select_one('input[name="Password"]'):
            raise PortalUnavailable('SLCM login fields changed')
        fields.update(UserName=username, Password=credentials['password'], LoginFor='2', EmailFor='@muj.manipal.edu')
        response = self.request('POST', action, data=fields,
                                headers={'Origin': self.origin, 'Referer': str(page.url)})
        result = BeautifulSoup(response.text, 'html.parser')
        if result.select('[name*="captcha" i], [name*="otp" i], .g-recaptcha, .h-captcha'):
            raise PortalAuthenticationError('Complete the authentication challenge on SLCM')
        if result.find('form', id='kt_login_form'):
            raise PortalAuthenticationError('SLCM sign-in failed; check your credentials on the portal')
        # A non-login response alone is not proof of successful authentication.
        # The authenticated marks flow must be verified before enabling polling.
        return response


class SLCMClient:
    # Gate API connections until HTTP authentication and real JSON are verified.
    enabled = config.PORTAL_ENABLED
    academic = '/Student/Academic'

    def __init__(self, session_factory=SLCMSession):
        self.session_factory = session_factory

    def fetch(self, credentials: dict, semester: int) -> dict:
        roman = semester_value(semester)
        with self.session_factory() as session:
            session.login(credentials)
            marks_page = self.academic + '/InternalMarkForStudent'
            page = session.request('GET', marks_page)
            self.check_page(page.text, roman, '/GetInternalMarkForFaculty')
            marks = session.json(self.academic + '/GetInternalMarkForFaculty',
                                 {'Enrollment': '', 'Semester': roman}, marks_page)
            courses = parse_marks_json(marks)

            grades_page = self.academic + '/GradesForStudent'
            page = session.request('GET', grades_page)
            self.check_page(page.text, roman, '/GetGradesForFaculty')
            grades = session.json(self.academic + '/GetGradesForFaculty',
                                  {'Enrollment': '', 'Semester': roman}, grades_page)
            merge_grades(courses, grades)

            gpa_page = self.academic + '/CGPAGPAForStudent'
            page = session.request('GET', gpa_page)
            self.check_page(page.text, None, '/GetCGPAGPAForFaculty')
            gpa = session.json(self.academic + '/GetCGPAGPAForFaculty',
                               {'Enrollment': '', 'AcademicYear': '', 'ProgramCode': ''}, gpa_page)
            attendance = timetable = None
            try:
                page = session.request('GET', self.academic + '/AttendanceSummaryForStudent')
                payload = session.json(self.academic + '/GetAttendanceSummaryList',
                                       {'StudentCode': ''}, self.academic + '/AttendanceSummaryForStudent')
                attendance = parse_attendance(payload)
            except (PortalUnavailable, ValueError, KeyError, TypeError):
                pass  # Optional portal data must never block saved marks.
            try:
                from datetime import datetime
                from zoneinfo import ZoneInfo
                today = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d')
                page = session.request('GET', self.academic + '/ViewTimeTableForStudent')
                response = session.request('POST', self.academic + '/GetStudentCalenderEventList',
                    data={'Year': '', 'Month': '', 'Type': 'agendaWeek', 'Dated': today, 'PreNext': '2'},
                    headers={'Origin': session.origin, 'Referer': session.url(self.academic + '/ViewTimeTableForStudent'),
                             'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})
                if 'application/json' not in response.headers.get('content-type', '').lower():
                    raise PortalUnavailable('Unexpected timetable response')
                timetable = parse_timetable(response.json())
            except (PortalUnavailable, ValueError, KeyError, TypeError):
                pass
            return {'courses': courses, 'official_sgpa': parse_official_gpa(gpa, roman),
                    'attendance': attendance, 'timetable': timetable, 'complete': True}

    @staticmethod
    def check_page(html, semester, endpoint):
        soup = BeautifulSoup(html, 'html.parser')
        if soup.find('form', id='kt_login_form'):
            raise PortalAuthenticationError('SLCM session expired; sign in again')
        if endpoint not in '\n'.join(s.get_text() for s in soup.find_all('script', src=False)):
            raise PortalUnavailable('SLCM academic page changed')
        if semester is not None:
            selector = soup.select_one('select[name="Semester"]')
            if not selector or semester not in {o.get('value') for o in selector.find_all('option')}:
                raise PortalUnavailable('Selected semester is not available on SLCM')


def semester_value(semester):
    values = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X')
    if type(semester) is not int or not 1 <= semester <= len(values):
        raise PortalUnavailable('SLCM supports semesters 1 through 10')
    return values[semester - 1]


def parse_attendance(payload):
    rows = payload.get('AttendanceSummaryList') if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) > 100:
        raise PortalUnavailable('Unexpected attendance response')
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('CourseID'), str):
            raise PortalUnavailable('Incomplete attendance row')
        course = row['CourseID'].strip()
        if not course:
            raise PortalUnavailable('Empty attendance course')
        try:
            total, present = int(row['Total']), int(row['Present'])
        except (TypeError, ValueError, KeyError):
            raise PortalUnavailable('Invalid attendance count') from None
        if total < 0 or present < 0 or present > total:
            raise PortalUnavailable('Invalid attendance count')
        code, separator, name = course.partition(':')
        result.append({'code': code.strip() if separator else '', 'name': name.strip() if separator else course,
                       'present': present, 'total': total, 'percentage': round(100 * present / total, 1) if total else None})
    return result


def parse_timetable(payload):
    if not isinstance(payload, list) or len(payload) > 200:
        raise PortalUnavailable('Unexpected timetable response')
    result = []
    for row in payload:
        if not isinstance(row, dict) or not isinstance(row.get('StartDate'), str) or not isinstance(row.get('Description'), str):
            raise PortalUnavailable('Incomplete timetable event')
        start = row['StartDate'].strip()
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?', start):
            raise PortalUnavailable('Invalid timetable date')
        description = row['Description'].strip()
        if not description or len(description) > 500:
            raise PortalUnavailable('Invalid timetable description')
        result.append({'start': start, 'description': description})
    return sorted(result, key=lambda item: item['start'])


def portal_rows(payload, allow_unpublished=False):
    if not isinstance(payload, dict) or type(payload.get('IsSuccessfull')) is not bool:
        raise PortalUnavailable('Unrecognized academic response')
    rows = payload.get('InternalMarksList')
    if payload['IsSuccessfull'] is False:
        if allow_unpublished and rows == []:
            return []
        raise PortalUnavailable('SLCM did not return complete results')
    if not isinstance(rows, list) or len(rows) > 300 or any(not isinstance(r, dict) for r in rows):
        raise PortalUnavailable('Incomplete academic response')
    return rows


def portal_number(value):
    if value is None or (isinstance(value, str) and value.strip() in ('', '-', '—')):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise PortalUnavailable('Invalid academic value')
    try:
        number = Decimal(str(value).strip())
        if not number.is_finite() or number < 0:
            raise InvalidOperation
        return str(number.normalize())
    except InvalidOperation:
        raise PortalUnavailable('Unrecognized academic value') from None


def parse_marks_json(payload):
    rows = portal_rows(payload)
    courses = []
    columns = {'MTE1': 'MTE 1', 'MTE2': 'MTE 2', 'CWS': 'CWS', 'RESESSION': 'RE-SESSION', 'PRS': 'PRS'}
    for row in rows:
        identity = row.get('CourseID')
        match = re.fullmatch(r'(.+?)\s*\(([A-Za-z0-9]+)\)', identity.strip()) if isinstance(identity, str) else None
        if not match or not columns.keys() <= row.keys():
            raise PortalUnavailable('Incomplete course or assessment record')
        courses.append({'code': match[2].upper(), 'name': match[1].strip(),
                        'marks': {label: portal_number(row[key]) for key, label in columns.items()},
                        'grade': None, 'credits': None})
    if not courses or len({c['code'] for c in courses}) != len(courses):
        raise PortalUnavailable('Empty or duplicate course records')
    return courses


def merge_grades(courses, payload):
    rows = portal_rows(payload, allow_unpublished=True)
    by_code = {c['code']: c for c in courses}
    seen = set()
    for row in rows:
        if row.get('AcademicSession') == 'Total':
            continue  # Summary row is not a course or a semester GPA.
        if not {'CourseCode', 'CourseID', 'AcademicSession', 'Credits', 'Grade'} <= row.keys():
            raise PortalUnavailable('Incomplete grade record')
        code = row['CourseCode']
        if not isinstance(code, str) or code.upper().strip() not in by_code or code.upper().strip() in seen:
            raise PortalUnavailable('Grades do not match this semester’s courses')
        code = code.upper().strip()
        seen.add(code)
        grade = row['Grade']
        if grade is not None and not isinstance(grade, str):
            raise PortalUnavailable('Unrecognized grade')
        grade = grade.strip() if grade is not None else None
        if grade in ('', '-', '—'):
            grade = None
        if grade is not None and not re.fullmatch(r'[A-Za-z][A-Za-z0-9+\- ]{0,15}', grade):
            raise PortalUnavailable('Unrecognized grade')
        by_code[code].update(grade=grade, credits=portal_number(row['Credits']))
    # Partial grade publication is allowed. Existing published grades are protected
    # by changes.diff; missing/failed responses never replace a prior publication.


def parse_official_gpa(payload, semester):
    rows = portal_rows(payload, allow_unpublished=True)
    if not rows:
        return None
    if len(rows) != 1:
        raise PortalUnavailable('Ambiguous GPA response')
    key = 'GPASemester' + semester
    if key not in rows[0]:
        raise PortalUnavailable('Semester GPA field missing')
    value = portal_number(rows[0][key])
    # The actual page renders 0.00 as unpublished. Never substitute CGPA for GPA.
    if value is not None and Decimal(value) == 0:
        return None
    if value is not None and Decimal(value) > 10:
        raise PortalUnavailable('Invalid semester GPA')
    return value


def parse_marks_table(html: str) -> list[dict]:
    """Parse the inspected rendered marks table; reject missing/partial rows.

    Live browser markup was verified and copied into a sanitized structural fixture.
    Missing values remain None, distinct from numeric zero.
    """
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if not rows:
            continue
        headers = [re.sub(r'\s+', ' ', c.get_text(' ', strip=True)).upper() for c in rows[0].find_all(['td', 'th'])]
        if 'COURSE NAME' not in headers or 'MTE 1' not in headers:
            continue
        course_index = headers.index('COURSE NAME')
        courses = []
        for row in rows[1:]:
            cells = [c.get_text(' ', strip=True) for c in row.find_all('td')]
            if not cells:
                continue
            if len(cells) != len(headers):
                raise PortalUnavailable('Incomplete marks table; previous snapshot preserved')
            match = re.fullmatch(r'(.+?)\s*\(([A-Za-z0-9]+)\)', cells[course_index])
            if not match:
                raise PortalUnavailable('Unrecognized course identity')
            marks = {}
            for header, value in zip(headers[course_index + 1:], cells[course_index + 1:]):
                if value in ('', '-', '—'):
                    marks[header] = None
                else:
                    try:
                        number = Decimal(value)
                        if not number.is_finite() or number < 0:
                            raise InvalidOperation
                        marks[header] = str(number.normalize())
                    except InvalidOperation as exc:
                        raise PortalUnavailable('Unrecognized assessment value') from exc
            courses.append({'code': match[2].upper(), 'name': match[1].strip(), 'marks': marks, 'grade': None, 'credits': None})
        if not courses or len({c['code'] for c in courses}) != len(courses):
            raise PortalUnavailable('Empty or duplicate course records')
        return courses
    raise PortalUnavailable('Marks table not found; login or response format may have changed')


def demo_snapshot(revision: int = 0) -> dict:
    subjects = [
        ('CSC2102', 'Computer Organization and Architecture', '25'),
        ('CSC2101', 'Data Structures and Algorithms', '21.5'),
        ('CSC2104', 'Object Oriented Programming', '23'),
        ('DOA2099', 'Principles of Management', '27'),
        ('CSC2103', 'Relational Database Management Systems', '26'),
        ('MAS2001', 'Statistics and Probability', '21'),
    ]
    return {'courses': [
        {'code': code, 'name': name, 'marks': {'MTE 1': mark, 'MTE 2': str(22 + revision % 8) if revision and i == 0 else None, 'CWS': None, 'RE-SESSION': None, 'PRS': None}, 'grade': None, 'credits': None}
        for i, (code, name, mark) in enumerate(subjects)
    ], 'official_sgpa': None, 'complete': True}
