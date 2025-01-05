from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    github_url = Column(String)
    website = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    acquisition_score = Column(Float, default=0.0)
    
    github_metrics = relationship("GithubMetrics", back_populates="company", uselist=False)
    review_metrics = relationship("ReviewMetrics", back_populates="company", uselist=False)
    marketing_metrics = relationship("MarketingMetrics", back_populates="company", uselist=False)

class GithubMetrics(Base):
    __tablename__ = "github_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    contributors = Column(Integer, default=0)
    commit_frequency = Column(Float, default=0.0)
    issue_response_time = Column(Float, default=0.0)
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class MarketingMetrics(BaseModel):
    estimated_spend: float
    channels: Dict[str, Any]
    efficiency_score: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class CompanyDetail(Company):
    github_metrics: Optional[GithubMetrics]
    review_metrics: Optional[ReviewMetrics]
    marketing_metrics: Optional[MarketingMetrics]

    class Config:
        orm_mode = True