import pytest
from decimal import Decimal
from app.portal import parse_student_name, parse_marks_json


@pytest.mark.parametrize('html,expected', [
    ('<input id="StudentName" value="  Aanya   Sharma  ">', 'Aanya Sharma'),
    ('<span data-student-name="अदिति शर्मा"></span>', 'अदिति शर्मा'),
    ('<div id="studentName">Aanya Sharma</div>', 'Aanya Sharma'),
    ('<h1>Welcome back</h1><p>student@example.test</p>', None),
    ('<input name="StudentName" value="student@example.test">', None),
    ('<input name="StudentName" value="12345">', None),
])
def test_only_explicit_student_identity(html, expected):
    assert parse_student_name(html) == expected


def test_optional_ete_does_not_change_existing_assessments():
    row = {'CourseID': 'Mathematics (MA2101)', 'MTE1': 18, 'MTE2': None,
           'CWS': 20, 'RESESSION': None, 'PRS': None, 'ETE': 40}
    course = parse_marks_json({'IsSuccessfull': True, 'InternalMarksList': [row]})[0]
    assert Decimal(course['marks']['ETE']) == 40
    assert course['marks']['MTE 1'] == '18'
