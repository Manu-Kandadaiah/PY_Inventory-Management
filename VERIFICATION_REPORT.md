# pySupply rebuild — verification summary

**Scope:** A self-contained Python standard-library web app replacing the prior FastAPI/SQLAlchemy/Docker runtime that triggered application-control DLL errors on Windows. Rebranded as **pySupply** with fictional `@pysupply.com` email IDs.

- Passed: Python syntax compilation for all included `.py` sources.
- Passed: Python standard-library `unittest` integration suite (5 tests) verifying real HTTP responses.
- Passed: Login, session cookies, authentication failure, CSRF rejection, product creation, stock in/out/insufficient balance, supplier-linked PO receiving, duplicate receive protection, employee creation/domain rule and CSV exports.
- Passed: SQLite foreign-key check and uniqueness checks, with 300 employees, 240 products, 24 suppliers, 12 categories, 180 purchase orders and 605 stock movements.
- Passed: GET `/health` and static CSS/SVG assets in local HTTP smoke test.
- **Not verified:** Actual Windows/PyCharm execution and application-control policy on the user's machine.
- **Not verified:** Automated visual screenshot testing. The sandbox Chromium browser blocked both localhost and local file navigation under its administrator policy, though HTTP application tests passed.
- **Not claimed:** Production security audit, email delivery, live company data or GitHub upload.

No third-party Python packages, Docker, MySQL or Node tooling are required to run this project. JavaScript is served as static browser code.

- Passed: Fresh setup from an **empty `.env`**, creation of all three `@pysupply.com` demo logins, verification of seeded database relationships, and local web server startup/health check in a clean temporary folder.
