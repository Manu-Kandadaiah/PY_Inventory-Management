"""Run locally to securely reset demo admin password without deleting inventory."""
import secrets
from config import setting
from security import hash_password
from storage import transaction,init_db

def reset_admin():
    init_db()
    new_password=secrets.token_urlsafe(16)
    email=setting('ADMIN_EMAIL','admin@pysupply.com')
    with transaction() as db:
        row=db.execute('SELECT id FROM users WHERE username=?',(email,)).fetchone()
        if not row:raise SystemExit('Admin user missing. Run python setup_project.py first.')
        db.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(new_password),row['id']))
        db.execute('DELETE FROM sessions WHERE user_id=?',(row['id'],))
    print('Admin login:',email)
    print('New password (save privately):',new_password)
    print('Note: the old ADMIN_PASSWORD value in .env is not used to authenticate existing users.')

if __name__=='__main__':reset_admin()
