from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, eligibility, parse, profile, recommend, research, saved, schemes
from db.session import Base, engine, SessionLocal
from services.import_schemes import import_demo

app = FastAPI(title="CivicGuide API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schemes.router)
app.include_router(eligibility.router)
app.include_router(parse.router)
app.include_router(profile.router)
app.include_router(recommend.router)
app.include_router(saved.router)
app.include_router(admin.router)
app.include_router(research.router)


@app.get("/api/health")
def health():
    return {"ok": True, "product": "CivicGuide"}


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from db.models import Scheme

        if db.query(Scheme).count() == 0:
            import_demo(db)
    finally:
        db.close()
