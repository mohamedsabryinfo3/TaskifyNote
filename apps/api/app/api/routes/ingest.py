from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AnyUrl, BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from bs4 import BeautifulSoup
from ...core.db import get_db
from ...models import Note

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

class URLRequest(BaseModel):
    url: AnyUrl
    save_as_note: bool = True

@router.post("/url", status_code=201)
async def ingest_url(payload: URLRequest, db: AsyncSession = Depends(get_db)):
    url = str(payload.url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers={"User-Agent":"TaskifyNote/0.7"}) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(400, f"Could not read URL: {exc}")
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    for tag in soup(["script","style","noscript","nav","footer","header"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    if payload.save_as_note:
        note = Note(title=title[:500], content=text[:200000], source_url=url)
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return {"status":"saved","note_id":str(note.id),"title":title,"url":url}
    return {"status":"extracted","title":title,"url":url,"content":text[:200000]}
