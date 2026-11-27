
# Customer Management API

A RESTful Customer Management API built using Python, FastAPI, PostgreSQL, SQLAlchemy, and Alembic.

The application provides customer CRUD operations, API key authentication, pagination, secure webhook verification using HMAC-SHA256, and automated integration testing.

## Features

- Create, read, update, and delete customers.
- API key authentication using X-API-Key.
- Pagination for customer listing.
- PostgreSQL database integration.
- SQLAlchemy ORM.
- Database migrations using Alembic.
- Secure webhook receiver using HMAC-SHA256.
- Background event processing using FastAPI BackgroundTasks.
- Automated integration tests using Pytest and TestClient.
- Separate SQLite test database.
- Code coverage reporting using pytest-cov.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Pytest
- HTTPX
- pytest-cov

## Project Structure

```text
customer-management-api/
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── schemas.py
│
├── tests/
│   └── test_api.py
│
├── alembic/
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
├── README.md
└── test_webhook.py
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/sivaprakashmyoho/customer-management-api.git
cd customer-management-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql://username:password@localhost:5432/customer_db
API_KEY=your-secret-api-key
WEBHOOK_SECRET=your-secret-webhook-key
```

Replace the database credentials with your actual PostgreSQL configuration.

Never commit your real `.env` file or secrets.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the application

```bash
uvicorn src.main:app --reload
```

API URL:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API and database health |
| POST | `/customers` | Create a customer |
| GET | `/customers` | Get all customers |
| GET | `/customers/{customer_id}` | Get customer by ID |
| PUT | `/customers/{customer_id}` | Update customer |
| DELETE | `/customers/{customer_id}` | Delete customer |
| POST | `/webhooks/customer-events` | Receive customer webhook events |

## Authentication

Customer CRUD endpoints require an API key.

Include this request header:

```text
X-API-Key: your-secret-api-key
```

Requests with missing or invalid API keys receive HTTP 401.

## Pagination

Example:

```text
GET /customers?page=1&per_page=10
```

- `page`: Page number.
- `per_page`: Number of customers per page.

## Webhook Security

The webhook endpoint is:

```text
POST /webhooks/customer-events
```

It validates incoming requests using HMAC-SHA256.

The sender must calculate a signature using the shared webhook secret and the exact raw request body.

Required header:

```text
X-Signature: <generated-hmac-signature>
```

- Valid signature: HTTP 200.
- Invalid signature: HTTP 401.
- Missing signature: HTTP 401.
- Valid signature with invalid JSON: HTTP 400.

Accepted events are scheduled for background processing.

## Integration Testing

The project uses:

- Pytest
- FastAPI TestClient
- SQLite in-memory test database
- Pytest fixtures
- Dependency overrides

Tests run against a separate SQLite database, keeping the application PostgreSQL database isolated.

Run all tests:

```bash
pytest -v
```

Run tests with code coverage:

```bash
pytest --cov=src
```

## Test Results

Latest local test execution:

- Total tests: 19
- Passed: 19
- Failed: 0
- Overall code coverage: 93%

| Module | Coverage |
|---|---:|
| src/main.py | 95% |
| src/database.py | 71% |
| src/models.py | 100% |
| src/schemas.py | 100% |
| Overall | 93% |

## Error Handling

The API handles the following HTTP status codes:

| Status | Description |
|---|---|
| 200 | Successful request |
| 201 | Customer created |
| 400 | Invalid pagination parameters |
| 401 | Invalid or missing authentication |
| 404 | Customer not found |
| 409 | Duplicate customer email |
| 422 | Invalid request validation |
| 503 | Database connection failure |

## Future Improvements

- GitHub Actions CI/CD integration.
- PostgreSQL service container for automated testing.
- Additional test coverage.
- Production deployment.
