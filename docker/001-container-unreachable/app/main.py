from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Infrastructure Labs API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
