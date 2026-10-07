from fastapi import APIRouter
router=APIRouter(tags=['Health'])
@router.get('/health')
async def health():
    return {'status':'ok','service':'taskify-note-api','version':'0.7.5'}
