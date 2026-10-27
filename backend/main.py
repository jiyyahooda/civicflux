from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from project_paths import PROJECT_ROOT
from backend.db.repository import initialize
from backend.auth import router as auth
from backend.api import models,predictions,observations,cities,scenarios,feedback,civic,assessments,resources,references,maps

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app=FastAPI(title='CivicFlux research and civic resilience API',version='2.0.0',lifespan=lifespan)
for router in [auth,models.router,predictions.router,observations.router,cities.router,scenarios.router,feedback.router,civic.router,assessments.router,resources.router,references.router,maps.router]:app.include_router(router)
@app.get('/api/health')
def health():return {'status':'ok','research_only':True,'automatic_dispatch':False}
dist=PROJECT_ROOT/'frontend/dist'
if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
