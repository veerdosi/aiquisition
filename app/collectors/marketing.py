import aiohttp
import logging
from typing import Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from fake_useragent import UserAgent
import asyncio
import json
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MarketingEstimator:
    def __init__(self):
        self.ua = UserAgent()
        self.pytrends = TrendReq()
        
    async def collect_metrics(self, domain: str) -> Dict[str, Any]:
        try:
            metrics = {
                'estimated_spend': 0.0,
                'channels': {},
                'efficiency_score': 0.0,
                'raw_data': {}
            }
            
            # Collect data from multiple free sources
            tranco_data = await self._collect_tranco(domain)
            trends_data = await self._collect_trends(domain)
            tech_data = await self._collect_tech_stack(domain)
            
            if tranco_data:
                metrics['raw_data']['tranco'] = tranco_data
                # Estimate traffic based on Tranco rank
                metrics['estimated_spend'] = self._estimate_spend_from_rank(tranco_data['rank'])
            
            if trends_data:
                metrics['raw_data']['trends'] = trends_data
                metrics['channels'].update(self._process_trends_data(trends_data))
            
            if tech_data:
                metrics['raw_data']['tech_stack'] = tech_data
                
            # Calculate efficiency score
            metrics['efficiency_score'] = await self._calculate_efficiency(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting marketing metrics: {str(e)}")
            return None

    async def _collect_tranco(self, domain: str) -> Dict[str, Any]:
        """Collect domain ranking from Tranco list API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://tranco-list.eu/api/ranks/domain/{domain}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'rank': data.get('rank'),
                            'last_updated': datetime.now().isoformat()
                        }
        except Exception as e:
            logger.error(f"Error collecting Tranco data for {domain}: {str(e)}")
            return None

    async def _collect_trends(self, domain: str) -> Dict[str, Any]:
        """Collect Google Trends data"""
        try:
            # Remove TLD for better trend matching
            company_name = domain.split('.')[0]
            self.pytrends.build_payload([company_name], timeframe='today 3-m')
            
            interest_data = self.pytrends.interest_over_time()
            related_queries = self.pytrends.related_queries()
            
            return {
                'interest_over_time': interest_data[company_name].tolist() if not interest_data.empty else [],
                'related_queries': {
                    'rising': related_queries[company_name]['rising'].to_dict('records') if related_queries[company_name]['rising'] is not None else [],
                    'top': related_queries[company_name]['top'].to_dict('records') if related_queries[company_name]['top'] is not None else []
                }
            }
        except Exception as e:
            logger.error(f"Error collecting Google Trends data for {domain}: {str(e)}")
            return None

    async def _collect_tech_stack(self, domain: str) -> Dict[str, Any]:
        """Collect technology stack information"""
        try:
            headers = {'User-Agent': self.ua.random}
            async with aiohttp.ClientSession() as session:
                url = f"https://{domain}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        tech_stack = {
                            'analytics': [],
                            'advertising': [],
                            'marketing_tools': []
                        }
                        
                        # Detect Analytics
                        if 'ga.js' in html or 'analytics.js' in html or 'gtag' in html:
                            tech_stack['analytics'].append('Google Analytics')
                        
                        # Detect Advertising
                        if 'googlesyndication' in html:
                            tech_stack['advertising'].append('Google AdSense')
                        if 'doubleclick' in html:
                            tech_stack['advertising'].append('Google Ads')
                            
                        # Detect Marketing Tools
                        if 'hubspot' in html:
                            tech_stack['marketing_tools'].append('HubSpot')
                        if 'marketo' in html:
                            tech_stack['marketing_tools'].append('Marketo')
                            
                        return tech_stack
        except Exception as e:
            logger.error(f"Error collecting tech stack for {domain}: {str(e)}")
            return None

    def _estimate_spend_from_rank(self, rank: int) -> float:
        """Estimate marketing spend based on Tranco rank"""
        if not rank:
            return 0.0
            
        # Rough estimation using power law distribution
        base_spend = 1000000  # Assumed monthly spend for rank 1
        decay_factor = 0.7
        
        estimated_spend = base_spend * (rank ** -decay_factor)
        return round(estimated_spend, 2)

    def _process_trends_data(self, trends_data: Dict) -> Dict[str, Any]:
        """Process Google Trends data into channel metrics"""
        channels = {
            'search': {'score': 0, 'trend': 0},
            'brand': {'score': 0, 'trend': 0}
        }
        
        if not trends_data:
            return channels
            
        # Calculate search interest
        interest_values = trends_data.get('interest_over_time', [])
        if interest_values:
            recent_interest = sum(interest_values[-4:]) / 4  # Last 4 weeks average
            channels['search']['score'] = recent_interest
            
            # Calculate trend (comparing with previous period)
            previous_interest = sum(interest_values[-8:-4]) / 4
            trend = ((recent_interest - previous_interest) / previous_interest * 100 
                    if previous_interest > 0 else 0)
            channels['search']['trend'] = round(trend, 2)
        
        # Calculate brand strength from related queries
        rising_queries = trends_data.get('related_queries', {}).get('rising', [])
        if rising_queries:
            brand_terms = sum(1 for q in rising_queries if 'brand' in q.get('query', '').lower())
            channels['brand']['score'] = (brand_terms / len(rising_queries)) * 100
            
        return channels

    async def _calculate_efficiency(self, metrics: Dict) -> float:
        """Calculate marketing efficiency score using available metrics"""
        try:
            efficiency_score = 0
            weights = {
                'rank_score': 0.4,
                'trend_score': 0.3,
                'tech_diversity': 0.3
            }
            
            # 1. Rank Score (inverse of rank percentile)
            rank = metrics.get('raw_data', {}).get('tranco', {}).get('rank')
            if rank:
                rank_score = max(0, 100 - (rank / 1000000 * 100))  # Assumes top 1M websites
            else:
                rank_score = 0
                
            # 2. Trend Score
            trends_data = metrics.get('raw_data', {}).get('trends', {})
            trend_score = 0
            if trends_data and trends_data.get('interest_over_time'):
                recent_trends = trends_data['interest_over_time'][-4:]
                trend_score = sum(recent_trends) / len(recent_trends)
                
            # 3. Tech Stack Diversity
            tech_data = metrics.get('raw_data', {}).get('tech_stack', {})
            total_tools = sum(len(tools) for tools in tech_data.values())
            tech_score = min(100, total_tools * 20)  # 5 tools = 100%
            
            # Calculate weighted final score
            efficiency_score = (
                rank_score * weights['rank_score'] +
                trend_score * weights['trend_score'] +
                tech_score * weights['tech_diversity']
            )
            
            return min(max(efficiency_score, 0), 100)
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {str(e)}")
            return 0.0