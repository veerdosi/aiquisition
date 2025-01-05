from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    github_url: str
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

class ReviewMetrics(BaseModel):
    nps_score: float
    review_count: int
    average_rating: float
    sentiment_score: float
    raw_data: Dict[str, Any]
    updated_at: datetime

    class Config:
        orm_mode = True