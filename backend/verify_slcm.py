"""Private end-to-end check of SLCM login and result fetching."""
import getpass
from app.portal import SLCMClient, PortalUnavailable


def main():
    username = input('SLCM student username or MUJ email: ').strip()
    semester = int(input('Semester number (1-10): '))
    password = getpass.getpass('SLCM password (hidden): ')
    try:
        snapshot = SLCMClient().fetch({'email': username, 'password': password}, semester)
        print(f"Verified: {len(snapshot['courses'])} courses; official GPA published: {snapshot['official_sgpa'] is not None}")
    except PortalUnavailable as exc:
        print(f'Verification failed: {exc}')
    finally:
        password = ''


if __name__ == '__main__':
    main()
