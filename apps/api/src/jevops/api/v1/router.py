from fastapi import APIRouter

from jevops.api.v1.analytics import router as analytics_router
from jevops.api.v1.decisions import router as decisions_router
from jevops.api.v1.demo import router as demo_router
from jevops.api.v1.health import router as health_router
from jevops.api.v1.policies import router as policies_router
from jevops.api.v1.replays import router as replays_router
from jevops.api.v1.reviews import router as reviews_router

v1_router = APIRouter()
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(decisions_router)
v1_router.include_router(policies_router)
v1_router.include_router(reviews_router)
v1_router.include_router(analytics_router)
v1_router.include_router(replays_router)
v1_router.include_router(demo_router)
