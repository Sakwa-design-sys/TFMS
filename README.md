# KAPKOSGEI OUTGROWERS FARM MANAGEMENT SYSTEM

Full tea-farm management foundation: workers, daily plucking/weighing, historical rates, monthly payroll, advances, deductions, attendance, expenses, vehicles, transport trips, approvals, audit trail and dashboard.

## Local
1. `python -m venv .venv`
2. activate the environment
3. `pip install -r requirements.txt`
4. `flask --app app init-db`
5. `flask --app app run`

Default administrator is `admin` with password from `ADMIN_PASSWORD`, or `Admin@12345` if not set. Change it immediately in production.

## Render
The included `render.yaml` provisions a PostgreSQL database and web service. Set `ADMIN_PASSWORD` during deployment.

## GitHub
Create a repository named `kapkosgei-outgrowers-farm`, commit this project, then connect the repository to Render using the included `render.yaml`.
