from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.scraper import scrape_profiles
import asyncio
import playwright.__main__ as pw_main
asyncio.get_event_loop().run_until_complete(pw_main.main(["install"]))

app = FastAPI()

class ScrapeRequest(BaseModel):
    li_at: str
    search_link: str
    max_results: int = 5

@app.post("/json/")
async def scrape_json(req: ScrapeRequest):
    try:
        data = await scrape_profiles(req.li_at, req.search_link, req.max_results)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
