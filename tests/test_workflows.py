"""Stdlib-only integration tests: real HTTP requests against a temporary SQLite DB."""
import http.cookiejar
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import storage
from seed import seed_demo,employee_rows
from security import hash_password
from run import Handler

class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory()
        cls.old_path=storage.db_path
        storage.db_path=lambda: Path(cls.folder.name)/'test.db'
        os.environ['SECRET_KEY']='test-secret-please-change-not-for-production-12345'
        storage.init_db()
        with storage.transaction() as db:
            db.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',('admin@pysupply.com',hash_password('OnlyForTests123!'),'admin'))
            db.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',('viewer@pysupply.com',hash_password('ViewerOnly123!'),'viewer'))
        seed_demo()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.cookies=http.cookiejar.CookieJar()
        cls.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cookies))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        storage.db_path=cls.old_path
        cls.folder.cleanup()
        os.environ.pop('SECRET_KEY',None)

    def request(self,path,method='GET',data=None,csrf=None,client=None):
        headers={}
        if data is not None:
            if isinstance(data,dict) and path=='/login':
                data=urllib.parse.urlencode(data).encode()
                headers['Content-Type']='application/x-www-form-urlencoded'
            else:
                data=json.dumps(data).encode()
                headers['Content-Type']='application/json'
        if csrf is not None:headers['X-CSRF-Token']=csrf
        req=urllib.request.Request(self.base+path,data=data,method=method,headers=headers)
        try:
            r=(client or self.client).open(req,timeout=6)
            return r.status,r.headers,r.read()
        except urllib.error.HTTPError as e:
            return e.code,e.headers,e.read()

    def login(self):
        status,_,_=self.request('/login','POST',{'username':'admin@pysupply.com','password':'OnlyForTests123!'})
        self.assertEqual(status,200)
        status,_,payload=self.request('/api/me')
        self.assertEqual(status,200)
        return json.loads(payload)['csrf_token']

    def test_01_seed_and_emails(self):
        with storage.connect() as db:
            count=db.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
            self.assertEqual(count,300)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM products').fetchone()[0],240)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stock_transactions').fetchone()[0],605)
            self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall())
        self.assertTrue(all(x['email']==f"{x['first_name'].lower()}.{x['last_name'].lower()}@pysupply.com" for x in employee_rows()))

    def test_02_anonymous_and_static(self):
        anon=urllib.request.build_opener()
        self.assertEqual(self.request('/api/products',client=anon)[0],401)
        self.assertEqual(self.request('/health',client=anon)[0],200)
        self.assertEqual(self.request('/static/style.css',client=anon)[0],200)
        self.assertEqual(self.request('/static/logo.svg',client=anon)[0],200)
        self.assertEqual(self.request('/login',client=anon)[0],200)

    def test_03_auth_and_crud_stock(self):
        csrf=self.login()
        self.assertEqual(self.request('/api/products','POST',{'sku':'PYS-TEST','name':'Test Scanner','category_id':1,'supplier_id':1,'reorder_level':5,'unit_price':750},csrf='invalid')[0],403)
        code,_,payload=self.request('/api/products','POST',{'sku':'PYS-TEST','name':'Test Scanner','category_id':1,'supplier_id':1,'reorder_level':5,'unit_price':750},csrf=csrf)
        self.assertEqual(code,201,payload)
        pid=json.loads(payload)['id']
        def move(kind,n):return self.request('/api/stock','POST',{'product_id':pid,'kind':kind,'quantity':n},csrf=csrf)
        self.assertEqual(move('in',10)[0],201)
        self.assertEqual(move('out',11)[0],409)
        self.assertEqual(json.loads(move('out',4)[2])['balance_after'],6)
        code,_,payload=self.request('/api/orders','POST',{'product_id':pid,'supplier_id':1,'quantity':7,'unit_cost':675},csrf=csrf)
        self.assertEqual(code,201,payload)
        oid=json.loads(payload)['id']
        self.assertEqual(self.request(f'/api/orders/{oid}/status','POST',{'status':'submitted'},csrf=csrf)[0],200)
        self.assertEqual(self.request(f'/api/orders/{oid}/status','POST',{'status':'received'},csrf=csrf)[0],200)
        self.assertEqual(self.request(f'/api/orders/{oid}/status','POST',{'status':'received'},csrf=csrf)[0],409)
        products=json.loads(self.request('/api/products')[2])
        self.assertEqual(next(x['quantity'] for x in products if x['id']==pid),13)
        self.assertEqual(self.request('/api/export/products')[0],200)

    def test_04_new_named_employee(self):
        csrf=self.login()
        data={'employee_code':'PYS-T100','first_name':'Test','last_name':'Candidate','email':'test.candidate@pysupply.com','department':'Warehouse Operations','job_title':'Coordinator','phone':'','joining_date':'2026-05-01','status':'active'}
        self.assertEqual(self.request('/api/employees','POST',data,csrf=csrf)[0],201)
        self.assertEqual(self.request('/api/employees','POST',data,csrf=csrf)[0],409)
        data['employee_code']='PYS-T101';data['email']='test@example.com'
        self.assertEqual(self.request('/api/employees','POST',data,csrf=csrf)[0],422)
        self.assertEqual(self.request('/api/export/employees')[0],200)

    def test_05_viewer_is_read_only(self):
        readonly=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.assertEqual(self.request('/login','POST',{'username':'viewer@pysupply.com','password':'ViewerOnly123!'},client=readonly)[0],200)
        self.assertEqual(self.request('/api/employees',client=readonly)[0],200)
        code,_,payload=self.request('/api/me',client=readonly)
        csrf=json.loads(payload)['csrf_token']
        self.assertEqual(self.request('/api/categories','POST',{'name':'Unauthorized'},csrf=csrf,client=readonly)[0],403)
        self.assertEqual(self.request('/api/audit',client=readonly)[0],403)
        self.assertEqual(self.request('/api/export/employees',client=readonly)[0],403)


if __name__=='__main__':unittest.main()
