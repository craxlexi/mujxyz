# Run MUJ Pulse on your PC

Install Python 3.12+ and Node.js 22 LTS. Extract the project, open a terminal in its folder, then run:

```sh
python scripts/run_local.py
```

On macOS/Linux, use `python3` if `python` is unavailable. On Windows, `py -3.12 scripts/run_local.py` also works.

The launcher installs dependencies, creates a private local encryption key if needed, starts the API, background worker and frontend, and opens http://localhost:3000. Create an app account, then connect SLCM with your portal username, password and semester. Keep the terminal open; Ctrl+C stops the services. Ports 3000 and 8000 must be free.

The local launcher enables the verified live SLCM connector. The first fetch establishes a baseline; later checks detect changes. Back up `backend/.env` securely if you want to keep access to stored credentials.

To diagnose SLCM from your own PC, run the interactive helper separately:

- Windows: `.venv\Scripts\python backend\verify_slcm.py`
- macOS/Linux: `.venv/bin/python backend/verify_slcm.py`

Enter the password only at the hidden prompt. The command prints a result count and whether official GPA is published. It saves no credentials, cookies, or marks.
