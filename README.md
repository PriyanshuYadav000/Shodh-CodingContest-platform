# Shodh Coding Contest Platform

Backend implementation for the Shodh a Code Backend Engineer Intern take-home assessment.

## Planned stack
- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2 + Alembic
- Docker-based isolated code execution
- PostgreSQL-backed durable job processing
- Pytest + HTTPX

## Assessment stages
1. Contest API and relational data model
2. Asynchronous judging and isolated execution
3. Idempotency, concurrency, recovery, and rejudging
4. Security, performance, and diagnostic evidence

This repository currently contains the initial project scaffold. Application logic and environment setup will be added and verified incrementally.

## Stage 1 problem management

Problems are scoped to both an organization and a contest. All problem routes
require organization membership; create, update, deactivate, and version
history routes require an organizer role.

- `POST /api/v1/organizations/{organization_id}/contests/{contest_id}/problems`
- `GET /api/v1/organizations/{organization_id}/contests/{contest_id}/problems`
- `GET /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}`
- `PATCH /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}`
- `DELETE /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}`
- `GET /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}/versions`

Each create produces problem version 1 and test-suite version 1. A problem
update writes a new immutable problem version and a corresponding test-suite
version. Omitting `test_cases` on update copies the preceding suite; supplying
them creates the suite for that new version. Deactivation is a soft delete.
Problem slugs are unique within a contest and can be changed only through an
update that also creates a new content version.

Participants can view only active problems in published contests. Their
responses contain public sample cases only; hidden test input and expected
output are never serialized in participant responses.
