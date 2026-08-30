# Green Star Tea Estate Management System

GitHub + Render ready Flask/PostgreSQL web application for online tea-estate operations.

## Modules
Dashboard, estates, fields, workers, tea rates, plucking, factory intake, production/grades, inventory/stock ledger, buyers, tea sales, attendance, advances, deductions, payroll, expenses, vehicles, transport trips, reports, users and audit log.

## Deploy to Render
1. Create a GitHub repository.
2. Upload the contents of this folder to the repository root.
3. In Render select **New + → Blueprint** and connect the repository.
4. Render reads `render.yaml` and creates the web service and PostgreSQL database.
5. Set `ADMIN_PASSWORD` to a strong password when prompted.
6. Deploy and open the generated `onrender.com` URL.
7. Login: username `admin`, password = your `ADMIN_PASSWORD`.

Do not commit secrets. The default local password is `Admin@12345`; change it immediately.

## Local
pip install -r requirements.txt
flask --app app init-db
flask --app app run
