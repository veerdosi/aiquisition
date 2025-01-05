from github import Github
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GitHubCollector:
    def __init__(self, token):
        self.github = Github(token)
        
    def collect_metrics(self, repo_url):
        try:
            # Extract repo name from URL
            repo_name = repo_url.split('github.com/')[-1]
            repo = self.github.get_repo(repo_name)
            
            # Collect basic metrics
            metrics = {
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'contributors': repo.get_contributors().totalCount,
                'commit_frequency': self._calculate_commit_frequency(repo),
                'issue_response_time': self._calculate_response_time(repo),
                'raw_data': {
                    'description': repo.description,
                    'language': repo.language,
                    'topics': repo.get_topics(),
                    'open_issues': repo.open_issues_count,
                    'watchers': repo.subscribers_count,
                    'last_update': repo.updated_at.isoformat()
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting GitHub metrics: {str(e)}")
            return None
            
    def _calculate_commit_frequency(self, repo):
        try:
            since = datetime.now() - timedelta(days=30)
            commits = repo.get_commits(since=since)
            return commits.totalCount / 30  # Average daily commits
        except Exception as e:
            logger.error(f"Error calculating commit frequency: {str(e)}")
            return 0
            
    def _calculate_response_time(self, repo):
        try:
            issues = repo.get_issues(state='closed', sort='updated')
            response_times = []
            
            for issue in issues[:100]:  # Sample last 100 issues
                if issue.comments > 0:
                    first_comment = issue.get_comments()[0]
                    response_time = (first_comment.created_at - issue.created_at).total_seconds() / 3600
                    response_times.append(response_time)
            
            return sum(response_times) / len(response_times) if response_times else 0
            
        except Exception as e:
            logger.error(f"Error calculating response time: {str(e)}")
            return 0