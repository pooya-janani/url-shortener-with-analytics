from fastapi import FastAPI

from app.database import Base, engine
from app import models


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener Analytics API",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}