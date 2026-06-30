from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.corpora import router as corpora_router
from app.routes.query import router as rag_router
from app.routes.sessions import router as sessions_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Domain Knowledge Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Validation error", "code": "VALIDATION_ERROR", "errors": exc.errors()})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc), "code": "INTERNAL_ERROR"})


app.include_router(auth_router)
app.include_router(corpora_router)
app.include_router(rag_router)
app.include_router(sessions_router)
