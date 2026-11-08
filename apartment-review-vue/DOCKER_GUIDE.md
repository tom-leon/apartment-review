# Docker Setup Guide

Run everything from the **client (frontend) folder** with a single command!

## Project Structure

```
apartment-review/
├── apartment-review-fastapi/      # Backend (FastAPI)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── pyproject.toml
│   └── uv.lock
├── apartment-review-vue/          # Frontend (Vue 3)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── docker-compose.yml         # ← Run from here!
│   ├── package.json
│   └── src/
```

## Quick Start

### 1. Navigate to the frontend folder

```bash
cd apartment-review-vue
```

### 2. Start all services

```bash
docker-compose up
```

This will:

- ✅ Start PostgreSQL database
- ✅ Build and start FastAPI backend
- ✅ Build and start Vue 3 frontend

### 3. Access the application

| Service     | URL                        |
| ----------- | -------------------------- |
| Frontend    | http://localhost:5173      |
| Backend API | http://localhost:8000      |
| API Docs    | http://localhost:8000/docs |
| Database    | localhost:5432             |

## Useful Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Stop all services
docker-compose down

# Stop and remove database
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec db psql -U tom -d apartment_review
```

## Services

### PostgreSQL (`db`)

- Port: 5432
- User: tom
- Password: 123
- Database: apartment_review

### Backend API (`backend`)

- Port: 8000
- Framework: FastAPI
- Hot reload: ✅ Enabled
- Depends on: PostgreSQL

### Frontend (`frontend`)

- Port: 5173
- Framework: Vue 3
- Hot reload: ✅ Enabled
- Depends on: Backend

## Development Workflow

Both services support hot reload:

- **Backend**: Changes to Python files auto-reload
- **Frontend**: Changes to Vue files auto-reload

Just edit your code and the changes will appear instantly!

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Error

```bash
# Check if database is healthy
docker-compose ps

# View database logs
docker-compose logs db
```

### Rebuild Everything

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Without Docker (Local Development)

### Backend

```bash
cd ../apartment-review-fastapi
source env/bin/activate
uvicorn main:app --reload
```

### Frontend

```bash
cd apartment-review-vue
npm run dev
```

## Next Steps

1. Run `docker-compose up` from the frontend folder
2. Open http://localhost:5173
3. Test the API at http://localhost:8000/docs
4. Start building your Vue 3 frontend!
