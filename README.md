# Mentoreed

<!-- Still missing some definitions about static files and video provider (prob going to use cloudflare stream)
![architecture](https://github.com/user-attachments/assets/b6b77611-0a2e-46e6-851b-2b3804fe2d02) -->

<!-- App might look something like this
![mentoreed-eng](https://github.com/user-attachments/assets/462ed6d1-8169-427c-a82e-0147cda83551) -->

## How to run
- Clone the repository
- Make sure you have [docker compose](https://docs.docker.com/compose/) and [make](https://www.gnu.org/software/make/#download) installed
- Inside the root folder:

```bash
docker compose -f local.yml build
docker compose -f local.yml up
```

## Application Stack

### Backend
- **Django & Django REST Framework**: Web framework and API layer.
- **PostgreSQL**: Relational database for persistent data storage.
- **Redis**: In-memory data store for caching and task brokering.
- **Celery & Flower**: Distributed task queue and real-time task monitoring.

### DevOps & Infrastructure
- **Docker**: Containerization for development and deployment.
- **Nginx**: Reverse proxy and static file server.
- **Portainer**: Container management.
- **DigitalOcean**: Cloud hosting and infrastructure provider.

### Roadmap
- **Observability**: Integrated metrics and logging for better visibility.
- **Stack Tracing**: Improved error monitoring and debugging.
- **CI/CD**: Automated testing, deployments, and migration health checks.

### Current architecture

```mermaid
flowchart TD
  users["End Users (Web/API Clients)"]

  subgraph DO["DigitalOcean (Cloud)"]
    direction TB
    nginx["Nginx (Reverse Proxy)"]
    portainer["Portainer (Docker Admin UI)"]
    flower["Flower (Task Monitoring)"]
    celery["Celery Worker (Task Queue)"]
    django["Django + DRF (Web API/App)"]
    postgres["PostgreSQL (Database)"]
    redis["Redis (Cache & Broker)"]
    elastic["Elasticsearch (Search/Logs)"]
  end

  %% User traffic
  users --> nginx
  nginx --> django

  %% Nginx HTTPS exposes for admin/monitoring
  nginx -. "HTTPS" .-> flower
  nginx -. "HTTPS" .-> portainer

  %% Internal service flows
  django --> postgres
  django --> redis
  django --> elastic
  redis --> celery
  celery --> postgres
  flower --> celery

  %% Orchestration (dashed line)
  Docker-compose -.-> DO
```
