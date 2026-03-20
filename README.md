# Nomadbase

Nomadbase is a private travel planning and discovery app for building trips, saving places, and tracking shared costs in one self-hosted workspace.

## Features
- Search and browse imported places on a map
- Save places globally or per trip
- Create trips with cities and participants
- Track shared expenses, visits, and settlement suggestions
- Run as a simple Docker stack with app + PostGIS database

## Tech Stack
- FastAPI
- PostgreSQL + PostGIS
- SQLAlchemy + Alembic
- Vue 3 + Vite + Pinia
- Leaflet
- Docker / Docker Compose

## Setup
### Docker
```bash
git clone https://github.com/TheDachlatte007/Nomadbase.git
cd Nomadbase
docker compose up -d --build
```

Open `http://localhost:5000`

### Notes
- The current alpha stack uses a local Postgres setup intended for simple self-hosted deployment.
- The backend runs Alembic migrations automatically on container start.

## Status
- Work in progress
- Early public version

---
## Support

If you find this project useful and want to support development:

☕ Ko-fi: https://ko-fi.com/thedachlatte007

Your support helps with development, testing, and maintenance.

---
## Legal / Disclaimer

This project is provided "as is", without warranty of any kind.

Nomadbase may integrate with or display third-party data, images, or metadata. All respective trademarks, images, and content remain the property of their respective owners.

Users are responsible for ensuring their usage complies with applicable laws and the terms of any third-party services they connect to.
