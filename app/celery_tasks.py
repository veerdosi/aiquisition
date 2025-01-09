from celery import shared_task
from .database import SessionLocal
from . import crud
from .collectors import GitHubCollector
from .marketing import MarketingEstimator
from .config import Settings
import logging
import asyncio

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
        marketing_estimator = MarketingEstimator()
        
        # Collect GitHub metrics
        github_metrics = github_collector.collect_metrics(company.github_url)
        if github_metrics:
            crud.update_github_metrics(db, company_id, github_metrics)
        
        # Collect marketing metrics using asyncio
        loop = asyncio.get_event_loop()
        marketing_metrics = loop.run_until_complete(
            marketing_estimator.collect_metrics(company.website)
        )
        if marketing_metrics:
            crud.update_market_metrics(db, company_id, marketing_metrics)
            
            # Extract and save tech stack data
            if tech_data := marketing_metrics.get('raw_data', {}).get('tech_stack'):
                crud.update_tech_stack(db, company_id, tech_data)
        
        # Calculate acquisition score
        acquisition_score = calculate_acquisition_score(
            github_metrics,
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
    marketing_metrics: dict
) -> float:
    try:
        # Define weights for each category
        weights = {
            'github': 0.4,
            'market': 0.3,
            'tech': 0.3
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
        
        # Calculate market score
        market_score = 0
        if marketing_metrics:
            # Get Tranco rank score (inverse of rank percentile)
            rank = marketing_metrics.get('raw_data', {}).get('tranco', {}).get('rank')
            rank_score = max(0, 100 - (rank / 1000000 * 100)) if rank else 0
            
            # Get trends score
            trends_data = marketing_metrics.get('raw_data', {}).get('trends', {})
            trend_score = 0
            if trends_data and trends_data.get('interest_over_time'):
                recent_trends = trends_data['interest_over_time'][-4:]
                trend_score = sum(recent_trends) / len(recent_trends)
            
            market_score = (rank_score * 0.6 + trend_score * 0.4) / 100
        
        # Calculate tech score
        tech_score = 0
        if tech_data := marketing_metrics.get('raw_data', {}).get('tech_stack'):
            total_tools = sum(len(tools) for tools in tech_data.values())
            tech_score = min(1.0, total_tools / 5)  # 5 tools = 100%
        
        # Calculate final score
        final_score = (
            github_score * weights['github'] +
            market_score * weights['market'] +
            tech_score * weights['tech']
        ) * 100
        
        return min(max(final_score, 0), 100)  # Ensure score is between 0 and 100
        
    except Exception as e:
        logger.error(f"Error calculating acquisition score: {str(e)}")
        return 0.0

@shared_task
def refresh_market_data(company_id: int):
    """Task to refresh just the marketing metrics"""
    try:
        db = SessionLocal()
        company = crud.get_company(db, company_id)
        
        if not company:
            logger.error(f"Company {company_id} not found")
            return
        
        marketing_estimator = MarketingEstimator()
        loop = asyncio.get_event_loop()
        marketing_metrics = loop.run_until_complete(
            marketing_estimator.collect_metrics(company.website)
        )
        
        if marketing_metrics:
            crud.update_market_metrics(db, company_id, marketing_metrics)
            
            if tech_data := marketing_metrics.get('raw_data', {}).get('tech_stack'):
                crud.update_tech_stack(db, company_id, tech_data)
                
        db.commit()
        
    except Exception as e:
        logger.error(f"Error refreshing market data for company {company_id}: {str(e)}")
        raise
    
    finally:
        db.close()