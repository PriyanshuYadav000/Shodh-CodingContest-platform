# Shodh Coding Contest Platform

A backend for a coding-contest platform, built for the Shodh a Code Backend Engineer Intern take-home assessment.

The project uses a layered FastAPI architecture and PostgreSQL for durable application data and submission queue state. Python submissions are executed in isolated Docker containers.

> **Implementation status:** Stage 1 is implemented. Stage 2 includes the PostgreSQL queue, Docker runner, judge service, and a real Docker-backed judge integration test. Full Docker Compose end-to-end startup and execution should be re-verified on the target machine. Stage 3 and Stage 4 are planned work and are not represented as completed in this README.

## Contents

- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Implemented functionality](#implemented-functionality)
- [Submission and judging flow](#submission-and-judging-flow)
- [Local setup](#local-setup)
- [Docker Compose](#docker-compose)
- [Demo accounts and seed data](#demo-accounts-and-seed-data)
- [API overview](#api-overview)
- [Running tests](#running-tests)
- [Security and current limitations](#security-and-current-limitations)
- [Reliability and operational-readiness roadmap](#reliability-and-operational-readiness-roadmap)

## Technology stack

- Python 3.12
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2
- Alembic
- Docker
- Pytest
- Ruff

Only Python 3 is currently supported for submitted programs.

## Architecture

The application follows a layered structure:

```text
src/shodh/
  config/          Settings
  controllers/     Route/controller coordination
  database/        SQLAlchemy base and sessions
  dependencies/    Authentication and organization dependencies
  models/          SQLAlchemy models
  repositories/    Database access
  routes/          FastAPI endpoints
  schemas/         Request and response schemas
  security/        Password and token helpers
  services/        Business logic, judge and code runner
  worker.py        PostgreSQL-backed submission worker
  seed.py          Deterministic development seed data

migrations/        Alembic migrations
tests/             Unit and PostgreSQL integration tests
Dockerfile
docker-compose.yml
```

## Implemented functionality

### Stage 1 — Contest API and relational data

- Authentication and organization membership.
- Organizations, contests and participant registration.
- Organizer and participant role checks.
- Problem management with immutable problem versions.
- Immutable test-suite versions associated with problem versions.
- Submissions pinned to the exact problem and test-suite versions used at submission time.
- Verdict-attempt history.
- Participant and organizer submission visibility rules.
- Contest leaderboard.

Problem routes are scoped to an organization and contest. Problem creation, updates, deactivation and version history require organizer privileges. Participants see active problems in published contests and receive public sample cases only.

### Stage 2 — Asynchronous judging and isolated execution

#### PostgreSQL submission queue

Submissions are persisted with a queue status. The worker claims queued rows using PostgreSQL row locking with `FOR UPDATE SKIP LOCKED`, changes the status to `running`, and records the start time.

The submission lifecycle uses:

- `queued`
- `running`
- `completed`
- `failed`

The queue-state Alembic migration adds worker timestamps and updates the status constraint while retaining existing submission rows.

#### Docker Python runner

The runner executes Python 3 submissions in short-lived Docker containers. Its configured sandbox includes:

- Network disabled.
- CPU and memory limits.
- Process-count limit.
- Read-only container filesystem.
- Limited writable `/tmp`.
- Non-root user.
- All Linux capabilities dropped.
- `no-new-privileges`.
- Read-only source bind mount.
- Wall-clock timeout.
- Bounded combined stdout/stderr capture.
- Container cleanup after execution.

The runner distinguishes compilation, runtime, time-limit, memory-limit, output-limit and infrastructure failures.

#### Judge service

The judge service loads the problem version and test-suite version pinned to a submission, runs test cases in ordinal order, compares normalized output and stores a verdict attempt using the existing verdict-history model.

Supported verdict categories include:

- Accepted
- Wrong Answer
- Compilation Error
- Runtime Error
- Time Limit Exceeded
- Memory Limit Exceeded
- Output Limit Exceeded
- Infrastructure Error

Hidden test contents are not written into judge diagnostics.

#### Verification performed

The development checks recorded during implementation include:

- 49 automated tests passing.
- A real Docker-backed PostgreSQL judge integration test passing.
- Manual runner checks for successful execution, runtime exception, timeout, output limit and memory limit.
- A Docker cleanup check showing no leftover runner containers.

These are development-session results, not a claim that every environment or the full Compose deployment has been independently validated.

## Submission and judging flow

The intended Stage 2 flow is:

1. A participant submits source code through the submissions API.
2. The submission row is stored with status `queued` and pinned version identifiers.
3. A worker claims a queued submission using PostgreSQL locking.
4. The judge loads the pinned problem and test-suite versions.
5. Each test case is executed in an isolated Docker container.
6. Output is compared with the expected output.
7. A verdict attempt is persisted and the submission lifecycle status is updated.

Run the worker locally with:

```bash
PYTHONPATH=src .venv/bin/python -m shodh.worker
```

The worker requires the application environment and database to be configured. Docker must also be available to the process running the code runner.

## Local setup

### Prerequisites

- Python 3.12
- PostgreSQL 17
- Docker Engine or Docker Desktop (for judging)
- Git

### 1. Clone and enter the repository

```bash
git clone https://github.com/PriyanshuYadav000/Shodh-CodingContest-platform.git
cd Shodh-CodingContest-platform
```

### 2. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Set a local PostgreSQL URL and a strong JWT secret in `.env`. For example:

```dotenv
POSTGRES_DB=shodh_db
POSTGRES_USER=shodh_user
POSTGRES_PASSWORD=change-this-local-password

DATABASE_URL=postgresql+psycopg://shodh_user:change-this-local-password@127.0.0.1:5433/shodh_db
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

Use URL-encoded credentials if the password contains reserved URL characters. Never commit `.env` or real credentials.

### 4. Apply migrations and seed development data

Ensure PostgreSQL is running and the configured database exists, then run:

```bash
alembic upgrade head
PYTHONPATH=src python -m shodh.seed
```

### 5. Start the API

```bash
PYTHONPATH=src uvicorn shodh.main:app --reload
```

The API is available at:

- Root: http://127.0.0.1:8000/
- OpenAPI UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 6. Start the worker in a separate terminal

Activate the virtual environment, ensure the same `.env` is available, and run:

```bash
PYTHONPATH=src python -m shodh.worker
```

## Docker Compose

The repository contains a Compose configuration intended to start:

- PostgreSQL 17.
- A one-shot initialization service that applies Alembic migrations and runs deterministic seed data.
- FastAPI.
- The background worker.

The worker requires access to the host Docker daemon to launch isolated execution containers. The Docker socket is mounted into the worker service only; it must never be mounted into submitted-code containers.

Build and start the stack:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps -a
```

Inspect startup:

```bash
docker compose logs init
docker compose logs api
docker compose logs worker
```

Verify the API:

```bash
curl http://127.0.0.1:8000/
```

Expected root response:

```json
{
  "message": "Shodh Coding Contest Platform API",
  "status": "running"
}
```

**Deployment note:** Docker Desktop bind-mount behavior must be checked for the worker-created temporary source directory when the Docker daemon is remote from the worker container. Confirm an actual API-created submission is judged successfully through the Compose worker before treating Compose execution as fully verified.

To stop the stack:

```bash
docker compose down
```

The named PostgreSQL volume is retained by this command. To remove persistent database data, Docker requires a separate explicit volume-removal action; do not remove it if you need to preserve local data.

## Demo accounts and seed data

The deterministic seed script creates these local development accounts:

| Role | Email | Password |
|---|---|---|
| Organizer | `organizer@example.test` | `OrganizerPass123!` |
| Participant | `participant@example.test` | `ParticipantPass123!` |

The seed data includes two organizations, a published contest, a draft contest, sample problems and test cases.

These credentials are for local development only. Change or replace them before any shared or deployed environment.

## API overview

The API prefix is `/api/v1`. The interactive OpenAPI documentation at `/docs` is the source of truth for request schemas and response models.

Main resource groups:

| Resource | Typical operations |
|---|---|
| Authentication | Register/login and authenticated identity |
| Organizations | Organization details and membership |
| Contests | Create, list, publish and retrieve contests |
| Participation | Register participants for contests |
| Problems | Organizer CRUD, public problem listing and version history |
| Submissions | Create, list and retrieve submissions |
| Verdict history | Retrieve attempts visible to the caller |
| Leaderboard | Retrieve contest standings |

Problem endpoints:

```text
POST   /api/v1/organizations/{organization_id}/contests/{contest_id}/problems
GET    /api/v1/organizations/{organization_id}/contests/{contest_id}/problems
GET    /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}
PATCH  /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}
DELETE /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}
GET    /api/v1/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}/versions
```

Submission and leaderboard endpoints:

```text
POST /api/v1/organizations/{organization_id}/contests/{contest_id}/submissions
GET  /api/v1/organizations/{organization_id}/contests/{contest_id}/submissions
GET  /api/v1/organizations/{organization_id}/contests/{contest_id}/submissions/{submission_id}
GET  /api/v1/organizations/{organization_id}/contests/{contest_id}/submissions/{submission_id}/verdicts
GET  /api/v1/organizations/{organization_id}/contests/{contest_id}/leaderboard
```

### Example submission request

The exact JSON schema is available through `GET /openapi.json` or Swagger UI. A representative request body is:

```json
{
  "problem_id": "00000000-0000-0000-0000-000000000000",
  "source_code": "n = int(input())\nprint(n * 2)",
  "language": "python"
}
```

Use a real problem ID from the seeded contest or a problem created through the API. Authenticate and supply the organization and contest IDs in the URL as required by the API.

## Running tests

Run static checks and the regular test suite:

```bash
.venv/bin/ruff check src tests
.venv/bin/python -m compileall -q src tests
.venv/bin/pytest -q
```

The PostgreSQL integration tests require a reachable database configured through `DATABASE_URL`.

The Docker-backed judge integration test is opt-in:

```bash
RUN_DOCKER_TESTS=1 .venv/bin/pytest -q \
  tests/test_stage1_postgres_integration.py::test_real_docker_judge_accepts_submission
```

The Docker daemon must be running and the configured Python image must be available or pullable. The regular unit/integration suite and the opt-in real Docker test are separate checks.

## Security and current limitations

- Participants should only be able to view their own submissions; organizers can inspect submissions within their authorized organization/contest scope.
- Participant problem responses expose public samples, not hidden test inputs or expected outputs.
- Judge diagnostics must not include hidden test contents.
- The runner uses a non-root user, no network, resource limits, a read-only root filesystem, dropped capabilities and a limited temporary filesystem.
- The worker's Docker daemon access is a privileged operational capability. Protect the worker host and Docker socket.
- Python 3 is the only supported submitted language.
- The current implementation has not yet completed the full Stage 3 reliability requirements or the Stage 4 security/performance evidence requirements.
- Compose-level bind-mount execution from the containerized worker must be verified on the actual target environment.

## Reliability and operational-readiness roadmap

The first two assessment stages establish the contest domain, immutable problem/test versioning, a PostgreSQL-backed submission queue, isolated Python execution and basic verdict persistence. The following work extends that foundation toward production-grade reliability and provides repeatable evidence for the assessment.

### Stage 3 — Reliability and concurrency

The reliability work is scoped around PostgreSQL transactions and the existing submission/verdict models:

- **Idempotent submission creation:** persist an idempotency key and a canonical request fingerprint scoped to the submitting user and contest. Return the original submission for an equivalent retry and reject reuse with different parameters.
- **Concurrent workers:** allow independent worker processes to claim jobs safely with row locking and attempt identities, so one logical attempt cannot be applied twice.
- **Retry and recovery policy:** bound retries, track failures and recover abandoned jobs without leaving submissions indefinitely in the running state.
- **Safe rejudging:** let an authorized organizer select explicit immutable problem and test-suite versions, preserve prior attempts and identify the authoritative attempt.
- **Leaderboard consistency:** derive standings from authoritative verdict records, support out-of-order completion and provide a rebuild/check path that agrees with the serving API.

**Completion evidence to produce:** migration review, idempotency tests (equivalent and conflicting requests, including after restart), multi-worker race tests, retry/recovery tests, rejudge ordering tests and leaderboard rebuild comparisons.

### Stage 4 — Security, performance and diagnostics

The final stage focuses on verifying the security boundaries and measuring the system under a repeatable workload:

- **Authorization:** test cross-organization access denial and participant attempts to invoke organizer-only operations.
- **Data protection:** verify that source code, submission details, judge diagnostics and hidden test data are disclosed only to authorized callers and are not leaked through logs or participant responses.
- **Concurrent workload:** exercise overlapping submission requests and leaderboard reads with at least two independent application/worker processes.
- **Performance measurements:** record dataset size, concurrency, machine resources and execution mode; measure API p50, p95 and p99 latency, throughput, errors, queue delay and execution time separately.
- **Database analysis:** capture an EXPLAIN plan for a measured bottleneck, apply one justified optimization and compare before/after results under the same workload, followed by correctness checks.
- **Diagnostics and recovery:** use structured logs with request, submission and attempt identifiers, then demonstrate a controlled infrastructure failure and successful recovery.
- **Submission documentation:** prepare a technical report of no more than four pages and an AI usage note of no more than one page.

**Completion evidence to produce:** authorization/security tests, saved workload results tied to a commit and configuration, query-plan evidence, before/after measurements, structured-log examples, a failure/recovery test and the two assessment documents.

### Delivery status

Stage 3 and Stage 4 are the remaining assessment scope. Their requirements and expected evidence are specified here to make the intended completion criteria clear; they should only be marked complete after the corresponding implementation, tests and measurements have been added to the repository.
