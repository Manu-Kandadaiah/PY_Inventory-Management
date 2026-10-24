"""SQLite schema and transactional domain operations. No third-party packages."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from config import db_path

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=30, isolation_level=None, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=30000')
    return db

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','manager','viewer')), active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS categories (
 id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS suppliers (
 id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, email TEXT NOT NULL DEFAULT '',
 phone TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 category_id INTEGER NOT NULL REFERENCES categories(id),
 supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
 quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
 reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level>=0),
 unit_price REAL NOT NULL DEFAULT 0 CHECK(unit_price>=0), active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS purchase_orders (
 id INTEGER PRIMARY KEY, supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
 product_id INTEGER NOT NULL REFERENCES products(id),
 quantity INTEGER NOT NULL CHECK(quantity>0), unit_cost REAL NOT NULL CHECK(unit_cost>=0),
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','submitted','received','cancelled')),
 created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS stock_transactions (
 id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 kind TEXT NOT NULL, change INTEGER NOT NULL, balance_after INTEGER NOT NULL CHECK(balance_after>=0),
 note TEXT NOT NULL DEFAULT '', user_id INTEGER REFERENCES users(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS employees (
 id INTEGER PRIMARY KEY, employee_code TEXT NOT NULL UNIQUE,
 first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 department TEXT NOT NULL, job_title TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '',
 joining_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
 created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_po_created ON purchase_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_stock_created ON stock_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_employee_dept ON employees(department);
'''

def init_db():
    with connect() as db:
        db.executescript(SCHEMA)

@contextmanager
def transaction():
    db = connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def rowdict(row):
    return dict(row) if row is not None else None

def audit(db, actor, action, detail):
    db.execute('INSERT INTO audit_logs(actor,action,detail,created_at) VALUES(?,?,?,?)',
               (actor, action, str(detail)[:500], utcnow()))

class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)

def require_str(data, name, length=150):
    value = str(data.get(name, '')).strip()
    if not value or len(value)>length:
        raise Problem(422, f'{name} is required (max {length} characters)')
    return value

def positive_number(data, key, integer=False, allow_zero=True):
    try:
        raw=data[key]
        if isinstance(raw,bool):raise ValueError('boolean not allowed')
        if integer and isinstance(raw,float) and not raw.is_integer():raise ValueError('fractional quantity')
        val = int(raw) if integer else float(raw)
    except (KeyError, ValueError, TypeError):
        raise Problem(422, f'Invalid {key}')
    if val < 0 or (not allow_zero and val==0) or (not integer and (val==float('inf') or val!=val)):
        raise Problem(422, f'Invalid {key}')
    return val

def must_exist(db,table,pk,active=False):
    if table not in ('products','categories','suppliers','employees','purchase_orders'):
        raise Problem(404,'Unknown resource')
    row=db.execute(f'SELECT * FROM {table} WHERE id=?',(pk,)).fetchone()
    if not row or (active and 'active' in row.keys() and not row['active']):
        raise Problem(404,f'{table} record not found or inactive')
    return row

def get_collection(kind, search='', limit=500):
    fields={'products':['sku','name'],'suppliers':['name','email'], 'categories':['name'],
            'employees':['first_name','last_name','email','department','job_title'],
            'purchase_orders':[], 'stock_transactions':[], 'audit_logs':[]}
    if kind not in fields:raise Problem(404,'Unknown resource')
    if kind=='products':
        sql='SELECT p.*, c.name category_name, s.name supplier_name FROM products p JOIN categories c ON c.id=p.category_id JOIN suppliers s ON s.id=p.supplier_id'
        prefix='p.'
    elif kind=='purchase_orders':
        sql='SELECT o.*, p.name product_name, p.sku, s.name supplier_name FROM purchase_orders o JOIN products p ON p.id=o.product_id JOIN suppliers s ON s.id=o.supplier_id'
        prefix='o.'
    elif kind=='stock_transactions':
        sql='SELECT t.*, p.name product_name, p.sku FROM stock_transactions t JOIN products p ON p.id=t.product_id'
        prefix='t.'
    else:
        sql=f'SELECT * FROM {kind}'
        prefix=''
    params=[]
    if search and fields[kind]:
        sql+=' WHERE ('+' OR '.join(f'{prefix}{f} LIKE ?' for f in fields[kind])+')'
        params=['%'+search[:100]+'%']*len(fields[kind])
    sql+=f' ORDER BY {prefix}id DESC LIMIT ?'
    params.append(max(1,min(int(limit),5000)))
    with connect() as db:
        return [dict(x) for x in db.execute(sql,params)]

def summary():
    with connect() as db:
        return {
          'products':db.execute('SELECT count(*) FROM products WHERE active=1').fetchone()[0],
          'suppliers':db.execute('SELECT count(*) FROM suppliers WHERE active=1').fetchone()[0],
          'employees':db.execute("SELECT count(*) FROM employees WHERE status='active'").fetchone()[0],
          'orders':db.execute('SELECT count(*) FROM purchase_orders').fetchone()[0],
          'stock_units':db.execute('SELECT coalesce(sum(quantity),0) FROM products WHERE active=1').fetchone()[0],
          'stock_value':round(db.execute('SELECT coalesce(sum(quantity*unit_price),0) FROM products WHERE active=1').fetchone()[0],2),
          'low_stock':db.execute('SELECT count(*) FROM products WHERE active=1 AND quantity<=reorder_level').fetchone()[0],
          'pending_orders':db.execute("SELECT count(*) FROM purchase_orders WHERE status IN ('draft','submitted')").fetchone()[0],
          'categories':db.execute('SELECT count(*) FROM categories WHERE active=1').fetchone()[0],
        }
