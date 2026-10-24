"""One-step offline setup. Creates .env, schema, demo data, and reports credentials."""
import secrets
from pathlib import Path
from config import ROOT,read_env
from storage import init_db,transaction,audit
from security import hash_password
from seed import seed_demo,write_employee_csv

def setup():
    path=ROOT/'.env'
    previous=read_env(path)
    def needs_new(value, minimum):
        return len(value or '')<minimum or value.lower().startswith(('replace','change','your_'))
    fresh=not path.exists() or not path.read_text(encoding='utf-8-sig').strip()
    generated_password=needs_new(previous.get('ADMIN_PASSWORD',''),12)
    generated_secret=needs_new(previous.get('SECRET_KEY',''),32)
    admin_email=previous.get('ADMIN_EMAIL','admin@pysupply.com').strip().lower()
    if not admin_email.endswith('@pysupply.com'):admin_email='admin@pysupply.com'
    accounts=[('admin',admin_email,'ADMIN_PASSWORD'),
              ('manager','manager@pysupply.com','MANAGER_PASSWORD'),
              ('viewer','viewer@pysupply.com','VIEWER_PASSWORD')]
    generated={key:needs_new(previous.get(key,''),12) for _,_,key in accounts}
    passwords={key:secrets.token_urlsafe(16) if generated[key] else previous[key] for _,_,key in accounts}
    secret=secrets.token_urlsafe(48) if generated_secret else previous['SECRET_KEY']
    values={**previous,'COMPANY_NAME':'pySupply',
            'DATABASE_PATH':previous.get('DATABASE_PATH','pysupply.db'),
            'ADMIN_EMAIL':admin_email,'SECRET_KEY':secret,
            'HOST':previous.get('HOST','127.0.0.1'),
            'PORT':previous.get('PORT','8000'),
            'COOKIE_HTTPS_ONLY':previous.get('COOKIE_HTTPS_ONLY','false'),
            **passwords}
    if fresh or any(generated.values()) or generated_secret or previous.get('COMPANY_NAME')!='pySupply':
        path.write_text('\n'.join(f'{k}={v}' for k,v in values.items())+'\n',encoding='utf-8')
        print('Local .env created/updated securely (excluded from GitHub).')
    init_db()
    with transaction() as db:
        for role,email,key in accounts:
            old=db.execute('SELECT id FROM users WHERE username=?',(email,)).fetchone()
            if not old:
                db.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',(email,hash_password(passwords[key]),role))
                audit(db,'system','create_user',email)
            elif generated[key]:
                db.execute('UPDATE users SET password_hash=?,role=? WHERE id=?',(hash_password(passwords[key]),role,old['id']))
                db.execute('DELETE FROM sessions WHERE user_id=?',(old['id'],))
                audit(db,'system','reset_demo_password',email)
    write_employee_csv()
    seed_demo()
    print('\npySupply local setup ready')
    print('Demo login accounts (keep these passwords private):')
    for role,email,key in accounts:
        print(f'  {role.title():7} {email}')
        if generated[key]:print(f'    New password (save now): {passwords[key]}')
        else:print('    Existing password preserved (not displayed).')
    print('Run: python run.py')

if __name__=='__main__':setup()
