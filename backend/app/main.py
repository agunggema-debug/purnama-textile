from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, core, distribution, finance, ppic, production, purchasing, warehouse

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistem ERP & SCM Internal Purnama Textile (On-Premise)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(core.router)
app.include_router(ppic.router)
app.include_router(purchasing.router)
app.include_router(warehouse.router)
app.include_router(production.router)
app.include_router(distribution.router)
app.include_router(finance.router)


@app.get("/", tags=["System"])
def root():
    return {"app": settings.APP_NAME, "status": "ok", "docs": "/docs"}


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "healthy", "app_env": settings.APP_ENV}
