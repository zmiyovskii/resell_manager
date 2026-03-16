import base64
import hashlib

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

router = APIRouter()


def verify_password(password: str, stored_hash: str) -> bool:
    raw = base64.b64decode(stored_hash.encode("utf-8"))
    salt = raw[:16]
    saved_hash = raw[16:]

    check_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,
    )
    return check_hash == saved_hash


def render_login_page(error_message: str | None = None) -> str:
    error_html = ""
    if error_message:
        error_html = f"""
        <div style="margin-bottom: 16px; padding: 12px; border-radius: 10px; background: #3a1111; color: #ffb4b4; border: 1px solid #7a2a2a;">
            {error_message}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }}
            .card {{
                width: 100%;
                max-width: 380px;
                background: #111827;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 24px;
                box-sizing: border-box;
            }}
            h2 {{
                margin-top: 0;
                margin-bottom: 18px;
            }}
            .field {{
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-bottom: 14px;
            }}
            input {{
                padding: 12px 14px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.12);
                background: #0b1220;
                color: white;
            }}
            button {{
                width: 100%;
                padding: 12px 14px;
                border: none;
                border-radius: 10px;
                background: #2563eb;
                color: white;
                font-weight: 700;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Login</h2>
            {error_html}
            <form method="post" action="/login">
                <div class="field">
                    <label>Username</label>
                    <input name="username" placeholder="Username" required>
                </div>
                <div class="field">
                    <label>Password</label>
                    <input name="password" type="password" placeholder="Password" required>
                </div>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """


@router.get("/login", response_class=HTMLResponse)
def login_page():
    return render_login_page()


@router.post("/login", response_class=HTMLResponse)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return HTMLResponse(render_login_page("Користувача не знайдено."), status_code=401)

    if not verify_password(password, user.password_hash):
        return HTMLResponse(render_login_page("Неправильний пароль."), status_code=401)

    response = RedirectResponse("/web/dashboard", status_code=303)
    response.set_cookie("user", user.username, httponly=True)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("user")
    return response