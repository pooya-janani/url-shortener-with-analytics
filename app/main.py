from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routers import api_keys, users


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener Analytics API",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(api_keys.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}