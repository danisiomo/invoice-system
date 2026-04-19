from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.auth import router as auth_router
from app.api.data_load import router as data_load_router
from app.api.references import router as references_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(data_load_router, prefix=settings.API_V1_PREFIX)
app.include_router(references_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "Invoice System MVP", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}