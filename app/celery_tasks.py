from celery import shared_task
from .database import SessionLocal
from . import crud
from .collectors import GitHubCollector, ReviewCollector, MarketingEstimator
from .config import Settings
import logging

logger = logging.getLogger(__name__)
settings = Settings()

@shared_task
def process_company_data(company_id: int):
    try:
        db = SessionLocal()
        company = crud.get_company(db, company_id)
        
        if not company:
            logger.error(f"Company {company_id} not found")
            return
        
        # Initialize collectors
        github_collector = GitHubCollector(settings.github_token)
        review_collector = ReviewCollector()
        marketing_estimator = MarketingEstimator()
        
        # Collect metrics
        github_metrics = github_collector.collect_metrics(company.github_url)
        if github_metrics:
            crud.update_github_metrics(db, company_id, github_metrics)
        
        review_metrics = review_collector.collect_metrics(company.name)
        if review_metrics:
            crud.update_review_metrics(db, company_id, review_metrics)
        
        marketing_metrics = marketing_estimator.collect_metrics(company.website)
        if marketing_metrics:
            crud.update_marketing_metrics(db, company_id, marketing_metrics)
        
        # Calculate acquisition score
        acquisition_score = calculate_acquisition_score(
            github_metrics,
            review_metrics,
            marketing_metrics
        )
        
        # Update company score
        company.acquisition_score = acquisition_score
        db.commit()
        
    except Exception as e:
        logger.error(f"Error processing company {company_id}: {str(e)}")
        raise
    
    finally:
        db.close()

def calculate_acquisition_score(
    github_metrics: dict,
    review_metrics: dict,
    marketing_metrics: dict
) -> float:
    try:
        # Define weights for each category
        weights = {
            'github': 0.4,
            'reviews': 0.3,
            'marketing': 0.3
        }
        
        # Calculate GitHub score
        github_score = 0
        if github_metrics:
            github_score = (
                github_metrics['stars'] * 0.3 +
                github_metrics['contributors'] * 0.3 +
                github_metrics['commit_frequency'] * 0.2 +
                (1 / (github_metrics['issue_response_time'] + 1)) * 0.2
            ) / 1000  # Normalize
        
        # Calculate review score
        review_score = 0
        if review_metrics:
            review_score = (
                review_metrics['nps_score'] * 0.4 +
                review_metrics['average_rating'] * 0.3 +
                review_metrics['sentiment_score'] * 0.3
            ) / 10  # Normalize
        
        # Calculate marketing efficiency score
        marketing_score = 0
        if marketing_metrics:
            marketing_score = (
                review_score / 
                (marketing_metrics['estimated_spend'] / 10000 + 1)
            )
        
        # Calculate final score
        final_score = (
            github_score * weights['github'] +
            review_score * weights['reviews'] +
            marketing_score * weights['marketing']
        )
        
        return min(max(final_score, 0), 100)  # Ensure score is between 0 and 100
        
    except Exception as e:
        logger.error(f"Error calculating acquisition score: {str(e)}")
        return 0.0