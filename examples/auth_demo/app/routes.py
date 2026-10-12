"""HTTP login endpoint."""

from fastapi import FastAPI, HTTPException

from .auth import authenticate, create_session
from .models import LoginRequest, LoginResponse

app = FastAPI()


@app.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(access_token=create_session(user["id"]))
