# Authentication module onboarding: login errors

## Your assigned task

Help a new developer update login error handling in the authentication module

## Module overview

The login route checks credentials and returns a signed session token on success. [app/routes.py:11](app/routes.py#L11) [app/routes.py:13](app/routes.py#L13) [app/routes.py:16](app/routes.py#L16)

## Relevant files

- **app/routes.py** — Defines the HTTP login handler and its 401 response. Change the client-visible error here [app/routes.py:11](app/routes.py#L11)
- **app/auth.py** — Verifies passwords and creates session tokens. Check the failure result before changing error handling [app/auth.py:15](app/auth.py#L15)
- **app/models.py** — Defines request and response models. Confirm the current login response shape [app/models.py:4](app/models.py#L4)
- **app/db.py** — Looks up demo users from an in-memory table. Understand where the credential check gets its record [app/db.py:6](app/db.py#L6)
- **tests/test_auth.py** — Tests credential and session behavior. Extend coverage for the desired error behavior [tests/test_auth.py:4](tests/test_auth.py#L4)
- **README.md** — Documents local setup. Use these commands to run the demo [README.md:6](README.md#L6)

## How the flow works

- POST /login receives a LoginRequest and passes its username and password to authenticate. [app/routes.py:11](app/routes.py#L11) [app/routes.py:12](app/routes.py#L12) [app/routes.py:13](app/routes.py#L13)
- authenticate looks up the user, compares the supplied password hash, and returns None on failure. [app/auth.py:15](app/auth.py#L15) [app/auth.py:16](app/auth.py#L16) [app/auth.py:17](app/auth.py#L17) [app/auth.py:18](app/auth.py#L18)
- The route raises HTTP 401 for None and otherwise returns a LoginResponse with a session token. [app/routes.py:14](app/routes.py#L14) [app/routes.py:15](app/routes.py#L15) [app/routes.py:16](app/routes.py#L16)

## API dependencies

- The handler is registered as POST /login with LoginResponse as its response model. [app/routes.py:11](app/routes.py#L11)
- LoginRequest requires username and password; LoginResponse includes access_token and bearer token_type. [app/models.py:4](app/models.py#L4) [app/models.py:5](app/models.py#L5) [app/models.py:6](app/models.py#L6) [app/models.py:9](app/models.py#L9) [app/models.py:10](app/models.py#L10) [app/models.py:11](app/models.py#L11)

## Database relationships

- The demo stores users in a Python dictionary and get_user performs a username lookup. [app/db.py:1](app/db.py#L1) [app/db.py:3](app/db.py#L3) [app/db.py:6](app/db.py#L6) [app/db.py:7](app/db.py#L7)

## Important conventions

- Authentication failures return None from authenticate and become HTTP 401 in the route. [app/auth.py:17](app/auth.py#L17) [app/auth.py:18](app/auth.py#L18) [app/routes.py:14](app/routes.py#L14) [app/routes.py:15](app/routes.py#L15)
- Session signing reads SESSION_SECRET from the environment. [app/auth.py:22](app/auth.py#L22) [app/auth.py:23](app/auth.py#L23) [app/auth.py:25](app/auth.py#L25)

## Local setup

- Create a Python 3.11 environment and install requirements with pip. [README.md:8](README.md#L8) [README.md:9](README.md#L9)
- Set SESSION_SECRET, run uvicorn app.routes:app --reload, then run pytest. [README.md:10](README.md#L10) [README.md:11](README.md#L11) [README.md:12](README.md#L12)

## First steps for this task

- Inspect the route 401 response and the None branch in authenticate before editing the error behavior. [app/routes.py:14](app/routes.py#L14) [app/routes.py:15](app/routes.py#L15) [app/auth.py:17](app/auth.py#L17) [app/auth.py:18](app/auth.py#L18)
- Extend the existing authentication tests for the chosen behavior. [tests/test_auth.py:4](tests/test_auth.py#L4) [tests/test_auth.py:8](tests/test_auth.py#L8)

## Unknowns to confirm

- The selected files do not describe the desired replacement error wording or whether the response shape may change. Confirm those requirements with the task owner.
