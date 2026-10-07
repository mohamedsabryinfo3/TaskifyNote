from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes.health import router as health_router
app=FastAPI(title='TaskifyNote API',version='0.7.5')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_methods=['*'],allow_headers=['*'])
app.include_router(health_router,prefix='/api/v1')
@app.get('/')
async def root():
    return {'name':'TaskifyNote','status':'ok','version':'0.7.5'}
