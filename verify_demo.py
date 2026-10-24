import sys
from storage import init_db,connect

def verify():
    init_db()
    expected={'employees':300,'products':240,'suppliers':24,'categories':12,'purchase_orders':180,'stock_transactions':605}
    with connect() as db:
        db.execute('PRAGMA foreign_keys=ON')
        fk=db.execute('PRAGMA foreign_key_check').fetchall()
        assert not fk, f'Invalid foreign keys: {fk}'
        for name,n in expected.items():
            found=db.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]
            print(f'{name}: {found} (expected {n})')
            assert found==n,(name,found,n)
        assert db.execute('SELECT COUNT(*) FROM employees WHERE email NOT LIKE ?',('%@pysupply.com',)).fetchone()[0]==0
        assert db.execute('SELECT COUNT(DISTINCT email) FROM employees').fetchone()[0]==300
        assert db.execute('SELECT COUNT(*) FROM products WHERE quantity<0').fetchone()[0]==0
    print('PASS: pySupply demo data, email uniqueness, stock, and FK integrity')
if __name__=='__main__':verify()
