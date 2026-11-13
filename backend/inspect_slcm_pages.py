"""Print only the shape of the two authenticated academic pages, never student data."""
import getpass
import os
from pathlib import Path
import re
from bs4 import BeautifulSoup
from app.portal import SLCMSession, PortalUnavailable
from app.db import db
from app.security import decrypt

PAGES = ('AttendanceSummaryForStudent', 'ViewTimeTableForStudent')
ORIGIN = '/Student/Academic/'


def describe(html):
    soup = BeautifulSoup(html, 'html.parser')
    scripts = '\n'.join(tag.get_text() for tag in soup.find_all('script', src=False))
    paths = sorted(set(re.findall(r'["\'](/Student/Academic/[A-Za-z0-9_/]+)["\']', scripts)))
    paths = [path for path in paths if not re.search(r'login|logout|password', path, re.I)]
    selects = sorted({tag.get('name') for tag in soup.select('select[name]') if tag.get('name')})
    tables = []
    for table in soup.find_all('table'):
        headers = [cell.get_text(' ', strip=True) for cell in table.select('thead th')]
        tables.append({'id': table.get('id'), 'headers': headers[:20], 'body_rows': len(table.select('tbody tr'))})
    return {'academic_paths': paths[:30], 'select_names': selects, 'tables': tables[:10]}


def main():
    os.chdir(Path(__file__).resolve().parent)
    with db() as conn:
        rows = conn.execute("SELECT a.credentials FROM accounts a JOIN users u ON u.id=a.user_id WHERE u.is_demo=0 AND a.credentials!=''").fetchall()
    if len(rows) == 1:
        credentials = decrypt(rows[0]['credentials'])
    elif len(rows) > 1:
        print('More than one live account is saved. Enter credentials for the account to inspect.')
        credentials = {'email': input('SLCM username or MUJ email: ').strip(), 'password': getpass.getpass('SLCM password (hidden): ')}
    else:
        print('No live account is saved. Enter credentials for the account to inspect.')
        credentials = {'email': input('SLCM username or MUJ email: ').strip(), 'password': getpass.getpass('SLCM password (hidden): ')}
    try:
        with SLCMSession() as session:
            session.login(credentials)
            for page in PAGES:
                html = session.request('GET', ORIGIN + page).text
                print(page, describe(html))
    except PortalUnavailable as error:
        print('Portal inspection failed:', str(error))
    finally:
        credentials = {}


if __name__ == '__main__':
    main()
