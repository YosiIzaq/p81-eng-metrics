"""Base fetcher abstract class and common data structures."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


@dataclass
class TeamMember:
    """Represents a team member with identifiers for different platforms."""
    name: str
    github_username: str
    jira_account_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TeamMember":
        """Create TeamMember from dictionary."""
        return cls(
            name=data["name"],
            github_username=data["github_username"],
            jira_account_id=data["jira_account_id"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TeamMember to dictionary."""
        return {
            "name": self.name,
            "github_username": self.github_username,
            "jira_account_id": self.jira_account_id
        }


@dataclass
class Period:
    """Represents a time period for data fetching."""
    name: str
    start_date: date
    end_date: date
    
    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]) -> "Period":
        """Create Period from configuration dictionary.
        
        Supports two formats:
        - Fixed: {"type": "fixed", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
        - Relative: {"type": "relative", "days_back": N}
        """
        period_type = config.get("type", "fixed")
        
        if period_type == "fixed":
            start_date = datetime.strptime(config["start"], "%Y-%m-%d").date()
            end_date = datetime.strptime(config["end"], "%Y-%m-%d").date()
        elif period_type == "relative":
            days_back = config["days_back"]
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
        else:
            raise ConfigError(f"Unknown period type: {period_type}")
        
        return cls(name=name, start_date=start_date, end_date=end_date)
    
    def to_jql_dates(self) -> Tuple[str, str]:
        """Convert to Jira JQL date format (YYYY-MM-DD)."""
        return (
            self.start_date.strftime("%Y-%m-%d"),
            self.end_date.strftime("%Y-%m-%d")
        )
    
    def to_github_date_range(self) -> str:
        """Convert to GitHub CLI date range format (start..end)."""
        return f"{self.start_date.strftime('%Y-%m-%d')}..{self.end_date.strftime('%Y-%m-%d')}"
    
    @property
    def duration_days(self) -> int:
        """Calculate duration in days."""
        return (self.end_date - self.start_date).days


@dataclass
class MetricData:
    """Container for productivity metrics."""
    items_completed: int = 0
    story_points: int = 0
    prs_authored: int = 0
    code_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MetricData to dictionary."""
        return {
            "items_completed": self.items_completed,
            "story_points": self.story_points,
            "prs_authored": self.prs_authored,
            "code_reviews": self.code_reviews
        }
    
    def merge(self, other: "MetricData") -> "MetricData":
        """Merge with another MetricData, taking non-zero values from other."""
        return MetricData(
            items_completed=self.items_completed if self.items_completed else other.items_completed,
            story_points=self.story_points if self.story_points else other.story_points,
            prs_authored=self.prs_authored if self.prs_authored else other.prs_authored,
            code_reviews=self.code_reviews if self.code_reviews else other.code_reviews
        )


class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""
    
    @abstractmethod
    def fetch(self, member: TeamMember, period: Period) -> MetricData:
        """Fetch metrics for a team member over a period.
        
        Args:
            member: The team member to fetch data for
            period: The time period to fetch data for
            
        Returns:
            MetricData containing the fetched metrics
        """
        pass
    
    @abstractmethod
    def fetch_test_data(self, member: TeamMember) -> MetricData:
        """Return deterministic mock data for testing.
        
        Args:
            member: The team member to generate mock data for
            
        Returns:
            MetricData with deterministic test values
        """
        pass


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If file not found or invalid JSON
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}")


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration against required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigError: If required fields are missing or invalid
    """
    required_fields = ["version", "team", "weights"]
    
    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Missing required field: {field}")
    
    # Validate team structure
    if "name" not in config.get("team", {}):
        raise ConfigError("Team must have a 'name' field")
    
    if "members" not in config.get("team", {}):
        raise ConfigError("Team must have a 'members' field")
    
    # Validate weights
    weights = config.get("weights", {})
    required_weights = ["items_completed", "prs_authored", "code_reviews"]
    
    for weight_name in required_weights:
        if weight_name not in weights:
            raise ConfigError(f"Missing required weight: {weight_name}")
    
    # Note: We don't error on non-summing weights, just normalize at calculation time
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.01:
        # Log warning but don't raise - weights will be normalized
        pass


def load_team_config(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load team configuration from team_config.json.
    
    Searches for team_config.json in the following order:
    1. base_dir (if provided)
    2. Repository root (Jira/statistics/)
    3. Current directory
    
    Args:
        base_dir: Optional base directory to search from
        
    Returns:
        Team configuration dictionary
        
    Raises:
        ConfigError: If team_config.json not found
    """
    search_paths = []
    
    if base_dir:
        search_paths.append(base_dir / "team_config.json")
    
    # Look for repo root (go up from productivity/dev_productivity_app/)
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent.parent.parent  # fetchers -> dev_productivity_app -> productivity -> statistics
    search_paths.append(repo_root / "team_config.json")
    
    # Current directory
    search_paths.append(Path.cwd() / "team_config.json")
    
    for config_path in search_paths:
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Invalid JSON in team_config.json: {e}")
    
    raise ConfigError(
        "team_config.json not found.\n"
        "To set up:\n"
        "  1. Copy team_config.example.json to team_config.json\n"
        "  2. Fill in your team's information\n"
        f"Searched: {[str(p) for p in search_paths]}"
    )


def load_team_members(config: Dict[str, Any], team_config_dir: Optional[Path] = None) -> List[TeamMember]:
    """Load team members from configuration, merging with team_config.json.
    
    Args:
        config: Configuration dictionary containing team data
        team_config_dir: Optional directory containing team_config.json
        
    Returns:
        List of TeamMember objects
    """
    # First, try to load from team_config.json (preferred)
    try:
        team_config = load_team_config(team_config_dir)
        members_data = team_config.get("members", [])
        if members_data:
            # Convert team_config format to our format
            members = []
            for m in members_data:
                # team_config uses display_name, we need name
                member_dict = {
                    "name": m.get("display_name", m.get("github_username", "")),
                    "github_username": m.get("github_username", ""),
                    "jira_account_id": m.get("jira_account_id", "")
                }
                members.append(TeamMember.from_dict(member_dict))
            return members
    except ConfigError:
        # Fall back to embedded config
        pass
    
    # Fall back to default_config.json members (may be empty)
    members_data = config.get("team", {}).get("members", [])
    return [TeamMember.from_dict(m) for m in members_data]
