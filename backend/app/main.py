from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.hybrid_matching import router as hybrid_matching_router
from app.api.job_ranking import router as job_ranking_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router
from app.api.profile import router as profile_router
from app.api.resume import router as resume_router
from app.api.semantic_matching import router as semantic_matching_router
from app.api.users import router as users_router

app = FastAPI(title="CareerLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(matching_router)
app.include_router(semantic_matching_router)
app.include_router(hybrid_matching_router)
app.include_router(job_ranking_router)