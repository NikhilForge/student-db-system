# Student DB System

Lightweight Flask app for managing students and courses. This repository includes Docker configuration and instructions for local and cloud deployment.

## Run locally (without Docker)

- Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Configure the database credentials in `config.py` or set environment variables used by your environment.
- Start a MySQL server and create the `student_db` database and required tables.
- Run the app:

```bash
python app.py
```

The app will start on port `5000` in debug mode when run directly.

## Run with Docker (recommended for deployment)

- Build and run with Docker Compose (includes MySQL):

```bash
docker compose up --build
```

The web app will be available at `http://localhost:8000` and MySQL on `localhost:3306`.

## Deploy to a cloud service (Render / Heroku / any container service)

- Build a Docker image and push to your registry, or deploy using the `Dockerfile` and `Procfile` provided.
- Example (build locally and run):

```bash
docker build -t student-db-system:latest .
docker run -e MYSQL_HOST=<your-db-host> -e MYSQL_USER=<user> -e MYSQL_PASSWORD=<pw> -e MYSQL_DB=<db> -p 8000:8000 student-db-system:latest
```

For managed services, provide environment variables for the database and a secure `SECRET_KEY` for the Flask session.

## Notes
- Update `app.secret_key` in `app.py` and avoid committing secrets to the repo.
- Ensure the MySQL schema (tables: `admin`, `students`, `courses`, `student_courses`, `marks`) exists before using the app.

## Deploy to Render (recommended)

1. Create a Render account and connect your GitHub repository.
2. Create a new Web Service and choose "Deploy from a Dockerfile".
3. Point Render to the `main` branch and use the `Dockerfile` in the repo. You can also import the `render.yaml` manifest included in this repository.
4. Set environment variables in the Render dashboard:
	- `MYSQL_HOST` — host for your production MySQL instance (use a managed DB service)
	- `MYSQL_USER`
	- `MYSQL_PASSWORD`
	- `MYSQL_DB`
	- `SECRET_KEY` — a long random string for Flask sessions
5. (Optional) If you want the CI to build and push Docker images to Docker Hub, add the following GitHub repository secrets:
	- `DOCKERHUB_USERNAME`
	- `DOCKERHUB_TOKEN`
	- `RENDER_API_KEY` and `RENDER_SERVICE_ID` (if you want the workflow to trigger a deploy)

Security reminders:
- Do not expose MySQL to the public internet. Use a managed DB or VPC/private connection for production.
- Use HTTPS (Render provides TLS automatically).

### Production compose and healthcheck

- A production-ready compose file `docker-compose.prod.yml` is included. It does not expose MySQL on the host.
- The app exposes a `/health` endpoint and the `Dockerfile` contains a `HEALTHCHECK` that queries it.


