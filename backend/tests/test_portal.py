from urllib.parse import parse_qs
from pathlib import Path
from copy import deepcopy

import httpx
import pytest

from app.portal import (SLCMSession, SLCMClient, PortalUnavailable, PortalAuthenticationError,
                        parse_marks_json, merge_grades, parse_official_gpa, parse_marks_table)
from app.changes import diff

# Sanitized structural fixture from the public login form inspected 2026-11-12.
LOGIN = '''<form action="/" id="kt_login_form" method="post">
<input type="hidden" name="__RequestVerificationToken" value="synthetic-token">
<input type="hidden" name="EmailFor"><input type="hidden" name="LoginFor">
<input name="UserName"><input name="Password" type="password"></form>'''


def test_student_login_preserves_csrf_cookie_and_redirect_session():
    requests = []

    def portal(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(200, text=LOGIN, headers={'set-cookie': 'csrf=synthetic; Path=/; Secure'})
        if len(requests) == 2:
            assert 'csrf=synthetic' in request.headers['cookie']
            assert parse_qs(request.content.decode()) == {
                '__RequestVerificationToken': ['synthetic-token'], 'UserName': ['test.student'],
                'Password': ['synthetic-password'], 'EmailFor': ['@muj.manipal.edu'], 'LoginFor': ['2'],
            }
            return httpx.Response(302, headers={'location': '/Student/Home', 'set-cookie': 'auth=synthetic; Path=/; Secure'})
        assert request.method == 'GET'
        assert 'auth=synthetic' in request.headers['cookie']
        assert not request.content
        return httpx.Response(200, text='<nav>synthetic landing</nav>')

    with SLCMSession(httpx.MockTransport(portal)) as session:
        response = session.login({'email': 'test.student@muj.manipal.edu', 'password': 'synthetic-password'})
        assert response.url.path == '/Student/Home'
    assert len(requests) == 3


@pytest.mark.parametrize('location', ['https://evil.example/', 'http://mujslcm.jaipur.manipal.edu/', '//evil.example/', 'https://mujslcm.jaipur.manipal.edu:444/'])
def test_never_forward_credentials_to_unverified_redirect(location):
    requests = []

    def portal(request):
        requests.append(request)
        return httpx.Response(200, text=LOGIN) if request.method == 'GET' else httpx.Response(307, headers={'location': location})

    with SLCMSession(httpx.MockTransport(portal)) as session:
        with pytest.raises(PortalUnavailable):
            session.login({'email': 'test', 'password': 'synthetic-password'})
    assert len(requests) == 2


@pytest.mark.parametrize('html', [LOGIN.replace('action="/"', 'action="https://evil.example/"'),
                                  LOGIN.replace('synthetic-token', ''),
                                  LOGIN + '<input name="otp">',
                                  LOGIN + '<div class="g-recaptcha"></div>'])
def test_changed_form_or_challenge_sends_no_password(html):
    methods = []

    def portal(request):
        methods.append(request.method)
        return httpx.Response(200, text=html)

    with SLCMSession(httpx.MockTransport(portal)) as session:
        with pytest.raises(PortalUnavailable):
            session.login({'email': 'test', 'password': 'synthetic-password'})
    assert methods == ['GET']


def test_login_failure_redacts_portal_message():
    with SLCMSession(httpx.MockTransport(lambda r: httpx.Response(200, text=LOGIN + 'private-student-info'))) as session:
        with pytest.raises(PortalAuthenticationError) as error:
            session.login({'email': 'test', 'password': 'synthetic-password'})
    assert 'private-student-info' not in str(error.value)


def test_redirect_loop_is_bounded():
    calls = []

    def portal(request):
        calls.append(request)
        return httpx.Response(302, headers={'location': '/Home/Logout'})

    with SLCMSession(httpx.MockTransport(portal)) as session:
        with pytest.raises(PortalUnavailable, match='redirect limit'):
            session.request('GET', '/')
    assert len(calls) == 6


def test_timeout_and_denied_access_are_safe():
    def timeout(request):
        raise httpx.ReadTimeout('private upstream detail', request=request)

    with SLCMSession(httpx.MockTransport(timeout)) as session:
        with pytest.raises(PortalUnavailable, match='request failed') as error:
            session.request('GET', '/')
        assert 'private' not in str(error.value)
    with SLCMSession(httpx.MockTransport(lambda r: httpx.Response(403, text='private'))) as session:
        with pytest.raises(PortalAuthenticationError):
            session.request('GET', '/')


@pytest.fixture
def marks():
    # Synthetic values; keys are from the inspected authenticated page script.
    return {'IsSuccessfull': True, 'InternalMarksList': [
        {'CourseID': 'Synthetic Subject (TST0001)', 'MTE1': '20.00', 'MTE2': '-',
         'CWS': '0.00', 'RESESSION': '', 'PRS': None}]}


def test_json_zero_unpublished_and_corrections(marks):
    courses = parse_marks_json(marks)
    assert courses[0]['marks'] == {'MTE 1': '2E+1', 'MTE 2': None, 'CWS': '0', 'RE-SESSION': None, 'PRS': None}
    before = {'courses': courses, 'official_sgpa': None}
    marks['InternalMarksList'][0]['MTE1'] = '19.50'
    after = {'courses': parse_marks_json(marks), 'official_sgpa': None}
    assert diff(before, after) == [{'course': 'TST0001', 'field': 'MTE 1', 'old': '2E+1', 'new': '19.5'}]


@pytest.mark.parametrize('mutation', ['missing_column', 'duplicate', 'nan', 'empty', 'failed', 'missing_identity'])
def test_partial_marks_fail_closed(marks, mutation):
    row = marks['InternalMarksList'][0]
    if mutation == 'missing_column': del row['MTE2']
    if mutation == 'missing_identity': del row['CourseID']
    if mutation == 'duplicate': marks['InternalMarksList'].append(deepcopy(row))
    if mutation == 'nan': row['MTE1'] = 'NaN'
    if mutation == 'empty': marks['InternalMarksList'] = []
    if mutation == 'failed': marks['IsSuccessfull'] = False
    with pytest.raises(PortalUnavailable): parse_marks_json(marks)


def test_grade_publication_and_missing_grade_protection(marks):
    courses = parse_marks_json(marks)
    before = {'courses': deepcopy(courses), 'official_sgpa': None}
    merge_grades(courses, {'IsSuccessfull': True, 'InternalMarksList': [
        {'CourseCode': 'TST0001', 'CourseID': 'Synthetic Subject', 'AcademicSession': 'synthetic', 'Credits': '4.00', 'Grade': 'A+'},
        {'AcademicSession': 'Total', 'Credits': '4.00'}]})
    assert courses[0]['credits'] == '4'
    after = {'courses': courses, 'official_sgpa': None}
    assert diff(before, after) == [{'course': 'TST0001', 'field': 'Grade', 'old': None, 'new': 'A+'},
                                   {'course': 'TST0001', 'field': 'Credits', 'old': None, 'new': '4'}]
    missing_credits = deepcopy(after)
    missing_credits['courses'][0]['credits'] = None
    with pytest.raises(PortalUnavailable, match='credits disappeared'): diff(after, missing_credits)
    missing = parse_marks_json(marks)
    merge_grades(missing, {'IsSuccessfull': False, 'InternalMarksList': []})
    with pytest.raises(PortalUnavailable, match='grade disappeared'):
        diff(after, {'courses': missing, 'official_sgpa': None})
    with pytest.raises(PortalUnavailable):
        merge_grades(missing, {'IsSuccessfull': False, 'InternalMarksList': None})


def test_only_requested_official_semester_gpa_is_used():
    payload = {'IsSuccessfull': True, 'InternalMarksList': [
        {'CGPA': '8.70', 'GPASemesterI': '8.00', 'GPASemesterII': '0.00', 'GPASemesterIII': '-'}]}
    assert parse_official_gpa(payload, 'I') == '8'
    assert parse_official_gpa(payload, 'II') is None
    assert parse_official_gpa(payload, 'III') is None
    with pytest.raises(PortalUnavailable): parse_official_gpa(payload, 'IV')


def test_live_rendered_table_sanitized_fixture():
    html = (Path(__file__).parent / 'fixtures' / 'marks-table.html').read_text()
    courses = parse_marks_table(html)
    assert len(courses) == 6 and courses[0]['code'] == 'TST0001'
    assert courses[0]['marks']['CWS'] == '0'


def test_observed_http_fetch_flow_and_expired_session(marks):
    ajax = []
    expired = False
    academic = '/Student/Academic/'

    def portal(request):
        path = request.url.path
        if path == '/':
            if request.method == 'GET': return httpx.Response(200, text=LOGIN)
            return httpx.Response(302, headers={'location': '/Home/Dashboard', 'set-cookie': 'auth=synthetic; Path=/; Secure'})
        if path == '/Home/Dashboard': return httpx.Response(200, text='<nav>synthetic</nav>')
        assert 'auth=synthetic' in request.headers['cookie']
        if request.method == 'GET':
            assert 'x-requested-with' not in request.headers
            endpoint = {'InternalMarkForStudent': 'GetInternalMarkForFaculty',
                        'GradesForStudent': 'GetGradesForFaculty', 'CGPAGPAForStudent': 'GetCGPAGPAForFaculty'}[path.split('/')[-1]]
            return httpx.Response(200, text='<select name="Semester"><option value="III">III</option></select><script>var url="/'+endpoint+'";</script>')
        assert request.headers['x-requested-with'] == 'XMLHttpRequest'
        assert request.headers['referer'].startswith(SLCMSession.origin + academic)
        ajax.append((path, parse_qs(request.content.decode(), keep_blank_values=True)))
        if expired: return httpx.Response(200, text=LOGIN, headers={'content-type': 'text/html'})
        if path.endswith('GetInternalMarkForFaculty'): return httpx.Response(200, json=marks)
        if path.endswith('GetGradesForFaculty'): return httpx.Response(200, json={'IsSuccessfull': False, 'InternalMarksList': []})
        return httpx.Response(200, json={'IsSuccessfull': True, 'InternalMarksList': [{'GPASemesterIII': '0.00'}]})

    client = SLCMClient(lambda: SLCMSession(httpx.MockTransport(portal)))
    result = client.fetch({'email': 'synthetic', 'password': 'synthetic'}, 3)
    assert result['complete'] and len(result['courses']) == 1 and result['official_sgpa'] is None
    assert ajax == [(academic + 'GetInternalMarkForFaculty', {'Enrollment': [''], 'Semester': ['III']}),
                    (academic + 'GetGradesForFaculty', {'Enrollment': [''], 'Semester': ['III']}),
                    (academic + 'GetCGPAGPAForFaculty', {'Enrollment': [''], 'AcademicYear': [''], 'ProgramCode': ['']})]
    expired = True
    with pytest.raises(PortalAuthenticationError, match='expired'): client.fetch({'email': 'synthetic', 'password': 'synthetic'}, 3)


def test_unavailable_semester_never_requests_results(marks):
    calls = []

    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def login(self, credentials): pass
        def request(self, *args):
            calls.append(args)
            return httpx.Response(200, text='<select name="Semester"><option value="I">I</option></select><script>"/GetInternalMarkForFaculty"</script>')
        def json(self, *args): raise AssertionError('Unavailable semester must not be fetched')

    with pytest.raises(PortalUnavailable, match='not available'):
        SLCMClient(Session).fetch({'email': 'synthetic', 'password': 'synthetic'}, 3)
    assert len(calls) == 1
