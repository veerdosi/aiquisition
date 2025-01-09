from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    github_url: Optional[str]
    website: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    acquisition_score: float

    class Config:
        orm_mode = True

class GithubMetrics(BaseModel):
    stars: int
    forks: int
    contributors: int
    commit_frequency: float
    issue_response_time: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class TrendsData(BaseModel):
    interest_over_time: List[float]
    related_queries: Dict[str, List[Dict[str, Any]]]

class MarketMetrics(BaseModel):
    tranco_rank: Optional[int]
    estimated_traffic: Optional[int]
    estimated_spend: float
    search_interest_score: float
    trend_score: float
    efficiency_score: float
    trends_data: TrendsData
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class TechStack(BaseModel):
    analytics_tools: List[str]
    advertising_tools: List[str]
    marketing_tools: List[str]
    tech_diversity_score: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True

class CompanyMetrics(BaseModel):
    github: Optional[GithubMetrics]
    market: Optional[MarketMetrics]
    tech_stack: Optional[TechStack]

class CompanyDetail(Company):
    metrics: CompanyMetrics

    class Config:
        orm_mode = True

class CompanyUpdate(BaseModel):
    name: Optional[str]
    github_url: Optional[str]
    website: Optional[str]

class MetricsResponse(BaseModel):
    success: bool
    message: str
    metrics: Optional[CompanyMetrics]
    updated_at: datetime

class TrancoRankResponse(BaseModel):
    rank: Optional[int]
    last_updated: datetime

class TrendsResponse(BaseModel):
    interest_data: TrendsData
    last_updated: datetime