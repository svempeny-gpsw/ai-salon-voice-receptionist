from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.bookings import router as bookings_router
from app.core.database import Base, engine
from app.models import booking_db  # noqa: F401  (register tables)

app = FastAPI(title="Salon Booking Policy API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield


app.router.lifespan_context = lifespan


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(bookings_router)
