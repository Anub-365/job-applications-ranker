from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import init_db
from backend.api.auth import router as auth_router
from backend.api.students import router as students_router
from backend.api.recruiters import router as recruiters_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown — cleanup if needed


app = FastAPI(
    title="Internship Connect Platform",
    description="AI-powered student-internship matching using semantic search, GitHub intelligence, and skill scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(students_router, prefix="/api/students", tags=["Students"])
app.include_router(recruiters_router, prefix="/api/recruiters", tags=["Recruiters"])


@app.get("/")
async def root():
    return {"message": "Internship Connect Platform API", "status": "running"}
