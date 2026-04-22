from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import string
import random
import validators
from datetime import datetime

from database import engine, get_db, Base
from models import URLMapping, Analytics

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "backend-url-shortener"}


@app.post("/shorten")
async def shorten_url(
    original_url: str,
    custom_code: str = None,
    title: str = None,
    db: Session = Depends(get_db),
):
    if not validators.url(original_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    if custom_code:
        existing = db.query(URLMapping).filter(URLMapping.short_code == custom_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Custom code already taken")
        short_code = custom_code
    else:
        short_code = generate_short_code()
        while db.query(URLMapping).filter(URLMapping.short_code == short_code).first():
            short_code = generate_short_code()

    url_mapping = URLMapping(
        short_code=short_code,
        original_url=original_url,
        custom_title=title,
    )
    db.add(url_mapping)
    db.commit()
    db.refresh(url_mapping)

    return {
        "short_code": short_code,
        "short_url": f"http://localhost:8000/{short_code}",
        "original_url": original_url,
        "title": title,
        "created_at": url_mapping.created_at,
    }


@app.get("/api/links")
async def get_all_links(db: Session = Depends(get_db)):
    links = db.query(URLMapping).order_by(desc(URLMapping.created_at)).all()
    return [
        {
            "short_code": link.short_code,
            "original_url": link.original_url,
            "short_url": f"http://localhost:8000/{link.short_code}",
            "title": link.custom_title,
            "clicks": link.click_count,
            "created_at": link.created_at,
            "last_clicked": link.last_clicked,
        }
        for link in links
    ]


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_links = db.query(URLMapping).count()
    total_clicks = (
        db.query(URLMapping).with_entities(func.sum(URLMapping.click_count)).scalar() or 0
    )
    return {"total_links": total_links, "total_clicks": total_clicks}


@app.delete("/api/links/{short_code}")
async def delete_link(short_code: str, db: Session = Depends(get_db)):
    url_mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
    if not url_mapping:
        raise HTTPException(status_code=404, detail="Short URL not found")
    db.delete(url_mapping)
    db.query(Analytics).filter(Analytics.short_code == short_code).delete()
    db.commit()
    return {"message": "Link deleted successfully"}


@app.get("/{short_code}")
async def redirect_to_original(short_code: str, request: Request, db: Session = Depends(get_db)):
    url_mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
    if not url_mapping:
        raise HTTPException(status_code=404, detail="Short URL not found")

    url_mapping.click_count += 1
    url_mapping.last_clicked = datetime.utcnow()

    analytics = Analytics(
        short_code=short_code,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
        ip_address=get_client_ip(request),
    )
    db.add(analytics)
    db.commit()

    return RedirectResponse(url=url_mapping.original_url)
