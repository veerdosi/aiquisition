from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    github_token: str
    database_url: str
    redis_url: str
    semrush_api_key: Optional[str]
    similarweb_api_key: Optional[str]
    
    class Config:
        env_file = ".env" = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="github_metrics")

class ReviewMetrics(Base):
    __tablename__ = "review_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    nps_score = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    raw_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="review_metrics")

class MarketingMetrics(Base):
    __tablename__ = "marketing_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    estimated_spend = Column(Float, default=0.0)
    channels = Column(JSON)
    efficiency_score = Column(Float, default=0.0)
    raw_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="marketing_metrics")