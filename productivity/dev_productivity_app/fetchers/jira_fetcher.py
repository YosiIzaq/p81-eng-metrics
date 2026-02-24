"""Jira fetcher for items completed and story points."""
import json
import subprocess
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import yaml

from .base_fetcher import BaseFetcher, TeamMember, Period, MetricData


def load_env_yaml() -> Dict[str, Any]:
    """Load credentials from .env.yaml file.
    
    Looks for .env.yaml in the app root directory.
    Returns empty dict if not found.
    """
    # Find the app root (where .env.yaml should be)
    app_root = Path(__file__).parent.parent
    env_file = app_root / ".env.yaml"
    
    if not env_file.exists():
        return {}
    
    try:
        with open(env_file, "r") as f:
            config = yaml.safe_load(f)
        
        # Check token expiration
        jira_config = config.get("jira", {})
        expires_at = jira_config.get("expires_at")
        
        if expires_at:
            try:
                expiry_date = datetime.strptime(str(expires_at), "%Y-%m-%d")
                if expiry_date < datetime.now():
                    print(f"  ⚠️  Warning: Jira token expired on {expires_at}")
                elif (expiry_date - datetime.now()).days < 7:
                    days_left = (expiry_date - datetime.now()).days
                    print(f"  ⚠️  Warning: Jira token expires in {days_left} days ({expires_at})")
            except ValueError:
                pass  # Ignore invalid date format
        
        return config
    except Exception as e:
        print(f"  Warning: Failed to load .env.yaml: {e}")
        return {}


class JiraFetcher(BaseFetcher):
    """Fetches Jira metrics: items completed and story points."""
    
    # Default field for story points (Jira custom field)
    STORY_POINTS_FIELD = "customfield_10016"
    
    def __init__(
        self,
        project: str,
        done_statuses: Optional[List[str]] = None,
        cloud_id: Optional[str] = None,
        test_mode: bool = False
    ):
        """Initialize JiraFetcher.
        
        Args:
            project: Jira project key (e.g., "P81")
            done_statuses: List of statuses considered as "done"
            cloud_id: Atlassian cloud ID or site URL
            test_mode: If True, return mock data instead of calling Jira API
        """
        self.project = project
        self.done_statuses = done_statuses or ["Done", "Ready for Release"]
        self.cloud_id = cloud_id
        self.test_mode = test_mode
    
    def fetch(self, member: TeamMember, period: Period) -> MetricData:
        """Fetch Jira metrics for a team member.
        
        Args:
            member: Team member to fetch data for
            period: Time period to fetch data for
            
        Returns:
            MetricData with items_completed and story_points populated
        """
        if self.test_mode:
            return self.fetch_test_data(member)
        
        try:
            jql = self.build_jql(member, period)
            response = self._execute_jql(jql)
            items, points = self.parse_response(response)
            
            return MetricData(
                items_completed=items,
                story_points=points
            )
        except Exception:
            return MetricData()
    
    def fetch_test_data(self, member: TeamMember) -> MetricData:
        """Return deterministic mock data for testing.
        
        Uses hash of Jira account ID to generate consistent values.
        
        Args:
            member: Team member to generate mock data for
            
        Returns:
            MetricData with deterministic test values
        """
        # Generate deterministic values based on account ID hash
        hash_val = int(hashlib.md5(member.jira_account_id.encode()).hexdigest(), 16)
        
        items = (hash_val % 40) + 10  # 10-49 items
        points = (hash_val % 30) + 5  # 5-34 story points
        
        return MetricData(
            items_completed=items,
            story_points=points
        )
    
    def build_jql(self, member: TeamMember, period: Period) -> str:
        """Build JQL query for fetching issues.
        
        Args:
            member: Team member to query for
            period: Time period to query
            
        Returns:
            JQL query string
        """
        start_date, end_date = period.to_jql_dates()
        
        # Format statuses for JQL
        statuses_str = ", ".join(f"'{s}'" for s in self.done_statuses)
        
        jql = (
            f"project = {self.project} "
            f"AND assignee = '{member.jira_account_id}' "
            f"AND status IN ({statuses_str}) "
            f"AND updated >= '{start_date}'"
        )
        
        return jql
    
    def parse_response(self, response: Dict[str, Any]) -> Tuple[int, int]:
        """Parse Jira API response to extract metrics.
        
        Args:
            response: Jira API response dictionary
            
        Returns:
            Tuple of (items_completed, story_points)
        """
        issues = response.get("issues", [])
        
        items = len(issues)
        story_points = 0
        
        for issue in issues:
            fields = issue.get("fields", {})
            sp = fields.get(self.STORY_POINTS_FIELD)
            if sp is not None:
                story_points += int(sp)
        
        return items, story_points
    
    def _execute_jql(self, jql: str) -> Dict[str, Any]:
        """Execute JQL query against Jira API.
        
        Loads credentials from .env.yaml or environment variables.
        Falls back to empty result on error.
        
        Priority:
        1. .env.yaml file (preferred)
        2. Environment variables (JIRA_API_TOKEN, JIRA_EMAIL)
        
        Args:
            jql: JQL query string
            
        Returns:
            Jira API response as dictionary
        """
        try:
            import urllib.parse
            
            # Try loading from .env.yaml first
            env_config = load_env_yaml()
            jira_config = env_config.get("jira", {})
            
            jira_token = jira_config.get("api_token") or os.environ.get("JIRA_API_TOKEN")
            jira_email = jira_config.get("email") or os.environ.get("JIRA_EMAIL")
            cloud_id = jira_config.get("cloud_id") or self.cloud_id
            
            if not jira_token or not jira_email:
                print(f"  Warning: No Jira credentials found - check .env.yaml or set JIRA_API_TOKEN/JIRA_EMAIL")
                return {"issues": []}
            
            if not jira_token.strip():
                print(f"  Warning: Jira API token is empty in .env.yaml")
                return {"issues": []}
            
            # Build curl command to Jira REST API
            encoded_jql = urllib.parse.quote(jql)
            url = f"https://{cloud_id}/rest/api/3/search?jql={encoded_jql}&maxResults=100&fields=summary,status,{self.STORY_POINTS_FIELD}"
            
            cmd = [
                "curl", "-s",
                "-u", f"{jira_email}:{jira_token}",
                "-H", "Accept: application/json",
                url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                response = json.loads(result.stdout)
                if "issues" in response:
                    return response
                # Check for auth errors
                if "errorMessages" in response:
                    print(f"  Warning: Jira API error: {response['errorMessages']}")
            
            return {"issues": []}
            
        except Exception as e:
            print(f"  Warning: Jira fetch failed: {e}")
            return {"issues": []}
