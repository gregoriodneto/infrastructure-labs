# Infrastructure Labs — 002

## Docker Interservice Communication Troubleshooting

### Overview

This lab simulates a network connectivity incident in a containerized microservices architecture.

Although all containers were running and the application health endpoint returned HTTP 200, the business endpoint returned HTTP 503 due to communication failures between its dependencies.

### Technology Stack

- Docker
- Docker Compose
- Python / FastAPI
- Node.js / Fastify
- PostgreSQL
- Linux networking tools

### Incident

The following symptoms were identified:

- All containers were running.
- PostgreSQL reported a healthy status.
- The Order Service health endpoint returned HTTP 200.
- The order endpoint returned HTTP 503.
- Application logs reported upstream connection timeouts.

### Root Cause Analysis

Two independent network configuration issues were identified:

1. Order Service and Inventory Service did not share a Docker network.
2. Inventory Service and PostgreSQL did not share a Docker network.

The initial network configuration prevented the expected service discovery and connectivity between application dependencies.

### Solution

The Docker Compose network topology was reorganized to establish communication between dependent services while preserving network segmentation.

| Service | frontend | services | data |
|---|---|---|---|
| Order | Yes | Yes | No |
| Inventory | No | Yes | Yes |
| PostgreSQL | No | No | Yes |

The final architecture uses three user-defined bridge networks.

Only the Order Service publishes a port to the host. Inventory and PostgreSQL communicate through internal Docker network connections without published host ports.

### Architecture

```text
Client
  |
  | localhost:8080
  v
Order Service
  |
  | services network / HTTP:3000
  v
Inventory Service
  |
  | data network / TCP:5432
  v
PostgreSQL
```

### Running the Lab

Create the local environment configuration:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Build and start the environment:

```bash
docker compose up -d --build
```

Check the running services:

```bash
docker compose ps
```

### Troubleshooting Commands

Inspect application logs:

```bash
docker compose logs order
docker compose logs inventory
docker compose logs postgres
```

Inspect Docker networks:

```bash
docker network ls
docker network inspect 002-interservice-communication_services
docker network inspect 002-interservice-communication_data
```

Validate service discovery:

```bash
docker compose exec order getent hosts inventory
docker compose exec inventory getent hosts postgres
docker compose exec order getent hosts postgres
```

Validate internal HTTP communication:

```bash
docker compose exec order curl -i http://inventory:3000/inventory/1
```

### Results

Before the network configuration was corrected:

```http
HTTP/1.1 503 Service Unavailable
```

```json
{"detail":"Inventory unavailable"}
```

After the network configuration was corrected:

```http
HTTP/1.1 200 OK
```

```json
{
  "order_id": 1,
  "product_id": 1,
  "available": true,
  "stock_quantity": 12
}
```

Network inspection confirmed that services were connected to the expected networks. DNS resolution between Order and PostgreSQL was unavailable, as expected from the configured network segmentation.

### Additional Improvements

- Environment-based configuration.
- Removal of unnecessary published ports.
- Dynamic API endpoints.
- Input validation improvements.
- Separation of application and infrastructure responsibilities.

### Key Learnings

- Running containers do not guarantee application availability.
- Docker service discovery depends on network configuration.
- Containers can participate in multiple bridge networks.
- Internal container communication does not require published host ports.
- Application logs help identify failures across service dependencies.
- Network segmentation reduces unnecessary direct connectivity.

### Conclusion

The incident was resolved by correcting the Docker network topology. Application improvements were implemented separately from the infrastructure fix.

This lab is part of the Infrastructure Labs project, focused on practical infrastructure engineering, DevOps and troubleshooting.