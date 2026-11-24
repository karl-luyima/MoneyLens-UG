
# MoneyLens UG – Deployment Guide

## 1. Overview

MoneyLens UG is a personal finance insights platform for Ugandan mobile money users.

The application consists of three main services:

- **FastAPI:** Backend API responsible for authentication, transaction processing, categorisation and financial insights.
- **Streamlit:** Frontend dashboard for uploading transactions, viewing financial summaries and managing categories.
- **PostgreSQL:** Relational database for storing users, transactions, categories and financial records.

The application can be deployed using Render, Railway or AWS.

---

## 2. Deployment Requirements

Before deployment, ensure you have:

- Python 3.12
- PostgreSQL 16 or later
- Git and GitHub
- A configured production environment
- A secure application secret key
- Access to your deployment provider

---

## 3. Environment Configuration

Create environment variables in the deployment provider.

Required variables:

| Variable | Description |
|---|---|
| APP_NAME | Application name |
| APP_ENV | Set to production |
| DEBUG | Set to false |
| DATABASE_URL | PostgreSQL connection URL |
| SECRET_KEY | Secure random application secret |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token lifetime |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token lifetime |
| CORS_ORIGINS | Allowed frontend origins |
| ENABLE_LLM | Enable or disable optional AI functionality |
| ANTHROPIC_API_KEY | Optional AI API key |

Never commit `.env` or production credentials to GitHub.

Use `.env.example` as a reference when configuring deployment variables.

---

## 4. Option A: Deploying with Render

### Step 1: Create a PostgreSQL database

1. Create a Render account.
2. Create a new PostgreSQL database.
3. Select an appropriate region.
4. Copy the internal database connection URL.

Keep database credentials private.

### Step 2: Deploy the FastAPI backend

1. Connect your GitHub repository.
2. Create a new Web Service.
3. Select the MoneyLens-UG repository.
4. Configure:

**Build command:**

```bash
pip install .
```

**Start command:**

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Add the required environment variables.
6. Set `APP_ENV=production`.
7. Set `DEBUG=false`.

Configure the health check path as:

```text
/health
```

### Step 3: Deploy the Streamlit frontend

Create another Web Service using the same GitHub repository.

**Build command:**

```bash
pip install . && pip install -r frontend/requirements.txt
```

**Start command:**

```bash
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port $PORT
```

Configure:

```text
MONEYLENS_API_URL=https://your-api-domain/api/v1
STREAMLIT_SERVER_HEADLESS=true
```

Replace the API domain with the actual deployed backend address.

### Step 4: Configure CORS

Set `CORS_ORIGINS` to the actual frontend origin.

For example:

```text
CORS_ORIGINS=["https://your-frontend-domain"]
```

Do not use unrestricted origins in production.

---

## 5. Option B: Deploying with Railway

Railway can host the backend, frontend and PostgreSQL database.

### Step 1: Create a project

1. Create a Railway account.
2. Create a new project.
3. Connect the GitHub repository.
4. Add a PostgreSQL database service.

### Step 2: Configure the backend

Configure the backend service to use the project Dockerfile with the `api` build target.

Use the following startup command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the PostgreSQL connection URL and application environment variables.

### Step 3: Configure the frontend

Create another service using the same repository.

Select the `frontend` Docker build target.

Configure:

```text
MONEYLENS_API_URL=https://your-api-domain/api/v1
STREAMLIT_SERVER_HEADLESS=true
```

Ensure the frontend uses the deployed backend URL rather than a localhost address.

### Step 4: Configure health checks

Use:

```text
/health
```

for the backend health check.

Verify that both services can communicate successfully.

---

## 6. Option C: AWS Deployment

For a more advanced cloud deployment, AWS provides several suitable services.

Suggested architecture:

- **Amazon ECS:** Runs the FastAPI and Streamlit Docker containers.
- **Amazon ECR:** Stores Docker images.
- **Amazon RDS for PostgreSQL:** Managed relational database.
- **Application Load Balancer:** Routes incoming requests.
- **AWS Secrets Manager:** Stores sensitive application credentials.
- **Amazon CloudWatch:** Collects application logs and monitoring information.

### Deployment process

1. Build the Docker images.
2. Push images to Amazon ECR.
3. Provision an RDS PostgreSQL database.
4. Configure ECS task definitions.
5. Supply environment variables and secrets.
6. Deploy the backend and frontend services.
7. Configure the load balancer and health checks.
8. Monitor application logs through CloudWatch.

AWS deployment may require additional infrastructure configuration and cloud expenditure.

---

## 7. Database Migrations

MoneyLens UG uses Alembic to manage database schema changes.

Before starting the API in production, apply migrations:

```bash
alembic upgrade head
```

To inspect the current migration version:

```bash
alembic current
```

To inspect migration history:

```bash
alembic history
```

Always back up the production database before applying significant schema changes.

---

## 8. Docker Deployment

The repository includes:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

Build and start the application:

```bash
docker compose up --build -d
```

Check running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f api
```

Check API health:

```text
http://localhost:8000/health
```

Open the local dashboard:

```text
http://localhost:8502
```

Do not remove persistent database volumes when restarting the application.

---

## 9. Production Security

Before making MoneyLens UG publicly available:

- Set `DEBUG=false`.
- Use a strong, unique `SECRET_KEY`.
- Store credentials in the deployment provider's secret manager.
- Restrict CORS to trusted frontend origins.
- Use HTTPS for public endpoints.
- Keep dependencies updated.
- Protect database credentials.
- Use database backups.
- Avoid logging passwords, access tokens or sensitive transaction information.
- Monitor application errors and service health.

---

## 10. Post-Deployment Verification

After deployment, verify the following:

| Component | Verification |
|---|---|
| FastAPI | API documentation loads |
| Health endpoint | Returns healthy status |
| PostgreSQL | Database connection succeeds |
| Alembic | Migrations are applied |
| Authentication | Registration and login work |
| Transaction processing | Upload and parsing work |
| Categorisation | Transactions receive categories |
| Financial insights | Dashboard displays summaries |
| Streamlit | Frontend communicates with API |
| Logging | Structured JSON logs are available |

Useful backend endpoints:

```text
/
 /health
 /docs
 /api/v1
```

The API documentation is normally available at `/docs`.

---

## 11. Deployment Considerations

Render and Railway provide relatively straightforward deployment workflows for smaller applications.

AWS offers greater infrastructure flexibility and scalability but requires more configuration and ongoing management.

For an initial portfolio deployment, Render or Railway is a reasonable starting point.

---

**Project:** MoneyLens UG  
**Backend:** FastAPI  
**Frontend:** Streamlit  
**Database:** PostgreSQL  
**Migrations:** Alembic  
**Containerisation:** Docker  
**Language:** Python 3.12
