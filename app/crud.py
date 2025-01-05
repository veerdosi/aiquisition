from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from typing import List, Optional

def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_companies(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    min_score: float = 0.0
) -> List[models.Company]:
    return db.query(models.Company)\
        .filter(models.Company.acquisition_score >= min_score)\
        .offset(skip)\
        .limit(limit)\
        .all()

def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_github_metrics(db: Session, company_id: int, metrics: dict):
    db_metrics = db.query(models.GithubMetrics)\
        .filter(models.GithubMetrics.company_id == company_id)\
        .first()
    
    if db_metrics:
        for key, value in metrics.items():
            setattr(db_metrics, key, value)
    else:
        db_metrics = models.GithubMetrics(company_id=company_id, **metrics)
        db.add(db_metrics)
    
    db.commit()
    return db_metrics

def update_review_metrics(db: Session, company_id: int, metrics: dict):
    db_metrics = db.query(models.ReviewMetrics)\
        .filter(models.ReviewMetrics.company_id == company_id)\
        .first()
    
    if db_metrics:
        for key, value in metrics.items():
            setattr(db_metrics, key, value)
    else:
        db_metrics = models.ReviewMetrics(company_id=company_id, **metrics)
        db.add(db_metrics)
    
    db.commit()
    return db_metrics

def update_marketing_metrics(db: Session, company_id: int, metrics: dict):
    db_metrics = db.query(models.MarketingMetrics)\
        .filter(models.MarketingMetrics.company_id == company_id)\
        .first()
    
    if db_metrics:
        for key, value in metrics.items():
            setattr(db_metrics, key, value)
    else:
        db_metrics = models.MarketingMetrics(company_id=company_id, **metrics)
        db.add(db_metrics)
    
    db.commit()
    return db_metrics