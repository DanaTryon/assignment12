
# Assignment12

A FastAPI application with CI/CD, Docker support, and automated testing.

## 🚀 Features
- FastAPI backend with Swagger/OpenAPI docs
- PostgreSQL integration
- CI/CD pipeline via GitHub Actions
- Dockerized deployment
- Security scanning with Trivy
- High test coverage (~97%)

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/danatryon/assignment12.git
cd assignment12
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🧪 Running Tests Locally

Unit, integration, and end‑to‑end tests are included.

```bash
pytest --cov=app
```

- Coverage reports are generated in the terminal.
- To view HTML coverage:
  ```bash
  pytest --cov=app --cov-report=html
  open htmlcov/index.html
  ```

---

## 🐳 Docker

### Build the image
```bash
docker build -t assignment12:latest .
```

### Run with Docker Compose
```bash
docker compose up -d
```

Swagger docs will be available at:
```
http://localhost:8000/docs
```

---

## 🔒 Security

This project uses **Trivy** in CI/CD to scan dependencies and Docker images for vulnerabilities.  
You can run it locally via Docker:

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image assignment12:latest
```

---

## 📂 Docker Hub Repository

Images are published automatically via GitHub Actions:

👉 [Docker Hub: danatryon/assignment12](https://hub.docker.com/r/danatryon/assignment12)

---

## 📖 API Documentation

Once running, interactive API docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🛠️ Development Notes
- CI/CD pipeline runs tests, security scans, and pushes images to Docker Hub.
- PostgreSQL is provided via Docker Compose for local testing.
- Coverage exclusions are documented with `# pragma: no cover`.



