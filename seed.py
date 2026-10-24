"""Deterministic, fictional pySupply demo data. Never sends email."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path
from storage import init_db, transaction, audit, utcnow

FIRST = ['Aarav','Diya','Ishaan','Meera','Rohan','Ananya','Kabir','Tara','Vivaan','Saanvi','Arjun','Nisha','Dev','Ira','Kiran','Neha','Reyansh','Aditi','Rahul','Priya','Advik','Kavya','Manav','Riya','Nikhil','Pooja','Siddharth','Sneha','Varun','Shreya']
LAST = ['Sharma','Rao','Patel','Nair','Gupta','Menon','Iyer','Singh','Kulkarni','Mehta','Joshi','Reddy','Bhat','Pillai','Das','Kapoor','Chatterjee','Verma','Desai','Mishra']
DEPARTMENTS = ['Procurement','Warehouse Operations','Supplier Relations','Logistics','Sales Operations','Finance','Information Technology','Quality Assurance','Human Resources','Supply Planning']
JOBS = ['Coordinator','Analyst','Specialist','Executive','Associate','Lead','Supervisor','Officer']
CATEGORIES = ['Packaging','Safety Equipment','Warehouse Tools','Office Supplies','Material Handling','Networking','Computers','Electronics','Shipping Supplies','Workstation Gear','Quality Instruments','Maintenance']
PRODUCTS = ['Barcode Scanner','Thermal Label Printer','Shipping Carton','Safety Helmet','Pallet Jack','Warehouse Tablet','Laptop','Docking Station','Wireless Access Point','Network Switch','Desktop Monitor','Label Roll','Packing Tape','Precision Scale','RFID Reader','ESD Gloves','Hand Truck','Portable SSD','UPS','Asset Tag','Bubble Wrap','Cable Kit','Inventory Scanner','Industrial Keyboard']

def employee_rows():
    rng=random.Random(2026)
    combinations=[(a,b) for a in FIRST for b in LAST]
    rng.shuffle(combinations)
    rows=[]
    for i,(first,last) in enumerate(combinations[:300],1):
        department=DEPARTMENTS[(i-1)%len(DEPARTMENTS)]
        joined=date(2022,1,1)+timedelta(days=rng.randint(0,1600))
        rows.append(dict(employee_code=f'PYS-EMP-{i:04d}', first_name=first, last_name=last,
           email=f'{first.lower()}.{last.lower()}@pysupply.com', department=department,
           job_title=f'{JOBS[i%len(JOBS)]} - {department}',
           phone=f'+91-90000-{i:05d}',joining_date=joined.isoformat(),status='active'))
    assert len({x['email'] for x in rows})==300
    return rows

def write_employee_csv(path=None):
    target=Path(path) if path else Path(__file__).resolve().parent/'demo_data'/'employees_300.csv'
    target.parent.mkdir(parents=True,exist_ok=True)
    rows=employee_rows()
    with target.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return target

def seed_demo():
    init_db()
    rng=random.Random(502026)
    with transaction() as db:
        existing=db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        if existing:
            print('Demo inventory already present; no duplicate records created.')
            return False
        if not db.execute('SELECT id FROM users LIMIT 1').fetchone():
            raise RuntimeError('Run python setup_project.py first to create the administrator.')
        for c in CATEGORIES:
            db.execute('INSERT INTO categories(name) VALUES(?)',(c,))
        for i in range(1,25):
            db.execute('INSERT INTO suppliers(name,email,phone) VALUES(?,?,?)',(
                f'{["Apex","Meridian","Vertex","Summit","Nimbus","BluePeak","Synergy","Everest"][((i-1)%8)]} Supply Partners {i:02}',
                f'vendor{i:02d}@pysupply.com',f'+91-80400-{i:05d}'))
        for emp in employee_rows():
            db.execute('INSERT INTO employees(employee_code,first_name,last_name,email,department,job_title,phone,joining_date,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
             (*[emp[k] for k in ('employee_code','first_name','last_name','email','department','job_title','phone','joining_date','status')],utcnow()))
        for i in range(1,241):
            category=((i-1)%12)+1
            supplier=((i*7-1)%24)+1
            name=f'{PRODUCTS[(i-1)%len(PRODUCTS)]} · Model {i:03d}'
            db.execute('INSERT INTO products(sku,name,category_id,supplier_id,quantity,reorder_level,unit_price) VALUES(?,?,?,?,0,?,?)',
                       (f'PYS-{i:05d}',name,category,supplier,rng.randint(12,38),round(rng.uniform(160,26500),2)))
            qty=rng.randint(6,160)
            db.execute('UPDATE products SET quantity=? WHERE id=?',(qty,i))
            db.execute('INSERT INTO stock_transactions(product_id,kind,change,balance_after,note,user_id,created_at) VALUES(?,?,?,?,?,?,?)',
                       (i,'in',qty,qty,'Fictional opening inventory',1,utcnow()))
        for i in range(320):
            pid=rng.randint(1,240)
            old=db.execute('SELECT quantity FROM products WHERE id=?',(pid,)).fetchone()[0]
            change=rng.randint(1,25) if i%3!=0 else -min(old,rng.randint(1,10))
            new=old+change
            db.execute('UPDATE products SET quantity=? WHERE id=?',(new,pid))
            db.execute('INSERT INTO stock_transactions(product_id,kind,change,balance_after,note,user_id,created_at) VALUES(?,?,?,?,?,?,?)',
                (pid,'in' if change>=0 else 'out',change,new,'Fictional warehouse movement',1,utcnow()))
        for i in range(180):
            pid=rng.randint(1,240)
            product=db.execute('SELECT supplier_id,unit_price,quantity FROM products WHERE id=?',(pid,)).fetchone()
            quantity=rng.randint(3,75)
            status=['draft','submitted','received','cancelled'][i%4]
            db.execute('INSERT INTO purchase_orders(supplier_id,product_id,quantity,unit_cost,status,created_at) VALUES(?,?,?,?,?,?)',
                       (product['supplier_id'],pid,quantity,product['unit_price'],status,utcnow()))
            if status=='received':
                old=product['quantity']; new=old+quantity
                db.execute('UPDATE products SET quantity=? WHERE id=?',(new,pid))
                db.execute('INSERT INTO stock_transactions(product_id,kind,change,balance_after,note,user_id,created_at) VALUES(?,?,?,?,?,?,?)',
                          (pid,'in',quantity,new,f'Demo receipt of PO #{i+1}',1,utcnow()))
        audit(db,'system','seed_demo','Fictional pySupply portfolio data; no real email sent')
    print('Seed completed: 300 employees, 240 products, 24 suppliers, 180 POs, 605 stock transactions.')
    return True

if __name__=='__main__':
    write_employee_csv();seed_demo()
