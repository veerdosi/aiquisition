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
    market_metrics = relationship("MarketMetrics", back_populates="company", uselist=False)
    tech_stack = relationship("TechStack", back_populates="company", uselist=False)

class GithubMetrics(Base):
    __tablename__ = "github_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    contributors = Column(Integer, default=0)
    commit_frequency = Column(Float, default=0.0)
    issue_response_time = Column(Float, default=0.0)
    raw_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="github_metrics")

class MarketMetrics(Base):
    __tablename__ = "market_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    tranco_rank = Column(Integer)
    estimated_traffic = Column(Integer)
    estimated_spend = Column(Float, default=0.0)
    search_interest_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    efficiency_score = Column(Float, default=0.0)
    trends_data = Column(JSON)  # Stores Google Trends data
    raw_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="market_metrics")

class TechStack(Base):
    __tablename__ = "tech_stack"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    analytics_tools = Column(JSON)  # List of analytics tools detected
    advertising_tools = Column(JSON)  # List of advertising tools detected
    marketing_tools = Column(JSON)  # List of marketing tools detected
    tech_diversity_score = Column(Float, default=0.0)
    raw_data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="tech_stack")

# Pydantic models for API
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class GithubMetricsModel(BaseModel):
    stars: int
    forks: int
    contributors: int
    commit_frequency: float
    issue_response_time: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class MarketMetricsModel(BaseModel):
    tranco_rank: Optional[int]
    estimated_traffic: Optional[int]
    estimated_spend: float
    search_interest_score: float
    trend_score: float
    efficiency_score: float
    trends_data: Dict[str, Any]
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class TechStackModel(BaseModel):
    analytics_tools: List[str]
    advertising_tools: List[str]
    marketing_tools: List[str]
    tech_diversity_score: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class CompanyDetail(BaseModel):
    id: int
    name: str
    github_url: Optional[str]
    website: str
    created_at: datetime
    updated_at: datetime
    acquisition_score: float
    github_metrics: Optional[GithubMetricsModel]
    market_metrics: Optional[MarketMetricsModel]
    tech_stack: Optional[TechStackModel]

    class Config:
        orm_mode = True