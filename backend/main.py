from backend.api import civilian,civilian_travel
from backend.api import area_transparency
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.frontend import FrontendFiles
from project_paths import PROJECT_ROOT
from backend.db.repository import initialize
from backend.auth import router as auth
from backend.api import models,predictions,observations,cities,scenarios,feedback,civic,assessments,resources,references,maps,municipal,locality_planning,open_data,city_infra,notifications

@asynccontextmanager
async def lifespan(app):
    initialize()
    civilian.initialize()
    area_transparency.initialize()
    yield

app=FastAPI(title='CivicFlux research and civic resilience API',version='2.0.0',lifespan=lifespan)
from backend.jurisdiction import JurisdictionMiddleware
app.add_middleware(JurisdictionMiddleware)
for router in [auth,models.router,predictions.router,observations.router,cities.router,scenarios.router,feedback.router,civic.router,assessments.router,resources.router,references.router,maps.router,municipal.router,locality_planning.router,open_data.router,city_infra.router,notifications.router]:app.include_router(router)
@app.get('/api/health')
def health():return {'status':'ok','research_only':True,'automatic_dispatch':False}
app.include_router(area_transparency.router)
app.include_router(civilian.router)
app.include_router(civilian_travel.router)
dist=PROJECT_ROOT/'frontend/dist'
app.mount('/', FrontendFiles(dist), name='frontend')
