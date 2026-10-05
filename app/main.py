import os
import secrets
from typing import Any

import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates


APP_NAME = "IP Cycler Admin"
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")

app = FastAPI(title=APP_NAME)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET or "CHANGE-ME-BEFORE-DEPLOY",
    session_cookie="ipcycler_admin",
    max_age=60 * 60 * 12,
    https_only=True,
    same_site="strict",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

_firebase_ready = False
_firebase_error = ""


def init_firebase() -> None:
    global _firebase_ready, _firebase_error
    if _firebase_ready:
        return

    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").strip().replace("\\n", "\n")

    if not all([project_id, client_email, private_key, FIREBASE_DATABASE_URL]):
        _firebase_error = "Firebase environment variables are not configured."
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            firebase_admin.initialize_app(cred, {
                "databaseURL": FIREBASE_DATABASE_URL,
            })
        _firebase_ready = True
        _firebase_error = ""
    except Exception as exc:
        _firebase_error = f"Firebase initialization failed: {exc}"


@app.on_event("startup")
def startup() -> None:
    init_firebase()


def require_admin(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/login", status_code=303)
    return None


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


def check_csrf(request: Request, token: str) -> bool:
    expected = request.session.get("csrf", "")
    return bool(expected and token and secrets.compare_digest(expected, token))


def firebase_root() -> Any:
    init_firebase()
    if not _firebase_ready:
        raise RuntimeError(_firebase_error or "Firebase is not ready")
    return db.reference("/")


def get_devices() -> list[dict[str, Any]]:
    data = firebase_root().child("config").child("devices").get() or {}
    result = []
    for device_id, value in data.items():
        value = value or {}
        result.append({
            "id": device_id,
            "status": value.get("status", "unknown"),
            "uid": value.get("uid", device_id),
        })
    result.sort(key=lambda x: x["id"].lower())
    return result


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("admin"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "", "csrf": csrf_token(request)},
    )


@app.post("/login")
def login(request: Request, password: str = Form(...), csrf: str = Form(...)):
    if not check_csrf(request, csrf):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid session. Refresh and try again.", "csrf": csrf_token(request)},
            status_code=400,
        )
    if not ADMIN_PASSWORD:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "ADMIN_PASSWORD is not configured on the server.", "csrf": csrf_token(request)},
            status_code=500,
        )
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect password.", "csrf": csrf_token(request)},
            status_code=401,
        )
    request.session.clear()
    request.session["admin"] = True
    request.session["csrf"] = secrets.token_urlsafe(32)
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request, csrf: str = Form(...)):
    if check_csrf(request, csrf):
        request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    redirect = require_admin(request)
    if redirect:
        return redirect

    init_firebase()
    enabled = False
    devices = []
    error = _firebase_error

    if _firebase_ready:
        try:
            root = firebase_root()
            enabled = bool(root.child("config").child("enabled").get())
            devices = get_devices()
        except Exception as exc:
            error = str(exc)

    counts = {
        "total": len(devices),
        "approved": sum(d["status"] == "approved" for d in devices),
        "pending": sum(d["status"] == "pending" for d in devices),
        "disabled": sum(d["status"] == "disabled" for d in devices),
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "enabled": enabled,
            "devices": devices,
            "counts": counts,
            "error": error,
            "csrf": csrf_token(request),
        },
    )


@app.post("/global")
def global_toggle(request: Request, enabled: str = Form(...), csrf: str = Form(...)):
    redirect = require_admin(request)
    if redirect:
        return redirect
    if not check_csrf(request, csrf):
        return RedirectResponse("/", status_code=303)

    try:
        firebase_root().child("config").child("enabled").set(enabled == "true")
    except Exception:
        pass
    return RedirectResponse("/", status_code=303)


@app.post("/device/{device_id}")
def device_action(
    request: Request,
    device_id: str,
    action: str = Form(...),
    csrf: str = Form(...),
):
    redirect = require_admin(request)
    if redirect:
        return redirect
    if not check_csrf(request, csrf):
        return RedirectResponse("/", status_code=303)

    if action not in {"approve", "disable", "delete"}:
        return RedirectResponse("/", status_code=303)

    try:
        ref = firebase_root().child("config").child("devices").child(device_id)
        if action == "approve":
            ref.child("status").set("approved")
        elif action == "disable":
            ref.child("status").set("disabled")
        elif action == "delete":
            ref.delete()
    except Exception:
        pass

    return RedirectResponse("/", status_code=303)
