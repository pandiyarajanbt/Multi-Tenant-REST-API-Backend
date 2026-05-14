# Multi-Tenant REST API Backend

A production-ready B2B SaaS REST API built with Django REST Framework, featuring multi-tenant data isolation, JWT authentication, role-based access control (RBAC), Redis caching, and full Docker Compose containerisation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                    │
│                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ PostgreSQL│    │  Django API  │    │   Redis   │  │
│  │  :5432   │◄───│  Gunicorn    │───►│  :6379    │  │
│  │          │    │  :8000       │    │  (cache)  │  │
│  └──────────┘    └──────────────┘    └───────────┘  │
└─────────────────────────────────────────────────────┘
```

### Multi-Tenancy Model

Each `User` belongs to an `Organization` (tenant). Every resource (`Project`, `Invitation`) is scoped to an `Organization` via a foreign key. The `TenantMiddleware` resolves the tenant from the JWT on every request, and all querysets are filtered by `organization=request.user.organization` — no cross-tenant data leakage is possible.

### RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full CRUD on all org resources, manage members, send invitations |
| `manager` | Create/update projects, view members |
| `member` | Read-only access to org resources |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2 + Django REST Framework 3.14 |
| Auth | JWT via `djangorestframework-simplejwt` (access + refresh + blacklist) |
| Database | PostgreSQL 15 |
| Cache | Redis 7 via `django-redis` |
| Containerisation | Docker + Docker Compose |
| API Docs | drf-spectacular (OpenAPI 3 / Swagger UI) |
| Web Server | Gunicorn (4 workers) |
| Static Files | WhiteNoise |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2+

### 1. Clone & configure

```bash
git clone <repo-url>
cd Multi-Tenant-REST-API-Backend
cp .env.example .env
# Edit .env — set a strong SECRET_KEY at minimum
```

### 2. Start the stack

```bash
docker compose up --build
```

This will:
- Start PostgreSQL and Redis
- Run `python manage.py migrate`
- Start Gunicorn on port `8000`

### 3. Create a superuser

```bash
docker compose exec api python manage.py createsuperuser
```

### 4. Access

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |
| `http://localhost:8000/admin/` | Django Admin |

---

## Local Development (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Requires a running PostgreSQL and Redis, or change DB to sqlite3 in .env
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

---

## API Reference

### Authentication

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

#### Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `POST` | `/api/auth/register/` | Public | Register a new user |
| `POST` | `/api/auth/login/` | Public | Obtain JWT token pair |
| `POST` | `/api/auth/token/refresh/` | Public | Refresh access token |
| `POST` | `/api/auth/logout/` | Bearer | Blacklist refresh token |
| `GET/PATCH` | `/api/auth/me/` | Bearer | Get/update own profile |

#### Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "full_name": "Jane Doe", "password": "securepass123"}'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

Response:
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

---

### Organization

| Method | URL | Role Required | Description |
|--------|-----|---------------|-------------|
| `GET` | `/api/organization/` | member+ | Get own organization details |
| `PATCH` | `/api/organization/` | admin | Update organization name/slug |

---

### Projects

Cached for 5 minutes per user (varies on `Authorization` header).

| Method | URL | Role Required | Description |
|--------|-----|---------------|-------------|
| `GET` | `/api/projects/` | member+ | List projects (paginated, filterable) |
| `POST` | `/api/projects/` | member+ | Create a project |
| `GET` | `/api/projects/<id>/` | member+ | Get project detail |
| `PATCH` | `/api/projects/<id>/` | member+ | Update project |
| `DELETE` | `/api/projects/<id>/` | admin | Delete project |

#### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by `active`, `archived`, `draft` |
| `search` | string | Search name/description |
| `ordering` | string | `created_at`, `-created_at`, `name` |
| `page` | int | Page number (20 per page) |

```bash
curl http://localhost:8000/api/projects/?status=active&search=api \
  -H "Authorization: Bearer <token>"
```

---

### Members

| Method | URL | Role Required | Description |
|--------|-----|---------------|-------------|
| `GET` | `/api/members/` | member+ | List org members (cached 5 min) |
| `GET` | `/api/members/<id>/` | admin | Get member detail |
| `PATCH` | `/api/members/<id>/` | admin | Update member role |
| `DELETE` | `/api/members/<id>/` | admin | Remove member |

---

### Invitations

| Method | URL | Role Required | Description |
|--------|-----|---------------|-------------|
| `GET` | `/api/invitations/` | admin | List pending invitations |
| `POST` | `/api/invitations/` | admin | Invite a user by email |

```bash
curl -X POST http://localhost:8000/api/invitations/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "role": "manager"}'
```

---

## Redis Caching

Read-heavy list endpoints are cached using `django-redis`:

| Endpoint | Cache TTL | Cache Key Varies On |
|----------|-----------|---------------------|
| `GET /api/projects/` | 5 minutes | `Authorization` header |
| `GET /api/members/` | 5 minutes | `Authorization` header |

Cache is automatically invalidated on the next write or TTL expiry. To manually flush:

```bash
docker compose exec redis redis-cli FLUSHDB
```

---

## Security

- JWT access tokens expire in **15 minutes** (configurable via `JWT_ACCESS_MINUTES`)
- Refresh tokens expire in **7 days** and are **blacklisted on rotation**
- All tenant querysets are scoped — no raw cross-tenant queries possible
- Rate limiting: `30/min` anonymous, `200/min` authenticated
- HSTS, SSL redirect, and secure cookies enabled when `DEBUG=False`
- Passwords validated against Django's built-in validators (min length, common passwords)

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | **Required.** Django secret key |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `DB_NAME` | `tenantdb` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_HOST` | `db` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://redis:6379/1` | Redis connection URL |
| `JWT_ACCESS_MINUTES` | `15` | Access token lifetime (minutes) |
| `JWT_REFRESH_DAYS` | `7` | Refresh token lifetime (days) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Project Structure

```
Multi-Tenant-REST-API-Backend/
├── apps/
│   ├── accounts/          # Custom User model, JWT auth, registration
│   │   ├── models.py      # User, Organization
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── organizations/     # Tenant-scoped resources
│   │   ├── models.py      # Project, Invitation
│   │   ├── serializers.py
│   │   ├── views.py       # Redis-cached list views
│   │   └── urls.py
│   └── core/
│       ├── middleware.py  # TenantMiddleware
│       └── permissions.py # IsOrgAdmin, IsOrgMember, IsSameTenant
├── tenant/
│   ├── settings.py        # Production settings
│   └── urls.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Running Tests

```bash
docker compose exec api python manage.py test
```

---

## Production Deployment Checklist

- [ ] Set a strong, unique `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Use a managed PostgreSQL instance (e.g. AWS RDS)
- [ ] Use a managed Redis instance (e.g. AWS ElastiCache)
- [ ] Put Nginx or a load balancer in front of Gunicorn
- [ ] Enable HTTPS — `SECURE_SSL_REDIRECT=True` is already set for non-debug
- [ ] Set up log aggregation (CloudWatch, Datadog, etc.)
- [ ] Configure automated DB backups
