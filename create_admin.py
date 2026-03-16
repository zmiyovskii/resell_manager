import base64
import hashlib
import os

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,
    )
    return base64.b64encode(salt + hashed).decode("utf-8")


db: Session = SessionLocal()

username = "admin"
password = "admin123"

existing = db.query(User).filter(User.username == username).first()
if existing:
    print("Admin already exists")
else:
    user = User(
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    print("Admin created")