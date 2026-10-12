# Demo authentication service

This small FastAPI app issues a signed session token after a username and password are verified.
The demo login is `ada` / `demo-password`.

## Local setup

1. Create a Python 3.11 virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Set `SESSION_SECRET` in the environment.
4. Start the app with `uvicorn app.routes:app --reload`.
5. Run tests with `pytest`.

The demo uses an in-memory user table in `app/db.py`; replace it with a real data store for production work.
