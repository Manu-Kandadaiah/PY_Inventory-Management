# Upload pySupply to GitHub

**Recommended repository:** `pysupply-inventory-management`

**Short description:** A Python + SQLite inventory and supplier management platform with procurement, stock tracking, 300 fictional employees, named @pysupply.com email IDs and a responsive dashboard.

## Files to upload

Upload all `.py` files, `static/`, `templates/`, `demo_data/`, `tests/`, `README.md`, `.env.example`, `.gitignore`, and `.github/workflows/ci.yml`.

Do **not** upload `.env`, `pysupply.db`, `.venv/`, caches, credentials, or actual employee records. These are excluded by `.gitignore`.

From an extracted project folder in PyCharm's terminal:

```powershell
git init
git add .
git status
git commit -m "Initial pySupply inventory management portfolio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pysupply-inventory-management.git
git push -u origin main
```

Create the empty GitHub repository first. Replace `YOUR_USERNAME`. You may need to authenticate with GitHub in your browser or Git Credential Manager.

## HR/recruiter review order

Read README overview → review sample CSVs → inspect `static/` and `templates/` → run locally → inspect the tests and transactional inventory logic.

The email addresses ending in `@pysupply.com` are fictional examples, not proof of domain ownership.
