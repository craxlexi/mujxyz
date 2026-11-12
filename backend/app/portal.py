"""Portal boundary. No unverified SLCM login selectors or endpoints are assumed."""
import re
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup

class PortalUnavailable(Exception):
    pass

class SLCMClient:
    enabled = False

    def fetch(self, credentials: dict, semester: int) -> dict:
        raise PortalUnavailable('Live SLCM integration awaits verification of login, semester selection and grade endpoints. No credentials were sent.')


def parse_marks_table(html: str) -> list[dict]:
    """Parse the table format supplied by the user; fail closed on missing/partial rows.

    This parser is fixture-tested, not a claim that the live response was inspected.
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
