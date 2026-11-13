"""Show safe browser login request details without saving passwords or cookies.

Run on your PC with Playwright installed. Enter credentials in the opened Chrome
window yourself; this script never types or prints them.
"""
import getpass
import hmac
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def main():
    captured = []
    browser_password = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=False)
        context = browser.new_context()
        page = context.new_page()

        def observe(request):
            if request.method != 'POST' or urlsplit(request.url).hostname != 'mujslcm.jaipur.manipal.edu':
                return
            fields = parse_qs(request.post_data or '', keep_blank_values=True)
            if fields.get('Password'):
                browser_password.append(fields['Password'][0])
            headers = request.headers
            captured.append({
                'path': urlsplit(request.url).path,
                'fields': sorted(fields),
                'LoginFor': fields.get('LoginFor', [''])[0],
                'EmailFor': fields.get('EmailFor', [''])[0],
                'username_has_domain': '@' in fields.get('UserName', [''])[0],
                'password_present': bool(fields.get('Password', [''])[0]),
                'csrf_present': bool(fields.get('__RequestVerificationToken', [''])[0]),
                'headers': {key: headers.get(key, '') for key in ('accept', 'content-type', 'origin', 'referer', 'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site', 'sec-fetch-user', 'user-agent')},
            })

        context.on('request', observe)
        page.goto('https://mujslcm.jaipur.manipal.edu/', wait_until='domcontentloaded')
        print('Sign in within this Chrome window. The trace stops when the dashboard loads.')
        try:
            page.wait_for_url('**/Home/Dashboard', wait_until='domcontentloaded', timeout=120000)
        except PlaywrightTimeout:
            print('Dashboard did not load within two minutes.')
        login = next((item for item in captured if item['password_present']), None)
        if login:
            terminal_password = getpass.getpass('Enter the same password once more in this terminal (hidden): ')
            login['password_matches_terminal'] = hmac.compare_digest(browser_password[-1], terminal_password)
            terminal_password = ''
            browser_password.clear()
            print(login)
        else:
            print({'login_form_visible_at_end': page.locator('#kt_login_form').count() > 0, 'end_path': urlsplit(page.url).path, 'post_paths': [item['path'] for item in captured[:8]]})
        browser.close()


if __name__ == '__main__':
    main()
