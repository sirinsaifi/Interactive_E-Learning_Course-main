# Alembic migrations

Generate a new revision:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
alembic upgrade head
```

Roll back one step:

```bash
alembic downgrade -1
```

> All commands must be run from the `backend/` directory with the project's
> Python environment active and a valid `.env` file in place.
