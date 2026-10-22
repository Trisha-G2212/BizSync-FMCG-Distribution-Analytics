# BizSync — Enterprise FMCG Distribution & Analytics Platform

**React · FastAPI · Python · PostgreSQL · REST APIs · Docker · Excel Analytics**

BizSync is a full-stack FMCG (Fast-Moving Consumer Goods) distribution and analytics application for managing products, retailers, distributors, orders, inventory, Excel imports, and operational issues. It brings everyday distribution workflows together with business dashboards and reporting.

> **Project status:** Completed as a 15-phase development project. The screenshots below show a locally running application with sample data; they do not represent a publicly hosted demo.

## Application Screenshots

### Analytics Dashboard

![BizSync analytics dashboard showing revenue, orders, inventory KPIs and charts](docs/screenshots/dashboard.png)

The dashboard summarizes revenue, orders, products, retailers, distributors, stock levels, and pending orders. It also visualizes sales trends, revenue by category, top products, and top retailers.

### Excel Data Import & Validation

![Excel import results with processed records, failures and row-level errors](docs/screenshots/excel-import.png)

Excel import supports structured uploads and displays imported records, duplicates, invalid rows, and downloadable error reports. The example screenshot shows 6 records processed, 3 imported, and 3 failed.

### Troubleshooting & Issue Tracking

![BizSync issue tracker with severity and status filters](docs/screenshots/troubleshooting.png)

The troubleshooting module tracks issues by module, severity, and resolution status, supporting user acceptance testing (UAT) and root-cause analysis.

## Key Features

- **Products & inventory:** Maintain product records, monitor stock, and identify low-stock items.
- **Retailers & distributors:** Manage FMCG distribution participants.
- **Orders:** Create and confirm orders with transaction-aware inventory handling.
- **Sales analytics:** Review revenue KPIs, sales trends, product performance, and retailer performance.
- **Excel import:** Validate spreadsheet records and produce actionable row-level error reports.
- **Authentication:** JWT-based authentication and role-based access control.
- **Issue tracking:** Record and review operational issues, severity, and resolution status.
- **Testing & documentation:** Automated tests, UAT scenarios, API documentation, and technical design notes.
- **Docker deployment:** Run frontend, backend, and PostgreSQL together using Docker Compose.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Frontend | React, JavaScript |
| Backend | Python, FastAPI |
| API | REST, OpenAPI / Swagger UI |
| Database | PostgreSQL |
| Authentication | JWT and role-based access control |
| Data processing | Python, Pandas, Excel files |
| Testing | Pytest, user acceptance testing |
| Deployment | Docker, Docker Compose |
| Version control | Git, GitHub |

## Architecture

```text
Browser / React frontend (port 3000)
              |
              | REST / HTTP
              v
FastAPI backend (port 8000)
              |
       API routers
              |
       Service layer
              |
     Repository layer
              |
              v
PostgreSQL database (port 5432)
```

The backend separates HTTP request handling, business logic, and database access into routers, services, and repositories. For implementation details, see [Architecture](docs/architecture.md).

## Repository Structure

```text
bizsync/
├── backend/             # FastAPI application and backend dependencies
├── database/            # Database-related resources
├── docs/                # Architecture, API, schema, troubleshooting, screenshots
│   └── screenshots/
│       ├── dashboard.png
│       ├── excel-import.png
│       ├── troubleshooting.png
│       └── docker-containers.png
├── frontend/            # React application
├── sample_data/         # Example data for testing/imports
├── tests/               # Test resources
├── .env.example         # Environment variable template
├── .gitignore           # Git exclusion rules
├── docker-compose.yml   # Multi-container configuration
└── README.md
```

## Getting Started — Docker (Recommended)

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### 1. Clone the repository

```powershell
git clone https://github.com/Trisha-G2212/BizSync-FMCG-Distribution-Analytics.git
cd BizSync-FMCG-Distribution-Analytics
```

Replace `Trisha-G2212` with your GitHub username. If you downloaded the project as a ZIP instead, extract it and open a terminal inside the folder containing `docker-compose.yml`.

### 2. Create the environment file

In PowerShell, from the repository root:

```powershell
Copy-Item .env.example .env
```

Review `.env` and adjust settings for your local machine. **Never commit real `.env` files, passwords, API keys, or private business data.**

### 3. Start all services

```powershell
docker compose up --build -d
```

Check the services:

```powershell
docker compose ps
```

### 4. Open the application

When the containers are healthy, use the ports shown in the Docker setup screenshot:

| Service | Local URL / port |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| PostgreSQL | `localhost:5432` (database connection, not a web page) |

**Note:** These are the ports visible in the supplied Docker Desktop screenshot. If your final Compose configuration uses different mappings, follow `docker compose ps` instead.

### 5. Stop or restart the project

```powershell
# Stop containers without deleting database volumes
docker compose down

# Start again
docker compose up -d

# View logs
docker compose logs -f
```

Avoid `docker compose down -v` unless you intentionally want to remove Compose-managed volumes, which may include your database data.

### Docker Deployment Screenshot

![Docker Desktop showing BizSync PostgreSQL, backend and frontend containers running](docs/screenshots/docker-containers.png)

## Local Development (Without Docker)

For manual development, install Python, Node.js/npm, and PostgreSQL first, and configure a working local database and `.env` file.

### Backend — Windows PowerShell

From the repository root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

After configuring PostgreSQL and the environment variables, the project's previously documented setup used:

```powershell
python -m app.create_tables
python -m app.seed_data
uvicorn app.main:app --reload
```

These initialization module names come from the earlier project instructions and should be checked against the actual final `backend/app` directory before use. Database seeding is usually a one-time setup operation.

### Frontend — separate PowerShell terminal

From the repository root:

```powershell
cd frontend
npm install
npm start
```

The `npm start` command was described in the earlier BizSync run instructions. Verify the scripts in `frontend/package.json`; if the project instead defines `dev`, use `npm run dev`.

## API Documentation

FastAPI automatically exposes interactive API documentation when the backend is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

The complete endpoint reference is in [API Documentation](docs/api-documentation.md). Use Swagger to inspect actual request bodies, response schemas, and authentication requirements.

## Testing & UAT

The development process included **15 UAT test cases** and automated backend tests, including coverage of application workflows and validation. From the backend folder with dependencies installed, a typical test command is:

```powershell
python -m pytest
```

Some tests may require an initialized test database or additional environment variables. Consult the repository's test configuration and documentation before running the full suite.

## Engineering Challenges & Troubleshooting

The project development notes identify several issues investigated during implementation:

- Dashboard request fan-out and inconsistent KPI updates
- Pandas / psycopg2 data integration issues
- PostgreSQL container health-check configuration
- Validation gaps for module field length
- Order confirmation and inventory consistency

The [Troubleshooting Guide](docs/troubleshooting.md) records the detailed root-cause analysis and fixes.

## Further Documentation

- [System Architecture](docs/architecture.md)
- [Database Schema](docs/database-schema.md)
- [API Documentation](docs/api-documentation.md)
- [Troubleshooting & Root-Cause Analysis](docs/troubleshooting.md)

## Demo Walkthrough

For a short project demonstration:

1. Start Docker Desktop and run `docker compose up -d`.
2. Open http://localhost:3000 and sign in using a configured demo account.
3. Show dashboard KPIs, trends, and category breakdowns.
4. Explore products, retailers, distributors, and inventory.
5. Demonstrate order creation and explain inventory consistency controls.
6. Import a sample Excel sheet and review validation errors.
7. Open Troubleshooting to discuss tracked defects and resolutions.
8. Show Swagger UI and the Docker containers to explain the technical architecture.

**Demo credentials:** Use the sample accounts defined in your project's seed data or original README. Do not publish real passwords or production credentials.

## Potential Enhancements

- Sales and demand forecasting
- Automated low-stock notifications
- More advanced retailer and distributor analytics
- CI/CD pipeline and automated deployment
- Enhanced audit logging and monitoring

## About This Project

BizSync demonstrates practical full-stack engineering across API development, relational database design, transactional inventory workflows, Excel validation, SQL-based reporting, Docker deployment, automated testing, UAT, and technical documentation.

---

**Note for maintainers:** Confirm the exact local setup scripts, demo accounts, and test prerequisites against the final project files before publishing. This README intentionally avoids inventing credentials or unverified endpoint lists.
