import asyncio
import logging
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("uvicorn.error")


class InventoryItem(BaseModel):
    product_id: int
    quantity: int

# Criar o .env com variáveis de
@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = float(os.environ["INVENTORY_TIMEOUT_SECONDS"])
    url = os.environ["INVENTORY_URL"]
    async with httpx.AsyncClient(base_url=url, timeout=timeout, trust_env=False) as client:
        app.state.inventory = client
        app.state.inventory_timeout = timeout
        app.state.hostname = socket.gethostname()
        app.state.started_at = datetime.now(timezone.utc)
        yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def identify_instance(request: Request, call_next):
    hostname = request.app.state.hostname
    started = perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Instance-ID"] = hostname
        return response
    finally:
        logger.info(
            "Request hostname=%s method=%s path=%s duration_ms=%.2f",
            hostname,
            request.method,
            request.url.path,
            (perf_counter() - started) * 1000,
        )


@app.exception_handler(500)
async def internal_server_error(request: Request, _error: Exception):
    return PlainTextResponse(
        "Internal Server Error",
        status_code=500,
        headers={"X-Instance-ID": request.app.state.hostname},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/instance")
async def instance(request: Request):
    return {
        "hostname": request.app.state.hostname,
        "pid": os.getpid(),
        "started_at": request.app.state.started_at,
    }


@app.get("/work")
async def work(delay_ms: Annotated[int, Query(ge=0, le=5000)] = 100):
    await asyncio.sleep(delay_ms / 1000)
    return {"delay_ms": delay_ms}


@app.get("/orders/{order_id}")
async def order(
    order_id: Annotated[str, Path(pattern=r"^0*[1-9][0-9]*$")],
    request: Request,
):
    client = request.app.state.inventory
    target = f"/inventory/{order_id}"

    try:
        async with asyncio.timeout(request.app.state.inventory_timeout):
            response = await client.get(target)
        response.raise_for_status()
        item = InventoryItem.model_validate_json(response.content)
    except (httpx.HTTPError, TimeoutError, ValidationError) as error:
        status = error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        logger.warning(
            "Inventory request failed target=%s error=%s upstream_status=%s",
            client.base_url.join(target),
            type(error).__name__,
            status,
        )
        if status == 404:
            raise HTTPException(status_code=404, detail="Product not found") from error
        raise HTTPException(status_code=503, detail="Inventory unavailable") from error

    return {
        "order_id": int(order_id.lstrip("0")),
        "product_id": item.product_id,
        "available": item.quantity > 0,
        "stock_quantity": item.quantity,
    }