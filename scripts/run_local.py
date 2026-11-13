"""Start MUJ Pulse on Windows, macOS, or Linux: python scripts/run_local.py."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]

def ensure_local_key(python, local_config):
    settings = local_config.read_text(encoding='utf-8').splitlines() if local_config.exists() else []
    keys = [line.split('=', 1)[1].strip() for line in settings if line.strip().startswith('ENCRYPTION_KEY=')]
    if keys and keys[-1]:
        return
    key = subprocess.check_output(
        [str(python), '-c', 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'],
        text=True,
    ).strip()
    with local_config.open('a', encoding='utf-8') as file:
        file.write('\nENCRYPTION_KEY=' + key + '\n')
    print('Created a local encryption key in backend/.env. Keep this file private and backed up.')

def main():
    if sys.version_info < (3, 12):
        raise SystemExit('Install Python 3.12 or newer, then run this command again.')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm:
        raise SystemExit('Install Node.js 22 LTS, then reopen your terminal and try again.')
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'backend/requirements.txt')], check=True)
    ensure_local_key(python, ROOT / 'backend/.env')
    npm_command = [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/c', npm] if os.name == 'nt' else [npm]
    subprocess.run(npm_command + ['ci', '--no-audit', '--no-fund'], cwd=ROOT / 'frontend', check=True)
    env = dict(os.environ, APP_ORIGIN='http://localhost:3000', API_ORIGIN='http://127.0.0.1:8000', SECURE_COOKIES='false', DEMO_ENABLED='false', PORTAL_ENABLED='true')
    processes = []
    try:
        for args, folder in [
            ([str(python), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], 'backend'),
            ([str(python), '-m', 'app.worker'], 'backend'),
            ([shutil.which('node'), str(ROOT / 'frontend/node_modules/next/dist/bin/next'), 'dev', '--hostname', '127.0.0.1', '--port', '3000'], 'frontend'),
        ]:
            processes.append(subprocess.Popen(args, cwd=ROOT / folder, env=env))
        for _ in range(90):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError('A service exited. Check the output above; ports 3000 and 8000 must be free.')
            try:
                with urllib.request.urlopen('http://localhost:3000/api/health', timeout=2) as response:
                    if response.status == 200:
                        webbrowser.open('http://localhost:3000')
                        print('\nMUJ Pulse: http://localhost:3000 — sign in and connect SLCM. Ctrl+C stops all services.\n')
                        break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError('Startup timed out. Check the service output above.')
        while all(p.poll() is None for p in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    p.terminate()
        for p in processes:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()

if __name__ == '__main__':
    main()
