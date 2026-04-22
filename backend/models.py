from sqlalchemy import Column, String, Integer, DateTime
from database import Base
from datetime import datetime


class URLMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True)
    original_url = Column(String(2048), index=True)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_clicked = Column(DateTime, nullable=True)
    custom_title = Column(String(255), nullable=True)


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), index=True)
    user_agent = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)
