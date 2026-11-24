# 001 · Container inacessível pelo host

API FastAPI executada com Docker Compose. O container estava em execução, mas a conexão com `localhost:8080` era encerrada antes de receber uma resposta HTTP.

O Uvicorn escutava em `127.0.0.1:8000`, no loopback do container. O tráfego encaminhado pelo Docker chegava pela interface de rede do container. No `Dockerfile`, a opção `--host` foi alterada para `0.0.0.0` para que o Uvicorn escutasse em todas as interfaces IPv4 do container.

## Reprodução e validação da correção

Na pasta do laboratório, reconstrua a imagem e consulte a API pelo host.

```bash
docker compose up -d --build
curl -i http://localhost:8080/
```

Após a correção, a API respondeu com `HTTP/1.1 200 OK` e `{"message":"Infrastructure Labs API"}`.
