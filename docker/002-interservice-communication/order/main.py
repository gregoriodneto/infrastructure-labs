import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("uvicorn.error")


class InventoryItem(BaseModel):
    product_id: int
    quantity: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = float(os.environ["INVENTORY_TIMEOUT_SECONDS"])
    url = os.environ["INVENTORY_URL"]
    async with httpx.AsyncClient(base_url=url, timeout=timeout, trust_env=False) as client:
        app.state.inventory = client
        app.state.inventory_timeout = timeout
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/orders/1")
async def order(request: Request):
    client = request.app.state.inventory
    target = "/inventory/1"
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
        raise HTTPException(status_code=503, detail="Inventory unavailable") from error

    return {
        "order_id": 1,
        "product_id": item.product_id,
        "available": item.quantity > 0,
        "stock_quantity": item.quantity,
    }
