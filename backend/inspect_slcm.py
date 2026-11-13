"""Run interactively in the cloud Terminal; secrets never appear in command arguments.

Private responses are kept only in a mode-0700 temporary directory for local
inspection, outside Git. Passwords and cookies are not written to disk.
"""
import getpass
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from app.portal import SLCMSession, PortalUnavailable


def describe(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return {
        'path': urlsplit(str(response.url)).path,
        'forms': [{'method': f.get('method'), 'action': urlsplit(f.get('action', '')).path,
                   'fields': [{'tag': e.name, 'name': e.get('name'), 'id': e.get('id'), 'type': e.get('type')}
                              for e in f.select('input,select,button')]} for f in soup.find_all('form')],
        'selects': [{'id': s.get('id'), 'name': s.get('name'), 'option_count': len(s.find_all('option'))}
                    for s in soup.find_all('select')],
        'table_headers': [[c.get_text(' ', strip=True) for c in t.select('th')] for t in soup.find_all('table')],
        'academic_links': sorted({urlsplit(a['href']).path for a in soup.select('a[href]')
                                  if '/Academic/' in a['href']}),
        'scripts': [urlsplit(s['src']).path for s in soup.select('script[src]')],
    }


def main():
    username = input('SLCM student username or MUJ email: ').strip()
    password = getpass.getpass('SLCM password (hidden): ')
    try:
        with SLCMSession() as session:
            landing = session.login({'email': username, 'password': password})
            password = ''
            marks = session.request('GET', '/Student/Academic/InternalMarkForStudent')
            if BeautifulSoup(marks.text, 'html.parser').find('form', id='kt_login_form'):
                raise PortalUnavailable('SLCM returned the login form; authentication was not verified')
            folder = Path(tempfile.mkdtemp(prefix='slcm-private-'))
            for name, response in [('landing', landing), ('marks', marks)]:
                path = folder / (name + '.html')
                path.touch(mode=0o600)
                path.write_text(response.text)
            report = folder / 'structure.json'
            report.touch(mode=0o600)
            report.write_text(json.dumps({'landing': describe(landing), 'marks': describe(marks)}, indent=2))
            print('Inspection completed. Private local directory:', folder)
            print('Password and cookies were not saved. Reply "inspection complete" in chat.')
    except PortalUnavailable as exc:
        print(str(exc))
    finally:
        password = ''


if __name__ == '__main__':
    if not os.isatty(0):
        raise SystemExit('Run in the interactive Terminal so password input stays hidden.')
    main()
