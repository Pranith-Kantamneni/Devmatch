# DevMatch

A developer matching and recommendation platform. Users create rich developer
profiles (skills, technologies, projects, experience, interests), and the
system converts each profile into a vector embedding to find and rank similar
developers using cosine similarity.

## Features

- **User authentication** — registration, login, JWT access tokens, password
  hashing (Argon2 via `pwdlib`).
- **Developer profiles** — bio, location, education, experience level, social
  links, availability, and collaboration preferences.
- **Normalized skill system** — a catalog of skills with categories
  (language / framework / tool / domain), linked to users with a proficiency
  rating and years of experience.
- **Projects** — users can list projects and tag them with skills.
- **Embedding pipeline** — deterministic, offline vector embeddings built from
  skills, technologies, domains, projects, and bio using the hashing trick.
- **Matching engine** — cosine similarity combined with configurable skill
  overlap and experience-compatibility signals to produce Top-K recommendations.
- **Resume parsing** — upload a PDF/DOCX/TXT resume to auto-extract name,
  contact info, skills, experience, education, and projects. Extracted skills
  default to level 3 and 1 year of experience, adjustable before saving.
- **Hackathon team formation** — create team projects with required skills,
  tech stack, team size, college, and same-college restriction. Get
  skill-matched developer recommendations per project, invite developers,
  and manage applications, members, and invitations. Team size and
  college rules are enforced by the backend.
- **Clean layered architecture** — API → service → repository → model, ready
  for a future LLM-powered feature.

## Tech Stack

| Layer     | Technology                                  |
| --------- | ------------------------------------------- |
| Framework | FastAPI                                     |
| Database  | PostgreSQL                                  |
| ORM       | SQLAlchemy 2.0                              |
| Migrations| Alembic                                     |
| Auth      | JWT (PyJWT) + Argon2 (pwdlib)               |
| Validation| Pydantic v2 + pydantic-settings             |
| Vectors   | NumPy (deterministic hashing-trick embedding)|
| Testing   | pytest + FastAPI TestClient                 |
| Packaging | Docker + Docker Compose                     |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / JSON
┌───────────────────────────▼─────────────────────────────────┐
│                     API layer (app/api)                     │
│   auth.py  users.py  profiles.py  recommendations.py        │
│   - request validation (Pydantic)  - auth dependency        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Service layer (app/services)              │
│   auth_service  profile_service  embedding_service          │
│   matching_service                                          │
│   - business logic  - embedding generation  - scoring       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                Repository layer (app/repositories)          │
│   user_repository  profile_repository  skill_repository     │
│   - database operations (SQLAlchemy)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  Model layer (app/db/models)               │
│   User  DeveloperProfile  Skill  UserSkill  Project  ...    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   PostgreSQL   │
                    └────────────────┘
```

Supporting layers:

- `app/core` — configuration (`config.py`), security (`security.py`),
  dependencies (`deps.py`), and centralized exception handling
  (`exceptions.py`).
- `app/schemas` — Pydantic request/response models.
- `app/utils` — shared model→schema mappers.

## Project Structure

```
DevMatch/
├── alembic/                  # Alembic migrations
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py               # FastAPI app, CORS, exception handlers, routes
│   ├── api/                  # API routers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── profiles.py
│   │   └── recommendations.py
│   ├── core/                 # config, security, deps, exceptions
│   ├── db/
│   │   ├── session.py        # engine, SessionLocal, get_db
│   │   └── models/           # SQLAlchemy models
│   ├── repositories/         # data-access layer
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # business logic
│   └── utils/                # mappers
├── tests/                    # pytest suite
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Database Design

```
users
├── id (PK)
├── username (unique)
├── email (unique)
├── password_hash
├── created_at / updated_at
│
├── 1:1 ── developer_profiles
│         ├── id (PK)
│         ├── user_id (FK, unique)
│         ├── full_name, bio, location, education
│         ├── experience_level (enum)
│         ├── github_url, linkedin_url, portfolio_url
│         ├── availability
│         ├── collaboration_preferences
│         ├── embedding (JSON)          ← profile vector
│         ├── embedding_updated_at
│         └── created_at / updated_at
│
├── 1:N ── user_skills ── N:1 ── skills
│         ├── user_id (FK)             ├── id (PK)
│         ├── skill_id (FK)            ├── name (unique)
│         ├── proficiency (1-5)        ├── category (enum)
│         ├── years_experience         └── created_at
│         └── unique(user_id, skill_id)
│
└── 1:N ── projects ── N:M ── skills  (via project_skills)
          ├── id (PK)                  ├── project_id (FK)
          ├── user_id (FK)             ├── skill_id (FK)
          ├── title, description, url   └── unique(project_id, skill_id)
          └── created_at
```

Key design decisions:

- **Normalized skills** — skills live in a catalog table and are linked to
  users and projects through association tables, avoiding uncontrolled
  comma-separated strings and enabling efficient overlap queries.
- **Embedding stored on the profile** — the vector is persisted as JSON and
  regenerated whenever relevant profile data changes, so it is not recomputed
  on every request.
- **Cascading deletes** — deleting a user removes their profile, skills, and
  projects.
- **Indexes** — foreign keys and lookup columns are indexed; unique constraints
  protect data integrity.

## Authentication Flow

1. `POST /api/v1/auth/register` — validates input, hashes the password
   (Argon2), and creates the user.
2. `POST /api/v1/auth/login` — verifies credentials and returns a JWT access
   token (`{ "access_token": "...", "token_type": "bearer" }`).
3. Protected routes require an `Authorization: Bearer <token>` header. The
   `get_current_user` dependency decodes the JWT, loads the user, and injects
   it into the request.

Tokens are signed with `JWT_SECRET_KEY` (HS256 by default) and expire after a
configurable number of minutes. Secrets are read from environment variables —
nothing is hardcoded.

## Embedding Approach

The embedding is **deterministic and offline** (no external model or API
needed). It uses the **hashing trick**:

1. Build a weighted token list from the profile:
   - **Skills** (languages/frameworks) — highest weight
   - **Tools / technologies** — medium weight
   - **Domains / interests** — medium weight
   - **Project titles + descriptions** — base weight
   - **Bio** — base weight
2. Tokenize each entry into lowercase alphanumeric words.
3. Hash each token (MD5) into a fixed-dimension vector (default 256),
   incrementing the corresponding dimension.
4. L2-normalize the result.

Because the vector is normalized, the dot product of two embeddings is their
cosine similarity. Weights are configurable via environment variables.

## Matching Algorithm

Given a user, the matching service:

1. Loads the user's stored profile embedding.
2. Loads all other profiles that have an embedding (eager-loaded to avoid N+1
   queries).
3. Computes a **weighted final score** for each candidate:

```
final_score =
    embedding_weight   × cosine_similarity(own, candidate)
  + skill_weight       × jaccard_similarity(own_skills, candidate_skills)
  + experience_weight  × experience_compatibility(own_level, candidate_level)
```

   - **Cosine similarity** — overall profile/embedding similarity.
   - **Jaccard similarity** — direct skill-set overlap (`|A∩B| / |A∪B|`).
   - **Experience compatibility** — 1.0 for the same level, 0.6 for adjacent,
     0.3 for two apart, 0.1 otherwise.

4. Ranks candidates by score and returns the **Top-K** (configurable limit).

The default weights are `0.7 / 0.2 / 0.1` and are configurable via environment
variables. Each recommendation includes the candidate's public profile, the
similarity score, and the list of overlapping skills — the structured signals a
future LLM feature could use to explain *why* two developers matched.

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Path                              | Auth | Description                          |
| ------ | --------------------------------- | ---- | ------------------------------------ |
| POST   | `/auth/register`                  | No   | Register a new user                  |
| POST   | `/auth/login`                     | No   | Log in, returns JWT                  |
| GET    | `/users/`                         | No   | List users (public info, paginated)  |
| GET    | `/users/me`                       | Yes  | Get current user                     |
| GET    | `/profiles/me`                    | Yes  | Get own full profile                 |
| PUT    | `/profiles/me`                    | Yes  | Update own profile                   |
| GET    | `/profiles/{user_id}`             | No   | Get a user's public profile          |
| POST   | `/profiles/me/skills`             | Yes  | Add a skill                          |
| DELETE | `/profiles/me/skills/{skill_id}`  | Yes  | Remove a skill                       |
| POST   | `/profiles/me/projects`           | Yes  | Add a project                        |
| DELETE | `/profiles/me/projects/{id}`      | Yes  | Remove a project                     |
| POST   | `/profiles/me/parse-resume`       | Yes  | Parse a resume file (multipart PDF/DOCX/TXT, 10MB max) |
| GET    | `/recommendations?limit=K`        | Yes  | Top-K developer recommendations      |
| POST   | `/team-projects`                  | Yes  | Create a team project                |
| GET    | `/team-projects`                  | No   | Discover teams (paginated, `college`/`q` filters) |
| GET    | `/team-projects/{id}`             | No*  | Team detail (*viewer flags when authenticated) |
| PUT/DELETE | `/team-projects/{id}`         | Yes  | Update/delete (creator only)         |
| POST/DELETE | `/team-projects/{id}/skills[/{skill_id}]` | Yes | Manage required skills (creator) |
| GET    | `/team-projects/{id}/recommendations` | Yes | Matched developers (creator only) |
| POST   | `/team-projects/{id}/apply`       | Yes  | Apply to join a team                 |
| GET    | `/team-projects/{id}/applications`| Yes  | List applications (creator only)     |
| POST   | `/team-projects/{id}/applications/{app_id}/accept|reject` | Yes | Accept/reject (creator) |
| POST   | `/team-projects/{id}/invite`      | Yes  | Invite a developer (creator only)    |
| GET    | `/team-projects/me/applications`  | Yes  | My outgoing applications             |
| GET    | `/team-projects/me/invitations`   | Yes  | My incoming invitations              |
| POST   | `/team-projects/invitations/{id}/accept|reject` | Yes | Respond to invitation   |
| DELETE | `/team-projects/{id}/members/{user_id}` | Yes | Remove member (creator) or leave (self) |

Other endpoints:

| Method | Path      | Description        |
| ------ | --------- | ------------------ |
| GET    | `/`       | API info           |
| GET    | `/health` | Health check       |
| GET    | `/docs`   | Swagger UI         |

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable                          | Default                              | Description                          |
| --------------------------------- | ------------------------------------ | ------------------------------------ |
| `DATABASE_URL`                    | `postgresql+psycopg://...`           | SQLAlchemy database URL              |
| `JWT_SECRET_KEY`                  | **(required)**                       | Secret used to sign JWTs             |
| `JWT_ALGORITHM`                   | `HS256`                              | JWT signing algorithm                |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                 | Access token lifetime                |
| `ENVIRONMENT`                     | `development`                         | `development` / `test` / `production`|
| `DEBUG`                           | `false`                              | Debug mode                           |
| `CORS_ORIGINS`                    | `["*"]`                              | Allowed CORS origins (JSON array)     |
| `EMBEDDING_DIMENSION`             | `256`                                | Embedding vector size                |
| `EMBEDDING_SKILL_WEIGHT`          | `3.0`                                | Weight for languages/frameworks      |
| `EMBEDDING_TECHNOLOGY_WEIGHT`     | `2.0`                                | Weight for tools/technologies        |
| `EMBEDDING_DOMAIN_WEIGHT`         | `2.0`                                | Weight for domains/interests         |
| `EMBEDDING_PROJECT_WEIGHT`        | `1.0`                                | Weight for projects                  |
| `EMBEDDING_BIO_WEIGHT`            | `1.0`                                | Weight for bio                       |
| `MATCHING_EMBEDDING_WEIGHT`       | `0.7`                                | Weight for cosine similarity         |
| `MATCHING_SKILL_WEIGHT`           | `0.2`                                | Weight for skill overlap             |
| `MATCHING_EXPERIENCE_WEIGHT`      | `0.1`                                | Weight for experience compatibility  |
| `MATCHING_DEFAULT_LIMIT`          | `10`                                 | Default Top-K                        |
| `MATCHING_MAX_LIMIT`              | `50`                                 | Maximum Top-K                        |

## Local Setup

**Prerequisites:** Python 3.11+ and PostgreSQL.

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd DevMatch

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
#    edit .env — set DATABASE_URL and JWT_SECRET_KEY

# 5. Run migrations
alembic upgrade head

# 6. Start the server
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000` (Swagger UI at `/docs`).

## Docker Setup

**Prerequisites:** Docker and Docker Compose.

```bash
# 1. Configure environment
cp .env.example .env
#    set JWT_SECRET_KEY (required) and adjust DATABASE_URL if needed

# 2. Build and start all services
docker compose up --build
```

This starts:

- **db** — PostgreSQL 17 (with a health check)
- **api** — the FastAPI app (runs `alembic upgrade head` on startup, then
  serves on port 8000)

The API is available at `http://localhost:8000` (Swagger UI at `/docs`).

To stop the containers:

```bash
docker compose down
```

## Database Migrations

Migrations are managed with [Alembic](https://alembic.sqlalchemy.org/).

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "description"

# Roll back the last migration
alembic downgrade -1
```

The initial migration creates the `users` table; subsequent migrations add
profile fields and introduce the `developer_profiles`, `skills`, `user_skills`,
`projects`, and `project_skills` tables.

## Running Tests

The test suite uses pytest with an in-memory SQLite database, so it is fast and
requires no external services.

```bash
# Run all tests
pytest

# Run with coverage (optional)
pytest --cov=app
```

Tests cover authentication, users, profiles, skills/projects, the embedding
pipeline, the matching engine, and database constraints/relationships.

## Example API Requests

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"password123"}'

# Log in
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}'

# Update profile (use the token from login)
curl -X PUT http://localhost:8000/api/v1/profiles/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Alice","experience_level":"senior","bio":"Python developer"}'

# Add a skill
curl -X POST http://localhost:8000/api/v1/profiles/me/skills \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Python","category":"language","proficiency":5}'

# Add a project
curl -X POST http://localhost:8000/api/v1/profiles/me/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"ML Pipeline","skill_names":["Python","Machine Learning"]}'

# Get recommendations
curl "http://localhost:8000/api/v1/recommendations?limit=5" \
  -H "Authorization: Bearer <token>"
```

## Future Improvements

- **LLM-powered features** — natural-language developer search, AI-generated
  profile summaries, and natural-language explanations for matches. The
  matching service already returns structured signals (score, skill overlap)
  that an LLM layer could consume.
- **pgvector** — move similarity search into PostgreSQL with the `pgvector`
  extension for large-scale, database-side vector search.
- **Embedding model** — replace the hashing-trick embedding with a learned
  sentence transformer for richer semantic similarity (the `EmbeddingService`
  interface is designed to be swapped without touching callers).
- **Caching** — cache embeddings and recommendation results.
- **Rate limiting & pagination** — on public endpoints.
- **Testing** — add integration tests against a real PostgreSQL instance and
  expand coverage.
