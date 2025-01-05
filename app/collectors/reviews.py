import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any
import json
from textblob import TextBlob
import re
from urllib.parse import quote_plus
import random
logger = logging.getLogger(__name__)

class ReviewCollector:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def collect_metrics(self, company_name: str) -> Dict[str, Any]:
        try:
            metrics = {
                'nps_score': 0.0,
                'review_count': 0,
                'average_rating': 0.0,
                'sentiment_score': 0.0,
                'raw_data': {}
            }
            
            # Collect from multiple sources
            g2_data = self._collect_g2(company_name)
            capterra_data = self._collect_capterra(company_name)
            
            if g2_data:
                metrics['raw_data']['g2'] = g2_data
                metrics['review_count'] += g2_data['review_count']
                metrics['average_rating'] = (
                    (metrics['average_rating'] * metrics['review_count'] + 
                     g2_data['rating'] * g2_data['review_count']) /
                    (metrics['review_count'] + g2_data['review_count'])
                )
            
            if capterra_data:
                metrics['raw_data']['capterra'] = capterra_data
                metrics['review_count'] += capterra_data['review_count']
                metrics['average_rating'] = (
                    (metrics['average_rating'] * metrics['review_count'] + 
                     capterra_data['rating'] * capterra_data['review_count']) /
                    (metrics['review_count'] + capterra_data['review_count'])
                )
            
            # Calculate NPS from raw review data
            metrics['nps_score'] = self._calculate_nps(metrics['raw_data'])
            metrics['sentiment_score'] = self._calculate_sentiment(metrics['raw_data'])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting review metrics: {str(e)}")
            return None
            
    def _collect_g2(self, company_name: str) -> Dict[str, Any]:
        """
        Collects review data from G2
        """
        try:
            # Construct G2 URL
            encoded_name = quote_plus(company_name.lower())
            url = f"https://www.g2.com/products/{encoded_name}/reviews"
            
            # Make request with rotating user agents
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.g2.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract review data
            reviews = []
            review_elements = soup.find_all('div', class_='review')
            
            for review in review_elements[:100]:  # Limit to first 100 reviews
                try:
                    rating_elem = review.find('meta', itemprop='ratingValue')
                    rating = float(rating_elem['content']) if rating_elem else None
                    
                    text_elem = review.find('div', class_='review-content')
                    text = text_elem.get_text(strip=True) if text_elem else ""
                    
                    date_elem = review.find('meta', itemprop='datePublished')
                    date = date_elem['content'] if date_elem else None
                    
                    if rating and text:
                        reviews.append({
                            'rating': rating,
                            'text': text,
                            'date': date
                        })
                except Exception as e:
                    logger.error(f"Error parsing G2 review: {str(e)}")
                    continue
            
            # Calculate metrics
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
            
            return {
                'rating': avg_rating,
                'review_count': len(reviews),
                'reviews': reviews,
                'source': 'g2'
            }
            
        except Exception as e:
            logger.error(f"Error collecting G2 data for {company_name}: {str(e)}")
            return None

    def _collect_capterra(self, company_name: str) -> Dict[str, Any]:
        """
        Collects review data from Capterra
        """
        try:
            # Construct Capterra URL
            encoded_name = quote_plus(company_name.lower())
            url = f"https://www.capterra.com/p/{encoded_name}/reviews"
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.capterra.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract review data
            reviews = []
            review_elements = soup.find_all('div', class_='review-wrapper')
            
            for review in review_elements[:100]:  # Limit to first 100 reviews
                try:
                    rating_elem = review.find('meta', itemprop='ratingValue')
                    rating = float(rating_elem['content']) if rating_elem else None
                    
                    text_elem = review.find('div', class_='review-text')
                    text = text_elem.get_text(strip=True) if text_elem else ""
                    
                    pros_elem = review.find('div', class_='pros-text')
                    pros = pros_elem.get_text(strip=True) if pros_elem else ""
                    
                    cons_elem = review.find('div', class_='cons-text')
                    cons = cons_elem.get_text(strip=True) if cons_elem else ""
                    
                    if rating:
                        reviews.append({
                            'rating': rating,
                            'text': text,
                            'pros': pros,
                            'cons': cons
                        })
                except Exception as e:
                    logger.error(f"Error parsing Capterra review: {str(e)}")
                    continue
            
            # Calculate metrics
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
            
            return {
                'rating': avg_rating,
                'review_count': len(reviews),
                'reviews': reviews,
                'source': 'capterra'
            }
            
        except Exception as e:
            logger.error(f"Error collecting Capterra data for {company_name}: {str(e)}")
            return None

    def _calculate_nps(self, raw_data: Dict) -> float:
        """
        Calculates NPS score from review data
        NPS = % Promoters - % Detractors
        Promoters: 9-10
        Passives: 7-8
        Detractors: 0-6
        """
        try:
            all_reviews = []
            
            # Combine reviews from all sources
            for source, data in raw_data.items():
                if data and 'reviews' in data:
                    all_reviews.extend(data['reviews'])
            
            if not all_reviews:
                return 0.0
            
            # Count promoters, passives, and detractors
            promoters = sum(1 for r in all_reviews if r['rating'] >= 9)
            detractors = sum(1 for r in all_reviews if r['rating'] <= 6)
            total_responses = len(all_reviews)
            
            if total_responses == 0:
                return 0.0
            
            # Calculate NPS
            promoter_percentage = (promoters / total_responses) * 100
            detractor_percentage = (detractors / total_responses) * 100
            
            nps = promoter_percentage - detractor_percentage
            
            # NPS ranges from -100 to 100
            return max(min(nps, 100), -100)
            
        except Exception as e:
            logger.error(f"Error calculating NPS: {str(e)}")
            return 0.0

    def _calculate_sentiment(self, raw_data: Dict) -> float:
        """
        Calculates sentiment score from review text using TextBlob
        Returns score from 0 to 100 where:
        0-40: Negative
        40-60: Neutral
        60-100: Positive
        """
        try:
            all_reviews = []
            
            # Combine reviews from all sources
            for source, data in raw_data.items():
                if data and 'reviews' in data:
                    all_reviews.extend(data['reviews'])
            
            if not all_reviews:
                return 50.0  # Neutral score if no reviews
            
            # Calculate sentiment for each review
            sentiments = []
            for review in all_reviews:
                # Combine all text fields
                text = review.get('text', '')
                if 'pros' in review:
                    text += ' ' + review['pros']
                if 'cons' in review:
                    text += ' ' + review['cons']
                    
                if text.strip():
                    # Use TextBlob for sentiment analysis
                    blob = TextBlob(text)
                    # Polarity ranges from -1 to 1
                    sentiments.append(blob.sentiment.polarity)
            
            if not sentiments:
                return 50.0
            
            # Calculate average sentiment and convert to 0-100 scale
            avg_sentiment = sum(sentiments) / len(sentiments)
            scaled_sentiment = (avg_sentiment + 1) * 50  # Convert -1,1 to 0,100
            
            return scaled_sentiment
            
        except Exception as e:
            logger.error(f"Error calculating sentiment: {str(e)}")
            return 50.0

    def _get_random_user_agent(self) -> str:
        """
        Returns a random user agent string
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        return random.choice(user_agents)
