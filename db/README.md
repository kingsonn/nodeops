# Database

This directory contains database schemas, migrations, and seed data.

## Structure

- `schema.sql` - Database schema definition
- `seed_data.sql` - Sample data for development
- `migrations/` - Database migration files

## Setup

For local development with PostgreSQL:

```bash
psql -U postgres -d autodefi < schema.sql
psql -U postgres -d autodefi < seed_data.sql
```

For production, use Alembic migrations:

```bash
alembic upgrade head
```
