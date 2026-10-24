# pySupply | Inventory & Supplier Management System

**Python | SQLite | HTML | CSS | JavaScript | Inventory Management**

## About My Project

I developed **pySupply**, a web-based Inventory & Supplier Management System designed to simplify inventory operations, supplier management, procurement tracking, and employee record management.

The main objective of this project was to build a centralized platform where businesses can efficiently manage their products, monitor stock availability, maintain supplier information, and track purchase orders.

I developed the application using Python, SQLite, HTML, CSS, and JavaScript, focusing on database management, backend functionality, responsive UI design, and practical business workflows.

The project uses fictional pySupply company data for demonstration and portfolio purposes.

## Business Problem

Businesses often face several operational challenges when managing inventory and suppliers using spreadsheets or manual records.

These challenges include:

- Inaccurate stock quantities and manual entry errors.
- Difficulty identifying low-stock products.
- Poor visibility into supplier and purchase-order information.
- Duplicate or incorrect stock transactions.
- Lack of centralized inventory reports.
- Limited visibility into changes made by different users.

These problems can result in inventory shortages, delayed procurement, inefficient operations, and unreliable business decisions.

## My Solution

To address these challenges, I developed pySupply as a centralized inventory management platform.

| Business Problem | Solution I Developed |
|---|---|
| Manual stock tracking | Digital inventory management with stock transaction records |
| Inventory shortages | Dashboard indicators and low-stock alerts |
| Disconnected supplier information | Centralized supplier records linked to products |
| Purchase-order tracking | Purchase-order creation, submission and receiving |
| Incorrect inventory updates | Stock validation and duplicate-receipt prevention |
| Limited accountability | Role-based permissions and audit history |
| Manual reporting | CSV exports for further business analysis |

The solution demonstrates how software automation can improve inventory visibility, data accuracy, and operational efficiency.

## Key Features

### Inventory Dashboard

A responsive dashboard displaying inventory KPIs, product distribution, stock levels, purchase-order information, and low-stock indicators.

### Product Management

Allows authorized users to add, update, search, and deactivate products while maintaining categories, supplier relationships, unit prices, and reorder levels.

### Supplier Management

Provides centralized supplier information and relationships between suppliers, products, and purchase orders.

### Purchase Order Management

Supports purchase-order creation, submission, receiving, and cancellation. Receiving updates stock quantities while preventing duplicate stock receipts.

### Stock Tracking

Records stock-in, stock-out, and stock-adjustment transactions. The system validates available inventory before allowing stock withdrawals.

### Employee Directory

Includes fictional employee profiles with departments, job titles, and name-based email addresses.

### Role-Based Login

Separate Admin, Manager, and Viewer accounts provide different levels of application access.

### Reporting and Exports

Supports CSV exports of operational records for further analysis using Excel or Python.

## Project Dataset

| Module | Demo Records |
|---|---:|
| Employees | 300 |
| Products | 240 |
| Suppliers | 24 |
| Categories | 12 |
| Purchase Orders | 180 |
| Stock Movements | 605 |

Employee emails follow the format `firstname.lastname@pysupply.com`.

All records are synthetic and are not associated with actual employees, suppliers, or company transactions.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend functionality and business logic |
| SQLite | Local relational database |
| HTML5 | Application structure |
| CSS3 | Responsive design and styling |
| JavaScript | Interactive frontend and API requests |
| JSON APIs | Communication between frontend and backend |
| Python unittest | Automated workflow testing |
| Git and GitHub | Version control and portfolio documentation |

## How to Run the Project

### Requirements

Python 3.11 or newer, PyCharm, and a web browser.

The application uses Python's standard library and does not require MySQL, Docker, or additional Python packages.

### Step 1 — Open in PyCharm

Download or clone the repository and open the extracted project folder in PyCharm.

Configure a supported Python interpreter.

### Step 2 — Initialize the Application

Open the PyCharm terminal and execute:

```powershell
python setup_project.py
```

This creates the SQLite database, local environment configuration, demonstration data, and three login accounts.

Save the generated passwords displayed in the terminal.

### Step 3 — Run the Application

```powershell
python run.py
```

Open:

**http://127.0.0.1:8000/login**

### Demo Login Accounts

| Role | Email |
|---|---|
| Administrator | admin@pysupply.com |
| Manager | manager@pysupply.com |
| Viewer | viewer@pysupply.com |

Passwords are generated securely during setup.

If the administrator password is forgotten:

```powershell
python reset_admin.py
```

### Step 4 — Verify and Test

```powershell
python verify_demo.py
python -m unittest discover -s tests -v
```

## Project Structure

```text
pySupply_Inventory_Supplier_Management/
├── run.py
├── config.py
├── storage.py
├── security.py
├── seed.py
├── setup_project.py
├── reset_admin.py
├── verify_demo.py
├── static/
├── templates/
├── demo_data/
├── tests/
├── .env.example
├── .gitignore
└── README.md
```

## Future Enhancements

The following are planned improvements and are not currently implemented:

1. **Barcode and QR Code Scanning:** Simplify product identification and stock transactions.
2. **Automatic Reorder Notifications:** Notify inventory managers when stock reaches minimum levels.
3. **Supplier Performance Analysis:** Evaluate supplier reliability, delivery time, and pricing.
4. **Purchase Approval Workflow:** Introduce multi-level approvals for procurement.
5. **Multi-Warehouse Management:** Track stock across multiple storage locations.
6. **Inventory Forecasting:** Estimate future inventory requirements using historical consumption.
7. **Advanced Reports:** Generate Excel and PDF reports for management.
8. **Cloud Deployment:** Support secure remote access with production-grade authentication, HTTPS, and backups.

## Skills Demonstrated

Through this project, I demonstrated practical experience in:

- Python backend development and REST-style JSON APIs.
- SQLite database design and relational data management.
- Inventory and procurement business logic.
- Authentication, role permissions, and data validation.
- Responsive web design with HTML, CSS, and JavaScript.
- Automated testing, debugging, and software documentation.

## Conclusion

Developing pySupply helped me strengthen my understanding of real-world inventory management workflows and full-stack Python application development.

The project demonstrates my ability to identify business problems, design software-based solutions, work with relational databases, and create interactive management applications.

**Project Type:** Personal Python Development Portfolio Project

**Company Name:** pySupply (Fictional)

**Status:** Local demonstration application using synthetic data.
