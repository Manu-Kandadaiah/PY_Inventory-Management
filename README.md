# pySupply — Inventory & Supplier Management Platform

**Python · SQLite · Inventory Control · Procurement · Supplier Management · Employee Directory · Responsive Web UI**

> **Portfolio disclosure:** This project uses a fictional **pySupply** organization and entirely synthetic people, inventory, suppliers and orders. The `@pysupply.com` email addresses are invented examples for this demonstration. This app does **not** send email, and ownership of the `pysupply.com` domain is not claimed.

## Overview

pySupply is a full-stack inventory and supplier management demonstration built with **only Python's standard library**, SQLite and vanilla HTML/CSS/JavaScript. It provides a polished local web workspace for tracking products, suppliers, stock movements, purchase orders and employee records, with role checks and an audit trail.

The application was rebuilt from the earlier Inventory & Supplier Management project to **remove SQLAlchemy, Alembic, FastAPI, Argon2, Docker and MySQL runtime dependencies**. Those packages used compiled DLL extensions that were blocked by Windows Application Control on the development computer. The new edition runs directly from `python run.py` without using `pip`.

### What a recruiter can explore

- **Overview dashboard:** summary cards, inventory valuation, stock levels, product distribution, purchase-order pipeline and low-stock alerts
- **Inventory:** add, edit, search and deactivate products; define reorder points and prices
- **Suppliers:** record vendor information and link suppliers to products
- **Purchase orders:** create, submit, receive and cancel orders; receiving updates stock once
- **Stock movements:** stock in, stock out and stock adjustment with balance checks and transaction history
- **Employee directory:** 300 synthetic people across ten departments; email IDs built from their names such as `aarav.sharma@pysupply.com`
- **Categories:** manage product groups and relationships
- **Audit history:** administrator-only view of changes
- **CSV exports:** export products, suppliers, employees, orders, transactions and categories
- **Responsive interface:** custom login, sidebar, tables, forms, badges and mobile layout with original SVG branding

## Sample data included

| Dataset | Quantity |
|---|---:|
| Employees | **300** |
| Products | **240** |
| Suppliers | **24** |
| Product categories | **12** |
| Purchase orders | **180** |
| Stock transactions | **605** |

The files in `demo_data/` are safe, fictional CSV snapshots. Run the one-step setup to create their linked SQLite records. Foreign-key relationships and unique employee emails are checked by the verification script. All data is generated deterministically, so it can be regenerated without relying on an external database server.

## Quick start — Windows / PyCharm

**Requirements:** Python **3.11 or newer**, PyCharm or a terminal, and a web browser. **No pip installation, `.venv`, MySQL, Docker or internet connection is required.**

1. Extract this ZIP and open its project folder in PyCharm.
2. Set a supported Python interpreter in **Settings → Project → Python Interpreter**. Using Python 3.12 is recommended; Python 3.14 is also supported by the standard-library code.
3. From the PyCharm Terminal, run:

```powershell
python setup_project.py
```

This creates a private `.env` file, `pysupply.db`, database tables and the full fictional data set. **It prints newly generated Admin, Manager, and Viewer passwords once. Save them privately.** If you already have a configured `.env`, it preserves valid credentials.

4. Start the local web server:

```powershell
python run.py
```

5. Open **http://127.0.0.1:8000/login**. Log in with `admin@pysupply.com` and the password printed in Step 3. Additional read-only and restricted-access logins are `viewer@pysupply.com` and `manager@pysupply.com` (their generated passwords are also printed).

**Even easier:** Running `python run.py` with no `.env` triggers the one-step setup automatically. We recommend running setup explicitly the first time so you can easily note the generated password.

### Empty or incomplete `.env`?

Run `python setup_project.py` again. It safely fills missing credentials with random values and keeps valid existing values. The reference file is `.env.example`:

```dotenv
COMPANY_NAME=pySupply
DATABASE_PATH=pysupply.db
ADMIN_EMAIL=admin@pysupply.com
ADMIN_PASSWORD=REPLACE_WITH_YOUR_OWN_PASSWORD_12_PLUS
MANAGER_PASSWORD=REPLACE_WITH_YOUR_OWN_PASSWORD_12_PLUS
VIEWER_PASSWORD=REPLACE_WITH_YOUR_OWN_PASSWORD_12_PLUS
SECRET_KEY=REPLACE_WITH_GENERATED_SECRET_AT_LEAST_32_CHARACTERS
HOST=127.0.0.1
PORT=8000
COOKIE_HTTPS_ONLY=false
```

Don't copy these placeholder values as real credentials. `setup_project.py` replaces them.

### Forgotten admin password?

```powershell
python reset_admin.py
```

The command issues a new password and invalidates old login sessions **without deleting employee, supplier or inventory data**.

### Verification & tests

```powershell
python verify_demo.py
python -m unittest discover -s tests -v
```

The application also offers a local health check at `http://127.0.0.1:8000/health`.

## Project structure

```text
pySupply_Inventory_Supplier_Management/
├── run.py                   # HTTP web server and JSON API
├── config.py                # Dependency-free .env reader
├── storage.py               # SQLite schema, queries and transactions
├── security.py              # PBKDF2 password hashing and sessions
├── seed.py                  # Linked fictional data generator
├── setup_project.py         # One-step local setup and credential generation
├── reset_admin.py           # Safe local administrator password reset
├── verify_demo.py           # Counts, email uniqueness and FK checks
├── static/
│   ├── logo.svg             # Original pySupply brand
│   ├── favicon.svg
│   ├── style.css
│   ├── app.js
│   └── login.js
├── templates/
│   ├── login.html
│   └── dashboard.html
├── demo_data/              # Fictional CSVs safe to review on GitHub
├── tests/
│   └── test_workflows.py
├── .github/workflows/ci.yml
├── .env.example             # Reference only; no credentials
├── .gitignore
└── README.md
```

## API examples

The frontend interacts with local JSON routes including `GET /api/me`, `GET /api/stats`, `GET /api/products`, `GET /api/suppliers`, `GET /api/employees`, `POST /api/stock`, `POST /api/orders`, and `POST /api/orders/{id}/status`. Authenticated exports are available at `/api/export/products` and related names.

Mutation requests require an authenticated session and a CSRF token. Sessions use HTTP-only cookies. Passwords use PBKDF2-HMAC-SHA256 with a random salt. SQLite enforces foreign keys, and stock updates and PO receiving are transactional.

## GitHub — what to include or exclude

**Include:** Python source, the `static/` and `templates/` directories, synthetic `demo_data/`, `tests/`, `README.md`, `.gitignore`, `.env.example` and GitHub Actions workflow.

**Do not include:** `.env`, `pysupply.db` (contains hashed local demo credentials), any real employee records, `.venv/`, `__pycache__/`, IDE files, logs or any secret keys.

Create an empty repository called `pysupply-inventory-management` and run:

```powershell
git init
git add .
git status
git commit -m "Build pySupply inventory and supplier management demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pysupply-inventory-management.git
git push -u origin main
```

Replace `YOUR_USERNAME`. **Review `git status`** before committing to confirm that `.env` and database files aren't staged.

## Limits and responsible use

This is a **local portfolio demonstration**, not an internet-exposed ERP application. It has a single SQLite database, a Python development HTTP server and simplified role administration. It has not been penetration-tested or validated as production-ready. If deployed externally, add HTTPS, server-side login rate limiting, robust session rotation, central logging, secure backups, fine-grained authorization and operational monitoring. Demonstration contact addresses use `@pysupply.com` as requested; no actual mail is delivered.

### Testing disclosure

Automated Python tests cover HTTP login, sessions, CRUD, stock insufficiency, order receipt idempotency, employee email constraints and CSV exports. Complete browser testing under Windows and the organization's application-control policy is not guaranteed and must be verified locally. This repository does not claim real production deployment or GitHub upload by the assistant.
