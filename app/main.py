from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from celery import Celery
from . import models, schemas, crud
from .database import SessionLocal, engine
from .collectors import GitHubCollector, ReviewCollector, MarketingEstimator
from .config import Settings
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acquisition Target Discovery API")

# Initialize Celery
celery = Celery('tasks', broker='redis://redis:6379/0')

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize collectors
settings = Settings()
github_collector = GitHubCollector(settings.github_token)
review_collector = ReviewCollector()
marketing_estimator = MarketingEstimator()

@app.post("/companies/", response_model=schemas.Company)
async def create_company(
    company: schemas.CompanyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_company = crud.create_company(db=db, company=company)
    background_tasks.add_task(process_company_data, db_company.id)
    return db_company

@app.get("/companies/", response_model=list[schemas.Company])
def get_companies(
    skip: int = 0,
    limit: int = 100,
    min_score: float = 0.0,
    db: Session = Depends(get_db)
):
    companies = crud.get_companies(db, skip=skip, limit=limit, min_score=min_score)
    return companies

@app.get("/companies/{company_id}", response_model=schemas.CompanyDetail)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = crud.get_company(db, company_id=company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company