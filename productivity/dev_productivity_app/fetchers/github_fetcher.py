"""GitHub fetcher for PRs authored and code reviews performed."""
import json
import subprocess
import time
import hashlib
from typing import Optional

from .base_fetcher import BaseFetcher, TeamMember, Period, MetricData


class GitHubFetcher(BaseFetcher):
    """Fetches GitHub metrics: PRs authored and code reviews performed."""
    
    def __init__(
        self,
        org: Optional[str] = None,
        test_mode: bool = False,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize GitHubFetcher.
        
        Args:
            org: GitHub organization to filter by (optional)
            test_mode: If True, return mock data instead of calling GitHub API
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        self.org = org
        self.test_mode = test_mode
        self.retry_count = retry_count
        self.retry_delay = retry_delay
    
    def fetch(self, member: TeamMember, period: Period) -> MetricData:
        """Fetch GitHub metrics for a team member.
        
        Args:
            member: Team member to fetch data for
            period: Time period to fetch data for
            
        Returns:
            MetricData with prs_authored and code_reviews populated
        """
        if self.test_mode:
            return self.fetch_test_data(member)
        
        prs_authored = self.fetch_prs_authored(member, period)
        code_reviews = self.fetch_code_reviews(member, period)
        
        return MetricData(
            prs_authored=prs_authored,
            code_reviews=code_reviews
        )
    
    def fetch_test_data(self, member: TeamMember) -> MetricData:
        """Return deterministic mock data for testing.
        
        Uses hash of username to generate consistent values.
        
        Args:
            member: Team member to generate mock data for
            
        Returns:
            MetricData with deterministic test values
        """
        # Generate deterministic values based on username hash
        hash_val = int(hashlib.md5(member.github_username.encode()).hexdigest(), 16)
        
        prs = (hash_val % 30) + 5  # 5-34 PRs
        reviews = (hash_val % 50) + 10  # 10-59 reviews
        
        return MetricData(
            prs_authored=prs,
            code_reviews=reviews
        )
    
    def fetch_prs_authored(self, member: TeamMember, period: Period) -> int:
        """Fetch count of PRs authored by a team member.
        
        Args:
            member: Team member to fetch PRs for
            period: Time period to search
            
        Returns:
            Number of PRs authored
        """
        date_range = period.to_github_date_range()
        
        cmd = [
            "gh", "search", "prs",
            f"--author={member.github_username}",
            "--merged",
            f"--created={date_range}",
            "--limit=100",
            "--json=number"
        ]
        
        return self._run_gh_command_with_retry(cmd)
    
    def fetch_code_reviews(self, member: TeamMember, period: Period) -> int:
        """Fetch count of code reviews performed by a team member.
        
        Args:
            member: Team member to fetch reviews for
            period: Time period to search
            
        Returns:
            Number of code reviews performed
        """
        date_range = period.to_github_date_range()
        
        cmd = [
            "gh", "search", "prs",
            f"--reviewed-by={member.github_username}",
            f"--created={date_range}",
            "--limit=500",
            "--json=number"
        ]
        
        return self._run_gh_command_with_retry(cmd)
    
    def _run_gh_command_with_retry(self, cmd: list) -> int:
        """Run a gh command with retry logic.
        
        Args:
            cmd: Command to run
            
        Returns:
            Count of results
        """
        attempts = 0
        
        while attempts < self.retry_count:
            attempts += 1
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        return len(data)
                    except json.JSONDecodeError:
                        return 0
                else:
                    # Check if rate limited
                    if "rate limit" in result.stderr.lower():
                        if attempts < self.retry_count:
                            time.sleep(self.retry_delay)
                            continue
                    return 0
                    
            except subprocess.TimeoutExpired:
                if attempts < self.retry_count:
                    time.sleep(self.retry_delay)
                    continue
                return 0
            except Exception:
                return 0
        
        return 0
