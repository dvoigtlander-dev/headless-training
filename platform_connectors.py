"""
Platform data connectors for Headless Training Dashboard
Integrates: PlusPlus (Learn++), Pluralsight, Trailhead, O'Reilly
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import lru_cache
import os

# ============================================================================
# PLUSPLUS / LEARN++ CONNECTOR
# ============================================================================

class PlusPlusConnector:
    """
    Connect to sfdc-bt.plusplus.app
    Docs: https://learn.plusplus.app/docs/api
    """

    def __init__(self, api_key: Optional[str] = None, api_url: str = "https://sfdc-bt.plusplus.app"):
        self.api_key = api_key or os.getenv("PLUSPLUS_API_KEY")
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        } if self.api_key else {}

    def get_courses(self) -> List[Dict]:
        """Fetch all courses/events from PlusPlus"""
        try:
            resp = requests.get(
                f"{self.api_url}/api/v2/courses",
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", [])
        except Exception as e:
            print(f"PlusPlus courses error: {e}")
            return []

    def get_assignments(self) -> List[Dict]:
        """Fetch learner assignments (completion tracking)"""
        try:
            resp = requests.get(
                f"{self.api_url}/api/v2/assignments",
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", [])
        except Exception as e:
            print(f"PlusPlus assignments error: {e}")
            return []

    def get_enrollments(self) -> List[Dict]:
        """Fetch learner event enrollments"""
        try:
            resp = requests.get(
                f"{self.api_url}/api/v2/enrollments",
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", [])
        except Exception as e:
            print(f"PlusPlus enrollments error: {e}")
            return []

    def get_adoption_metrics(self) -> Dict:
        """Fetch org-wide adoption/engagement metrics"""
        try:
            resp = requests.get(
                f"{self.api_url}/api/v2/metrics/adoption",
                headers=self.headers,
                params={"range": "all"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except Exception as e:
            print(f"PlusPlus metrics error: {e}")
            return {}

    def get_user_progress(self, email: str) -> Dict:
        """Get individual user progress by email"""
        try:
            resp = requests.get(
                f"{self.api_url}/api/v2/users/{email}/progress",
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except Exception as e:
            print(f"PlusPlus user progress error: {e}")
            return {}


# ============================================================================
# PLURALSIGHT CONNECTOR
# ============================================================================

class PluralsightConnector:
    """
    Connect to Pluralsight via GraphQL API
    Note: Single-user progress (API key holder only) unless enterprise reporting enabled
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PLURALSIGHT_API_KEY")
        self.graphql_url = "https://api.pluralsight.com/graphql"

    def search_courses(self, query: str, limit: int = 20) -> List[Dict]:
        """Search Pluralsight catalog"""
        payload = {
            "query": """
            query SearchCourses($query: String!, $limit: Int) {
                courseSearch(query: $query, limit: $limit) {
                    courses {
                        id
                        title
                        description
                        level
                        duration
                        averageRating
                        url
                        imageUrl
                        authors { displayName }
                        releaseDate
                    }
                }
            }
            """,
            "variables": {"query": query, "limit": limit}
        }

        try:
            resp = requests.post(
                self.graphql_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("courseSearch", {}).get("courses", [])
        except Exception as e:
            print(f"Pluralsight search error: {e}")
            return []

    def get_user_progress(self) -> Dict:
        """Get logged-in user's course progress (single user)"""
        payload = {
            "query": """
            query GetMyProgress {
                me {
                    courseProgress {
                        course { id title }
                        percentComplete
                        isCompleted
                        completedOn
                        totalWatchedSeconds
                    }
                }
            }
            """
        }

        try:
            resp = requests.post(
                self.graphql_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("me", {})
        except Exception as e:
            print(f"Pluralsight progress error: {e}")
            return {}

    @staticmethod
    def load_cached_courses() -> List[Dict]:
        """Load locally cached Pluralsight courses"""
        try:
            with open("~/.claude/skills/pluralsight/courses.json") as f:
                return json.load(f)
        except:
            return []


# ============================================================================
# TRAILHEAD CONNECTOR
# ============================================================================

class TrailheadConnector:
    """
    Connect to Trailhead via MCP server
    Note: Catalog-only (no learner progress endpoint)
    """

    def __init__(self):
        self.base_url = "https://trailhead.salesforce.com"
        # Would use MCP server mcp__trailhead__content_search and fetch_content
        # This is a reference implementation

    def search_content(self, query: str, content_type: str = None) -> List[Dict]:
        """
        Search Trailhead content.
        Content types: MODULE, PROJECT, TRAIL, TRAILMIX, SUPERBADGE
        """
        # Implementation would use MCP search_oreilly_content tool
        pass

    def get_content(self, api_name: str) -> Dict:
        """Fetch full content details including markdown body"""
        # Implementation would use MCP fetch_content tool
        pass

    @staticmethod
    def sample_trails() -> List[Dict]:
        """Return sample Trailhead content for demo"""
        return [
            {
                "id": "sfdc_fundamentals",
                "type": "TRAIL",
                "title": "Salesforce Fundamentals",
                "description": "Master the core concepts of Salesforce CRM",
                "pointTotal": 2500,
                "minuteTotal": 480,
                "url": "https://trailhead.salesforce.com/trails/force_com_admin_beginner",
                "level": "Foundational"
            },
            {
                "id": "platform_dev",
                "type": "TRAIL",
                "title": "Salesforce Platform Development",
                "description": "Build custom applications on the Salesforce platform",
                "pointTotal": 3200,
                "minuteTotal": 600,
                "url": "https://trailhead.salesforce.com/trails/platform_dev_beginner",
                "level": "Intermediate"
            }
        ]


# ============================================================================
# OREILLY CONNECTOR
# ============================================================================

class OReilly Connector:
    """
    Connect to O'Reilly via MCP server
    Note: Catalog-only (no learner progress)
    """

    def search_content(self, query: str, content_type: str = None) -> List[Dict]:
        """
        Search O'Reilly catalog.
        Content types: book, video, course, learning-path, certification, interactive-tutorial
        """
        # Implementation would use MCP search_oreilly_content tool
        pass

    @staticmethod
    def sample_content() -> List[Dict]:
        """Return sample O'Reilly content for demo"""
        return [
            {
                "title": "Python for Data Analysis",
                "authors": ["Wes McKinney"],
                "type": "book",
                "url": "https://www.oreilly.com/library/view/python-for-data-analysis/...",
                "publication_date": "2022-10-01",
                "tags": ["Python", "Data Science", "Pandas"]
            },
            {
                "title": "Kubernetes: Up and Running",
                "authors": ["Kelsey Hightower", "Brendan Burns", "Joe Beda"],
                "type": "book",
                "url": "https://www.oreilly.com/library/view/kubernetes-up-and-running/...",
                "publication_date": "2021-09-01",
                "tags": ["Kubernetes", "DevOps", "Cloud"]
            }
        ]


# ============================================================================
# UNIFIED DATA AGGREGATOR
# ============================================================================

class TrainingDataAggregator:
    """
    Aggregate course and learner data across all platforms
    """

    def __init__(self):
        self.plusplus = PlusPlusConnector()
        self.pluralsight = PluralsightConnector()
        self.trailhead = TrailheadConnector()
        self.oreilly = OReilly Connector()

    def get_all_courses(self) -> Dict[str, List[Dict]]:
        """Fetch courses from all platforms"""
        return {
            "plusplus": self.plusplus.get_courses(),
            "pluralsight": PluralsightConnector.load_cached_courses(),
            "trailhead": TrailheadConnector.sample_trails(),
            "oreilly": OReilly Connector.sample_content()
        }

    def get_learner_summary(self) -> Dict:
        """Get org-wide learner engagement and completion data"""
        return {
            "plusplus": {
                "metrics": self.plusplus.get_adoption_metrics(),
                "assignments": self.plusplus.get_assignments(),
                "enrollments": self.plusplus.get_enrollments()
            },
            "pluralsight": {
                "user_progress": self.pluralsight.get_user_progress()
            }
        }

    def normalize_course_data(self) -> List[Dict]:
        """
        Normalize course data from all platforms into common schema.
        Schema: id, title, platform, type, duration, cost, rating, mandatory, expiration
        """
        all_courses = self.get_all_courses()
        normalized = []

        for platform, courses in all_courses.items():
            for course in courses:
                normalized.append({
                    "id": f"{platform}_{course.get('id', course.get('title', '').lower().replace(' ', '_'))}",
                    "title": course.get("title"),
                    "platform": platform,
                    "type": course.get("type"),
                    "duration_minutes": course.get("duration", course.get("minuteTotal", 0)),
                    "cost": 0,  # Populated from cost_mapping.json
                    "rating": course.get("averageRating"),
                    "url": course.get("url"),
                    "mandatory": False,  # Determined from PlusPlus due_date + is_self_assignable
                    "expiration_date": None  # Manual tracking needed
                })

        return normalized


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    agg = TrainingDataAggregator()

    # Get all courses
    print("=== Courses by Platform ===")
    courses = agg.get_all_courses()
    for platform, course_list in courses.items():
        print(f"\n{platform.upper()}: {len(course_list)} courses")
        for course in course_list[:2]:
            print(f"  - {course.get('title')}")

    # Get learner data
    print("\n=== Learner Engagement ===")
    learners = agg.get_learner_summary()
    print(json.dumps(learners, indent=2, default=str))
