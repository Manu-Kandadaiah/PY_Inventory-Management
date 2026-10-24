"""pySupply local inventory web server: no pip packages or DLL extensions required."""
import csv
import hashlib
import html
import io
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime,timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from config import ROOT, read_env, setting
from security import check_csrf, create_session, get_session, hash_password, verify_password, csrf_for, token_digest
from storage import connect,init_db,transaction,require_str,positive_number,must_exist,Problem,audit,get_collection,summary,utcnow

ASSETS=ROOT/'static'; TEMPLATES=ROOT/'templates'
ALIASES={'orders':'purchase_orders','transactions':'stock_transactions','audit':'audit_logs',
    'purchase_orders':'purchase_orders','stock_transactions':'stock_transactions','audit_logs':'audit_logs',
    'products':'products','suppliers':'suppliers','categories':'categories','employees':'employees'}
EXPORTED={'products','suppliers','categories','purchase_orders','stock_transactions','employees'}


def integer_id(value,name='id'):
    try:n=int(value)
    except (TypeError,ValueError):raise Problem(422,f'Invalid {name}')
    if n<=0:raise Problem(422,f'Invalid {name}')
    return n


def optional_email(data,key='email'):
    email=str(data.get(key,'')).strip().lower()
    if len(email)>200 or (email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)):
        raise Problem(422,'Invalid email address')
    return email


def product_payload(data):
    return (require_str(data,'sku',50),require_str(data,'name',150),integer_id(data.get('category_id'),'category_id'),
            integer_id(data.get('supplier_id'),'supplier_id'),positive_number(data,'reorder_level',integer=True),
            positive_number(data,'unit_price'))


def employee_payload(data):
    first=require_str(data,'first_name',80)
    last=require_str(data,'last_name',80)
    email=optional_email(data)
    if not email or not email.endswith('@pysupply.com'):
        raise Problem(422,'Employee email must end in @pysupply.com')
    dept=require_str(data,'department',100)
    title=require_str(data,'job_title',120)
    code=require_str(data,'employee_code',40)
    joined=str(data.get('joining_date','')).strip()
    try: datetime.strptime(joined,'%Y-%m-%d')
    except ValueError:raise Problem(422,'joining_date must be YYYY-MM-DD')
    status=str(data.get('status','active'))
    if status not in ('active','inactive'):raise Problem(422,'Invalid status')
    return code,first,last,email,dept,title,str(data.get('phone',''))[:40],joined,status


def role_ok(user,*roles):
    if user['role'] not in roles:raise Problem(403,'Your role does not permit this action')


def respond_collection(kind,q,limit):
    resolved=ALIASES.get(kind)
    if not resolved:raise Problem(404,'Unknown collection')
    return get_collection(resolved,q,limit)


def create_object(kind,data,user):
    role_ok(user,'admin','manager')
    if kind=='categories': role_ok(user,'admin')
    with transaction() as db:
        if kind=='categories':
            cur=db.execute('INSERT INTO categories(name) VALUES(?)',(require_str(data,'name',100),))
        elif kind=='suppliers':
            cur=db.execute('INSERT INTO suppliers(name,email,phone) VALUES(?,?,?)',
               (require_str(data,'name',150),optional_email(data),str(data.get('phone',''))[:60]))
        elif kind=='products':
            values=product_payload(data)
            must_exist(db,'categories',values[2],True)
            must_exist(db,'suppliers',values[3],True)
            cur=db.execute('INSERT INTO products(sku,name,category_id,supplier_id,reorder_level,unit_price) VALUES(?,?,?,?,?,?)',values)
        elif kind=='employees':
            values=employee_payload(data)
            cur=db.execute('INSERT INTO employees(employee_code,first_name,last_name,email,department,job_title,phone,joining_date,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(*values,utcnow()))
        elif kind=='orders':
            pid=integer_id(data.get('product_id'),'product_id')
            sid=integer_id(data.get('supplier_id'),'supplier_id')
            product=must_exist(db,'products',pid,True)
            if product['supplier_id']!=sid:raise Problem(422,'Product must belong to the selected supplier')
            quantity=positive_number(data,'quantity',integer=True,allow_zero=False)
            cost=positive_number(data,'unit_cost')
            cur=db.execute('INSERT INTO purchase_orders(supplier_id,product_id,quantity,unit_cost,status,created_at) VALUES(?,?,?,?,?,?)',
                 (sid,pid,quantity,cost,'draft',utcnow()))
        else:raise Problem(404,'Unknown resource')
        uid=cur.lastrowid
        audit(db,user['username'],'create_'+kind,str(uid))
        return {'id':uid,'created':True}


def update_object(kind,pk,data,user):
    role_ok(user,'admin','manager')
    resolved=ALIASES.get(kind)
    if resolved not in ('products','categories','suppliers','employees'):raise Problem(404,'Unknown resource')
    if resolved=='categories':role_ok(user,'admin')
    with transaction() as db:
        must_exist(db,resolved,pk)
        if resolved=='categories':
            db.execute('UPDATE categories SET name=? WHERE id=?',(require_str(data,'name',100),pk))
        elif resolved=='suppliers':
            db.execute('UPDATE suppliers SET name=?,email=?,phone=? WHERE id=?',
               (require_str(data,'name',150),optional_email(data),str(data.get('phone',''))[:60],pk))
        elif resolved=='products':
            values=product_payload(data)
            must_exist(db,'categories',values[2],True);must_exist(db,'suppliers',values[3],True)
            db.execute('UPDATE products SET sku=?,name=?,category_id=?,supplier_id=?,reorder_level=?,unit_price=? WHERE id=?',(*values,pk))
        elif resolved=='employees':
            values=employee_payload(data)
            db.execute('UPDATE employees SET employee_code=?,first_name=?,last_name=?,email=?,department=?,job_title=?,phone=?,joining_date=?,status=? WHERE id=?',(*values,pk))
        audit(db,user['username'],'update_'+resolved,str(pk))
    return {'updated':True,'id':pk}


def archive_object(kind,pk,user):
    role_ok(user,'admin')
    resolved=ALIASES.get(kind)
    if resolved not in ('products','categories','suppliers','employees'):raise Problem(404,'Unknown resource')
    with transaction() as db:
        must_exist(db,resolved,pk)
        if resolved=='employees':
            db.execute('UPDATE employees SET status="inactive" WHERE id=?',(pk,))
        else:
            db.execute(f'UPDATE {resolved} SET active=0 WHERE id=?',(pk,))
        audit(db,user['username'],'deactivate_'+resolved,str(pk))
    return {'deactivated':True}


def update_stock(data,user):
    role_ok(user,'admin','manager')
    pid=integer_id(data.get('product_id'),'product_id')
    kind=str(data.get('kind',''))
    if kind not in ('in','out','adjust'):raise Problem(422,'kind must be in, out, or adjust')
    qty=positive_number(data,'quantity',integer=True,allow_zero=kind=='adjust')
    with transaction() as db:
        product=must_exist(db,'products',pid,True)
        before=product['quantity']; new=before+qty if kind=='in' else before-qty if kind=='out' else qty
        if new<0:raise Problem(409,'Insufficient stock')
        db.execute('UPDATE products SET quantity=? WHERE id=?',(new,pid))
        change=new-before
        cur=db.execute('INSERT INTO stock_transactions(product_id,kind,change,balance_after,note,user_id,created_at) VALUES(?,?,?,?,?,?,?)',
           (pid,kind,change,new,str(data.get('note',''))[:255],user['id'],utcnow()))
        audit(db,user['username'],'stock_'+kind,f'{product["sku"]}: {change:+}')
        return {'id':cur.lastrowid,'balance_after':new,'change':change}


def change_order(pk,status,user):
    role_ok(user,'admin','manager')
    transitions={'draft':{'submitted','cancelled'},'submitted':{'received','cancelled'},'received':set(),'cancelled':set()}
    with transaction() as db:
        order=must_exist(db,'purchase_orders',pk)
        if status not in transitions[order['status']]:raise Problem(409,f'Cannot change {order["status"]} order to {status}')
        if status=='received':
            product=must_exist(db,'products',order['product_id'],True)
            balance=product['quantity']+order['quantity']
            db.execute('UPDATE products SET quantity=? WHERE id=?',(balance,product['id']))
            db.execute('INSERT INTO stock_transactions(product_id,kind,change,balance_after,note,user_id,created_at) VALUES(?,?,?,?,?,?,?)',
                (product['id'],'in',order['quantity'],balance,f'PO #{pk} receipt',user['id'],utcnow()))
        db.execute('UPDATE purchase_orders SET status=? WHERE id=?',(status,pk))
        audit(db,user['username'],'order_status',f'PO #{pk}: {status}')
        return {'id':pk,'status':status}


def export_csv(kind):
    resolved=ALIASES.get(kind)
    if resolved not in EXPORTED:raise Problem(404,'Not exportable')
    rows=get_collection(resolved,'',5000)
    buf=io.StringIO()
    if rows:
        writer=csv.DictWriter(buf,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return buf.getvalue().encode('utf-8-sig')


class Handler(BaseHTTPRequestHandler):
    server_version='pySupply/1.0'

    def _headers(self,status,ctype,size,extra=None):
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(size))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.send_header('Cache-Control','no-store')
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.end_headers()

    def _send(self,status,data,ctype='application/json; charset=utf-8',extra=None):
        if isinstance(data,(dict,list)):raw=json.dumps(data,ensure_ascii=False,default=str).encode('utf-8')
        elif isinstance(data,str):raw=data.encode('utf-8')
        else:raw=data
        self._headers(status,ctype,len(raw),extra)
        self.wfile.write(raw)

    def _json(self,status,data):self._send(status,data)
    def _page(self,name):
        text=(TEMPLATES/name).read_bytes()
        self._send(200,text,'text/html; charset=utf-8')
    def _redirect(self,to,cookie=None):
        h={'Location':to}
        if cookie:h['Set-Cookie']=cookie
        self._send(303,b'',extra=h)
    def _cookie(self,token='',delete=False):
        h=f'session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={0 if delete else 28800}'
        if setting('COOKIE_HTTPS_ONLY','false').lower()=='true':h+='; Secure'
        return h
    def _body(self):
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:raise Problem(400,'Invalid Content-Length')
        if length<0 or length>1048576:raise Problem(413,'Request too large')
        return self.rfile.read(length)
    def _user(self):
        session=get_session(self.headers.get('Cookie',''))
        if not session:raise Problem(401,'Please log in')
        return session
    def _checked_user(self):
        user=self._user()
        if not check_csrf(user,self.headers.get('X-CSRF-Token','')):
            raise Problem(403,'Invalid CSRF token. Refresh the page and sign in again.')
        return user
    def _data(self):
        content_type=self.headers.get('Content-Type','')
        raw=self._body()
        if 'application/json' in content_type:
            try:data=json.loads(raw)
            except (json.JSONDecodeError,UnicodeDecodeError):raise Problem(400,'Invalid JSON')
            if not isinstance(data,dict):raise Problem(422,'Expected JSON object')
            return data
        parsed=parse_qs(raw.decode('utf-8',errors='replace'),keep_blank_values=True)
        return {k:v[0] for k,v in parsed.items()}
    def _safe(self,callback):
        try:callback()
        except Problem as e:self._json(e.status,{'detail':e.message})
        except sqlite3.IntegrityError:
            self._json(409,{'detail':'Duplicate value or an invalid database relationship'})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json(500,{'detail':'Internal server error. See the local terminal log.'})

    def do_GET(self):self._safe(self._get)
    def do_POST(self):self._safe(self._post)
    def do_PUT(self):self._safe(self._put)
    def do_DELETE(self):self._safe(self._delete)

    def _get(self):
        url=urlsplit(self.path); path=url.path
        if path in ('/health','/healthz'):
            with connect() as db:db.execute('SELECT 1')
            return self._json(200,{'status':'ok','service':'pySupply','database':'sqlite'})
        if path.startswith('/static/'):
            name=path[len('/static/'):]
            if '/' in name or '\\' in name or name.startswith('.'):raise Problem(404,'Not found')
            file=ASSETS/name
            if not file.is_file():raise Problem(404,'Not found')
            mime={'.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'}.get(file.suffix,'application/octet-stream')
            return self._send(200,file.read_bytes(),mime)
        if path=='/favicon.ico':return self._send(200,(ASSETS/'favicon.svg').read_bytes(),'image/svg+xml')
        if path=='/login':return self._page('login.html')
        if path=='/':
            if not get_session(self.headers.get('Cookie','')):return self._redirect('/login')
            return self._page('dashboard.html')
        if path=='/api/me':
            session=self._user()
            return self._json(200,{'id':session['id'],'email':session['username'],'username':session['username'],
                                   'role':session['role'],'company':'pySupply','csrf_token':csrf_for(session)})
        if path=='/api/stats':
            self._user()
            stats=summary()
            with connect() as db:
                cats=[dict(x) for x in db.execute('SELECT c.name,COUNT(p.id) item_count,COALESCE(SUM(p.quantity),0) stock_units FROM categories c LEFT JOIN products p ON p.category_id=c.id AND p.active=1 GROUP BY c.id ORDER BY stock_units DESC LIMIT 8')]
                status=[dict(x) for x in db.execute('SELECT status,COUNT(*) count FROM purchase_orders GROUP BY status')]
                low=[dict(x) for x in db.execute('SELECT sku,name,quantity,reorder_level FROM products WHERE active=1 AND quantity<=reorder_level ORDER BY quantity ASC LIMIT 8')]
            return self._json(200,dict(stats,categories_chart=cats,order_status=status,low_stock_items=low))
        if path.startswith('/api/export/'):
            user=self._user();role_ok(user,'admin','manager')
            kind=path.rsplit('/',1)[-1];payload=export_csv(kind)
            return self._send(200,payload,'text/csv; charset=utf-8',{'Content-Disposition':f'attachment; filename="pysupply_{kind}.csv"'})
        if path.startswith('/api/'):
            user=self._user();kind=path[len('/api/'):]
            if '/' in kind:raise Problem(404,'Not found')
            if kind in ('audit','audit_logs'):role_ok(user,'admin')
            query=parse_qs(url.query)
            search=query.get('search',[''])[0]
            try:limit=int(query.get('limit',['500'])[0])
            except ValueError:raise Problem(422,'Invalid limit')
            return self._json(200,respond_collection(kind,search,limit))
        raise Problem(404,'Page not found')

    def _post(self):
        path=urlsplit(self.path).path
        if path=='/login':
            data=self._data();email=str(data.get('username','')).strip().lower()
            password=str(data.get('password',''))
            with connect() as db:
                user=db.execute('SELECT id,username,password_hash,role FROM users WHERE username=? AND active=1',(email,)).fetchone()
            if not user or not verify_password(password,user['password_hash']):return self._redirect('/login?error=1')
            token=create_session(user['id'])
            return self._redirect('/',self._cookie(token))
        user=self._checked_user()
        if path=='/logout':
            with connect() as db:db.execute('DELETE FROM sessions WHERE token_hash=?',(token_digest(user['token']),))
            return self._redirect('/login',self._cookie(delete=True))
        data=self._data()
        if path=='/api/stock':return self._json(201,update_stock(data,user))
        if path in ('/api/categories','/api/suppliers','/api/products','/api/employees','/api/orders'):
            return self._json(201,create_object(path.rsplit('/',1)[-1],data,user))
        match=re.fullmatch(r'/api/orders/(\d+)/status',path)
        if match:return self._json(200,change_order(integer_id(match.group(1)),str(data.get('status','')),user))
        raise Problem(404,'Unknown endpoint')

    def _put(self):
        user=self._checked_user()
        match=re.fullmatch(r'/api/(categories|suppliers|products|employees)/(\d+)',urlsplit(self.path).path)
        if not match:raise Problem(404,'Unknown endpoint')
        return self._json(200,update_object(match.group(1),integer_id(match.group(2)),self._data(),user))
    def _delete(self):
        user=self._checked_user()
        match=re.fullmatch(r'/api/(categories|suppliers|products|employees)/(\d+)',urlsplit(self.path).path)
        if not match:raise Problem(404,'Unknown endpoint')
        return self._json(200,archive_object(match.group(1),integer_id(match.group(2)),user))


def main():
    configured=read_env()
    if (not configured.get('SECRET_KEY') or len(configured.get('SECRET_KEY',''))<32
         or configured.get('SECRET_KEY','').lower().startswith('replace')
         or not configured.get('ADMIN_PASSWORD') or configured.get('ADMIN_PASSWORD','').lower().startswith('replace')
         or not configured.get('ADMIN_EMAIL')):
        print('Missing/incomplete .env configuration. Running offline setup...')
        from setup_project import setup
        setup()
    init_db()
    with connect() as db:
        has_user=db.execute('SELECT id FROM users LIMIT 1').fetchone()
    if not has_user:
        from setup_project import setup
        setup()
    host=setting('HOST','127.0.0.1');port=int(setting('PORT','8000'))
    server=ThreadingHTTPServer((host,port),Handler)
    print(f'pySupply ready: http://{host}:{port}/login (Ctrl+C to stop)')
    try:server.serve_forever()
    except KeyboardInterrupt:print('\npySupply stopped.')
    finally:server.server_close()

if __name__=='__main__':main()
