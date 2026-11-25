# 002 · Comunicação entre microsserviços

## Cenário

O Order Service responde à checagem de saúde, mas retorna HTTP 503 ao consultar o pedido 1. Os três containers permanecem em execução durante o incidente.

## Arquitetura esperada

O Order Service (FastAPI) consulta o Inventory Service (Fastify) por HTTP. O Inventory Service consulta o estoque no PostgreSQL, inicializado com dados fictícios. Apenas o Order Service é publicado no host, em `127.0.0.1:8080`.

## Endpoints

| Serviço | Endpoint | Resposta esperada em operação normal |
| --- | --- | --- |
| Order | `GET /health` | HTTP 200 com o status do processo |
| Order | `GET /orders/1` | HTTP 200 com o pedido e a disponibilidade do produto |
| Inventory | `GET /health` | HTTP 200 com o status do processo |
| Inventory | `GET /inventory/1` | HTTP 200 com o estoque do produto consultado no PostgreSQL |

## Como iniciar

Na raiz do repositório, execute:

```bash
cd docker/002-interservice-communication
docker compose up --build -d
```
