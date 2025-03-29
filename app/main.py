import subprocess
subprocess.run(["playwright", "install", "chromium"], check=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.scraper import scrape_profiles

app = FastAPI()

# CORS pour Swagger
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
