"""Password hashing and cookie-session helpers using Python standard library."""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from config import setting
from storage import connect, utcnow

ROUNDS = 310_000

def hash_password(password):
    salt=os.urandom(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,ROUNDS)
    return f'pbkdf2_sha256${ROUNDS}${salt.hex()}${digest.hex()}'

def verify_password(password, stored):
    try:
        algorithm,iterations,salt,digest=stored.split('$')
        if algorithm!='pbkdf2_sha256':return False
        attempted=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt),int(iterations))
        return hmac.compare_digest(attempted,bytes.fromhex(digest))
    except (TypeError,ValueError,AttributeError):return False

def token_digest(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()

def create_session(user_id):
    token=secrets.token_urlsafe(40)
    expires=(datetime.now(timezone.utc)+timedelta(hours=8)).isoformat(timespec='seconds')
    with connect() as db:
        db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)',(token_digest(token),user_id,expires))
    return token

def get_session(cookie_header):
    jar=SimpleCookie()
    try:jar.load(cookie_header or '')
    except Exception:return None
    morsel=jar.get('session')
    if not morsel:return None
    token=morsel.value
    if len(token)>200:return None
    with connect() as db:
        row=db.execute('SELECT u.id,u.username,u.role,s.expires_at FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token_hash=? AND u.active=1',(token_digest(token),)).fetchone()
    if not row:return None
    try:
        if datetime.fromisoformat(row['expires_at'])<datetime.now(timezone.utc):return None
    except ValueError:return None
    return dict(row)|{'token':token}

def csrf_for(session):
    return hmac.new(setting('SECRET_KEY').encode(),session['token'].encode(),hashlib.sha256).hexdigest()

def check_csrf(session, token):
    return bool(session and token and hmac.compare_digest(csrf_for(session),str(token)))
