import requests
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketingEstimator:
    def __init__(self):
        self.api_keys = {
            'semrush': 'YOUR_SEMRUSH_API_KEY',
            'similarweb': 'YOUR_SIMILARWEB_API_KEY'
        }
        
    def collect_metrics(self, domain: str) -> Dict[str, Any]:
        try:
            metrics = {
                'estimated_spend': 0.0,
                'channels': {},
                'efficiency_score': 0.0,
                'raw_data': {}
            }
            
            # Collect data from multiple sources
            semrush_data = self._collect_semrush(domain)
            similarweb_data = self._collect_similarweb(domain)
            
            if semrush_data:
                metrics['raw_data']['semrush'] = semrush_data
                metrics['estimated_spend'] += semrush_data['estimated_spend']
                metrics['channels'].update(semrush_data['channels'])
            
            if similarweb_data:
                metrics['raw_data']['similarweb'] = similarweb_data
                metrics['estimated_spend'] = (metrics['estimated_spend'] + 
                                           similarweb_data['estimated_spend']) / 2
                
            # Calculate efficiency score
            metrics['efficiency_score'] = self._calculate_efficiency(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting marketing metrics: {str(e)}")
            return None
            
    def _collect_semrush(self, domain: str) -> Dict[str, Any]:
        """
        Collects marketing data from SEMrush API
        """
        try:
            # SEMrush API endpoint
            base_url = "https://api.semrush.com"
            
            # API parameters for domain analytics
            params = {
                'key': self.api_keys['semrush'],
                'type': 'domain_ranks',
                'domain': domain,
                'database': 'us',  # US database
                'export_columns': 'Dn,Rk,Or,Ot,Oc,Ad,At,Ac'
            }
            
            response = requests.get(f"{base_url}/analytics/ta/overview/{domain}", params=params)
            response.raise_for_status()
            
            # Get traffic data
            traffic_data = response.json()
            
            # Get keyword data
            keyword_params = {
                'key': self.api_keys['semrush'],
                'type': 'domain_organic',
                'domain': domain,
                'database': 'us',
                'display_limit': 100
            }
            
            keyword_response = requests.get(f"{base_url}/analytics/ta/keyword_organic/{domain}", 
                                        params=keyword_params)
            keyword_response.raise_for_status()
            keyword_data = keyword_response.json()
            
            # Calculate estimated spend based on traffic and CPC
            organic_traffic = traffic_data.get('data', {}).get('Or', 0)
            paid_traffic = traffic_data.get('data', {}).get('Ad', 0)
            avg_cpc = sum(kw.get('Cp', 0) for kw in keyword_data.get('data', [])) / len(keyword_data.get('data', [1]))
            
            estimated_monthly_spend = (paid_traffic * avg_cpc) + (organic_traffic * 0.1 * avg_cpc)  # Organic traffic valued at 10% of paid
            
            return {
                'estimated_spend': estimated_monthly_spend,
                'channels': {
                    'organic': {
                        'traffic': organic_traffic,
                        'keywords': len(keyword_data.get('data', [])),
                        'estimated_value': organic_traffic * 0.1 * avg_cpc
                    },
                    'paid': {
                        'traffic': paid_traffic,
                        'estimated_spend': paid_traffic * avg_cpc
                    }
                },
                'raw_data': {
                    'traffic_data': traffic_data,
                    'keyword_data': keyword_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting SEMrush data for {domain}: {str(e)}")
            return None

    def _collect_similarweb(self, domain: str) -> Dict[str, Any]:
        """
        Collects marketing data from SimilarWeb API
        """
        try:
            # SimilarWeb API endpoint
            base_url = "https://api.similarweb.com/v1"
            headers = {
                'Authorization': f"Bearer {self.api_keys['similarweb']}"
            }
            
            # Get total visits
            visits_response = requests.get(
                f"{base_url}/website/{domain}/total-traffic-and-engagement/visits",
                headers=headers
            )
            visits_response.raise_for_status()
            visits_data = visits_response.json()
            
            # Get traffic sources
            sources_response = requests.get(
                f"{base_url}/website/{domain}/traffic-sources/overview",
                headers=headers
            )
            sources_response.raise_for_status()
            sources_data = sources_response.json()
            
            # Get marketing channels
            channels_response = requests.get(
                f"{base_url}/website/{domain}/traffic-sources/marketing-channels",
                headers=headers
            )
            channels_response.raise_for_status()
            channels_data = channels_response.json()
            
            # Calculate estimated spend based on traffic sources and industry averages
            monthly_visits = visits_data.get('visits', [])[-1] if visits_data.get('visits') else 0
            
            # Industry average CPCs
            channel_cpcs = {
                'Display': 0.58,
                'Search': 2.69,
                'Social': 1.23,
                'Email': 0.45,
                'Direct': 0.0  # No direct cost
            }
            
            # Calculate spend per channel
            channel_spend = {}
            total_spend = 0
            
            for channel, data in channels_data.get('marketing_channels', {}).items():
                traffic_share = data.get('share', 0) / 100
                channel_traffic = monthly_visits * traffic_share
                cpc = channel_cpcs.get(channel, 1.0)
                channel_cost = channel_traffic * cpc
                
                channel_spend[channel] = {
                    'traffic': channel_traffic,
                    'share': traffic_share,
                    'estimated_spend': channel_cost
                }
                
                total_spend += channel_cost
            
            return {
                'estimated_spend': total_spend,
                'channels': channel_spend,
                'raw_data': {
                    'visits': visits_data,
                    'sources': sources_data,
                    'channels': channels_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting SimilarWeb data for {domain}: {str(e)}")
            return None

    def _calculate_efficiency(self, metrics: Dict) -> float:
        """
        Calculates marketing efficiency score based on collected metrics
        Score ranges from 0 to 100, higher is better
        """
        try:
            total_spend = metrics.get('estimated_spend', 0)
            if total_spend == 0:
                return 0
                
            efficiency_score = 0
            weights = {
                'traffic_cost': 0.3,
                'channel_diversity': 0.2,
                'organic_ratio': 0.3,
                'brand_presence': 0.2
            }
            
            # 1. Traffic Cost Efficiency (lower is better)
            semrush_data = metrics.get('raw_data', {}).get('semrush', {})
            total_traffic = (
                semrush_data.get('organic', {}).get('traffic', 0) +
                semrush_data.get('paid', {}).get('traffic', 0)
            )
            cost_per_visit = total_spend / total_traffic if total_traffic > 0 else float('inf')
            traffic_cost_score = min(100, (1 / (cost_per_visit + 0.1)) * 1000)  # Normalize to 0-100
            
            # 2. Channel Diversity (higher is better)
            channels = metrics.get('channels', {})
            active_channels = sum(1 for channel in channels.values() if channel.get('traffic', 0) > 0)
            channel_diversity_score = (active_channels / 5) * 100  # Assuming 5 main channels
            
            # 3. Organic vs Paid Ratio (higher organic is better)
            organic_traffic = semrush_data.get('organic', {}).get('traffic', 0)
            organic_ratio = organic_traffic / total_traffic if total_traffic > 0 else 0
            organic_score = organic_ratio * 100
            
            # 4. Brand Presence Score
            similarweb_data = metrics.get('raw_data', {}).get('similarweb', {})
            direct_traffic_share = (
                similarweb_data.get('channels', {})
                .get('Direct', {})
                .get('share', 0)
            )
            brand_presence_score = direct_traffic_share  # Direct traffic % as brand presence score
            
            # Calculate weighted final score
            efficiency_score = (
                traffic_cost_score * weights['traffic_cost'] +
                channel_diversity_score * weights['channel_diversity'] +
                organic_score * weights['organic_ratio'] +
                brand_presence_score * weights['brand_presence']
            )
            
            return min(max(efficiency_score, 0), 100)  # Ensure score is between 0 and 100
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {str(e)}")
            return 0.0